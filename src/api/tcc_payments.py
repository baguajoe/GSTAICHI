"""
PayPal subscriptions: subscribe, confirm, change plan, cancel, and the PayPal webhook.

Access is only ever granted from what PayPal itself reports for the subscription (never from the browser):
every path ends in sync_subscription(), which reads the subscription from PayPal and updates the member.
"""
import os
from datetime import datetime
from flask import jsonify, request
from sqlalchemy.exc import IntegrityError
from .models import db, User, Plan, Tier, SiteSettings, WebhookEvent
from .extensions import limiter
from . import paypal
from .paypal import PayPalError
from .notify import notify_school
from .member_emails import plan_status_emails
from .tcc_auth import role_required, get_current_user
from .taichi_company import tcc

STATUS_MAP = {
    "ACTIVE": "active",
    "SUSPENDED": "past_due",
    "CANCELLED": "cancelled",
    "EXPIRED": "expired",
}

SUBSCRIPTION_EVENTS = {
    "BILLING.SUBSCRIPTION.ACTIVATED", "BILLING.SUBSCRIPTION.UPDATED", "BILLING.SUBSCRIPTION.CANCELLED",
    "BILLING.SUBSCRIPTION.SUSPENDED", "BILLING.SUBSCRIPTION.EXPIRED", "BILLING.SUBSCRIPTION.RE-ACTIVATED",
    "BILLING.SUBSCRIPTION.PAYMENT.FAILED",
}


def _parse_time(value):
    if not value:
        return None
    try:
        return datetime.strptime(value.replace("Z", "")[:19], "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return None


def founding_offer_open(now=None):
    end = SiteSettings.get().founding_member_end_date
    return end is None or (now or datetime.utcnow()) < end


def plan_options_for(user):
    """Plans this member may choose. Founding members keep founding prices for life, on any tier."""
    options = []
    for tier in Tier.query.order_by(Tier.sort_order, Tier.rank).all():
        for interval in ("month", "year"):
            plan = None
            if user is not None and user.is_founding_member:
                plan = Plan.query.filter_by(tier_id=tier.id, interval=interval, is_founding=True) \
                    .order_by(Plan.price).first()
            if plan is None:
                plan = Plan.query.filter_by(tier_id=tier.id, interval=interval, is_active=True) \
                    .order_by(Plan.created_at.desc()).first()
            if plan is not None:
                options.append(plan)
    return options


def sync_subscription(user, sub):
    """Updates the member from PayPal's subscription record. Returns the new status."""
    plan = Plan.by_paypal_id(sub.get("plan_id"))
    status = STATUS_MAP.get(sub.get("status"))
    if plan is None or status is None:
        return None  # not ours, or still waiting for the member's approval
    billing = sub.get("billing_info") or {}
    next_billing = _parse_time(billing.get("next_billing_time"))

    before = user.subscription_status
    user.paypal_subscription_id = sub["id"]
    user.current_plan_id = plan.id
    user.tier_rank = plan.tier.rank
    user.subscription_status = status
    if status == "active" and before != "active":
        user.subscribed_at, user.cancelled_at = datetime.utcnow(), None
    if status == "cancelled" and before != "cancelled":
        user.cancelled_at = datetime.utcnow()
    if status == "active":
        user.next_billing_at = next_billing
        if next_billing:
            user.paid_through = next_billing
    else:
        user.next_billing_at = None
        # cancelled: access continues until the end of the period already paid for (paid_through stays)
    if status == "active" and plan.is_founding and founding_offer_open(_parse_time(sub.get("start_time"))):
        user.is_founding_member = True
    return status


def _tier_name(rank):
    tier = Tier.query.filter_by(rank=rank).first()
    return tier.name if tier else f"Level {rank}"


def _subscription_summary(user):
    plan = user.current_plan
    return {
        "status": user.subscription_status,
        "has_access": user.has_active_access,
        "plan": plan.serialize() if plan else None,
        "tier_rank": user.tier_rank,
        "next_billing_at": user.next_billing_at.isoformat() if user.next_billing_at else None,
        "paid_through": user.paid_through.isoformat() if user.paid_through else None,
        "is_founding_member": user.is_founding_member,
        "managed_by_paypal": bool(user.paypal_subscription_id),
        "granted": ({"tier_name": _tier_name(user.granted_rank),
                     "until": user.granted_until.isoformat() if user.granted_until else None}
                    if user.granted_rank else None),
        "options": [p.serialize() for p in plan_options_for(user)],
        "paypal_ready": paypal.is_configured(),
    }


@tcc.route('/subscription', methods=['GET'])
@role_required()
def get_subscription():
    return jsonify(_subscription_summary(get_current_user()))


@tcc.route('/plan-options', methods=['GET'])
def get_plan_options():
    """Plans offered to this visitor (founding members see their founding prices)."""
    try:
        user = get_current_user(optional=True)
    except Exception:
        user = None
    return jsonify([p.serialize() for p in plan_options_for(user)])


def _log(where, user, subscription_id, message):
    """One searchable line in the server log (Render > Logs): search for "[paypal]" or the subscription ID."""
    print(f"[paypal] {where} user={getattr(user, 'id', None)} sub={subscription_id}: {message}", flush=True)


def _owner_ok(user, sub):
    """The site sends the member's user id to PayPal as custom_id. Empty means it was made outside the site."""
    custom_id = str(sub.get("custom_id") or "").strip()
    return custom_id in ("", str(user.id))


def remember_subscription(user, subscription_id):
    """Stores an approved subscription ID on the member as soon as we know it, even before PayPal has
    activated it, so the webhook, the next login and /subscription/sync can all finish the job later.
    An ID that is still billing is never replaced (the member would lose track of it)."""
    if user.paypal_subscription_id == subscription_id:
        return
    if user.paypal_subscription_id and user.subscription_status in ("active", "past_due"):
        _log("remember", user, subscription_id,
             f"not stored yet: member still has billing subscription {user.paypal_subscription_id}")
        return
    user.paypal_subscription_id = subscription_id
    db.session.commit()


def activate_subscription(user, sub, cancel_replaced=True):
    """Applies a PayPal subscription record to the member, commits, and sends the emails and school notice.
    Returns the new status, or None when the subscription is not for one of our plans (nothing is changed)."""
    subscription_id = sub["id"]
    old_subscription = user.paypal_subscription_id if user.paypal_subscription_id not in (None, subscription_id) else None
    was_paying = user.has_active_access and user.tier_rank > 0
    before_status, before_rank = (user.subscription_status if not old_subscription else "none"), user.tier_rank
    status = sync_subscription(user, sub)
    if status is None:
        db.session.rollback()
        return None
    db.session.commit()
    plan_status_emails(user, before_status, before_rank)

    if old_subscription and cancel_replaced:
        # Subscribed again while an older subscription existed: stop the old one so nobody pays twice
        try:
            paypal.cancel_subscription(old_subscription, "Replaced by a new subscription")
        except PayPalError as e:
            _log("cancel-old", user, old_subscription, f"could not cancel the replaced subscription: {e}")
    if status == "active" and not was_paying and user.current_plan:
        notify_school("New subscriber", f"{user.name or ''} <{user.email}> subscribed to "
                      f"{user.current_plan.tier.name} ({user.current_plan.interval}ly, ${user.current_plan.price})."
                      f"{' Founding member.' if user.is_founding_member else ''}")
    return status


def restore_on_login(user):
    """At sign-in: a member with a PayPal subscription ID but no active paid level gets it back if PayPal says
    the subscription is ACTIVE. Never raises and never blocks sign-in for long."""
    subscription_id = user.paypal_subscription_id
    if not subscription_id or user.is_staff or (user.tier_rank > 0 and user.subscription_status == "active"):
        return
    try:
        sub = paypal.get_subscription(subscription_id, timeout=8)
        if sub.get("status") != "ACTIVE":
            return
        if not _owner_ok(user, sub):
            _log("login-restore", user, subscription_id, f"skipped: PayPal custom_id is {sub.get('custom_id')!r}")
            return
        status = activate_subscription(user, sub, cancel_replaced=False)
        _log("login-restore", user, subscription_id,
             f"restored level {user.tier_rank}" if status else f"plan {sub.get('plan_id')} is not one of our plans")
    except Exception as e:  # sign-in must work even when PayPal or email is down
        db.session.rollback()
        _log("login-restore", user, subscription_id, f"failed: {e} {getattr(e, 'details', '')}")


SUBSCRIPTION_ID_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-")


def link_subscription(user, subscription_id):
    """Admin: link an existing PayPal subscription to a member. Returns (ok, message).
    Changes only the PayPal fields (subscription ID, plan, paid level, status, paid through), never free access."""
    subscription_id = (subscription_id or "").strip().upper()
    if not subscription_id.startswith("I-") or not set(subscription_id) <= SUBSCRIPTION_ID_CHARS or len(subscription_id) > 64:
        return False, "That does not look like a PayPal subscription ID (they start with I-, for example I-ABC123XYZ)."
    other = User.query.filter(User.paypal_subscription_id == subscription_id, User.id != user.id).first()
    if other:
        return False, f"That subscription is already linked to {other.email} (user {other.id})."
    try:
        sub = paypal.get_subscription(subscription_id)
    except PayPalError as e:
        _log("admin-link", user, subscription_id, f"PayPal lookup failed: {e} {e.details}")
        if e.status == 404:
            return False, (f"PayPal has no subscription {subscription_id} in {'LIVE' if paypal.is_live() else 'SANDBOX'} "
                           "mode. Check the ID and PAYPAL_MODE.")
        return False, f"Could not check the subscription with PayPal: {e}"
    if sub.get("status") != "ACTIVE":
        return False, f"PayPal says this subscription is {sub.get('status')}, not ACTIVE. Nothing was changed."
    if not _owner_ok(user, sub):
        return False, (f"PayPal says this subscription was started by user {sub.get('custom_id')}, not user {user.id}. "
                       "Nothing was changed.")
    if Plan.by_paypal_id(sub.get("plan_id")) is None:
        return False, (f"PayPal plan {sub.get('plan_id')} is not in Plans and Prices "
                       f"({'paypal_plan_id' if paypal.is_live() else 'paypal_sandbox_plan_id'}). Nothing was changed.")
    replaced = user.paypal_subscription_id if user.paypal_subscription_id not in (None, subscription_id) else None
    status = activate_subscription(user, sub, cancel_replaced=False)
    if status is None:
        return False, "This subscription could not be applied. Nothing was changed."
    _log("admin-link", user, subscription_id, f"linked: level {user.tier_rank}, status {status}, "
                                              f"paid through {user.paid_through}")
    note = f" It replaced {replaced} on this account (that one was NOT cancelled in PayPal)." if replaced else ""
    return True, (f"Linked {subscription_id} to {user.email}: {user.current_plan.tier.name} (level {user.tier_rank}), "
                  f"status {status}, paid through {user.paid_through:%B %d, %Y}." if user.paid_through else
                  f"Linked {subscription_id} to {user.email}: level {user.tier_rank}, status {status}.") + note


@tcc.route('/subscription/confirm', methods=['POST'])
@limiter.limit("60 per hour")
@role_required()
def confirm_subscription():
    user = get_current_user()
    subscription_id = ((request.get_json(silent=True) or {}).get("subscription_id") or "").strip()
    if not subscription_id:
        return jsonify({"msg": "Missing subscription."}), 400
    try:
        sub = paypal.get_subscription(subscription_id)
    except PayPalError as e:
        _log("confirm", user, subscription_id, f"PayPal lookup failed: {e} {e.details}")
        return jsonify({"pending": True, "msg": "We could not check your payment with PayPal. Please try again in a minute."}), 502
    if not _owner_ok(user, sub):
        _log("confirm", user, subscription_id, f"refused: PayPal custom_id is {sub.get('custom_id')!r}")
        return jsonify({"msg": "This subscription belongs to a different account."}), 403
    if sub.get("status") in ("APPROVAL_PENDING", "APPROVED"):
        # Keep the ID now: if the browser gives up, the webhook, the next login or a refresh finishes it
        remember_subscription(user, subscription_id)
        return jsonify({"pending": True, "msg": "PayPal is finishing your payment. This usually takes a few seconds."}), 202

    try:
        status = activate_subscription(user, sub)
    except Exception as e:
        db.session.rollback()
        _log("confirm", user, subscription_id, f"saving failed: {e!r}")
        raise
    if status is None:
        _log("confirm", user, subscription_id, f"plan {sub.get('plan_id')} / status {sub.get('status')} is not ours")
        return jsonify({"msg": "This PayPal subscription is not for one of our plans."}), 400
    return jsonify({"msg": f"Welcome! Your {user.current_plan.tier.name} plan is active.",
                    "subscription": _subscription_summary(user), "user": user.serialize_account()})


@tcc.route('/subscription/sync', methods=['POST'])
@limiter.limit("30 per hour")
@role_required()
def resync_subscription():
    user = get_current_user()
    if not user.paypal_subscription_id:
        return jsonify(_subscription_summary(user))
    before_status, before_rank = user.subscription_status, user.tier_rank
    try:
        sync_subscription(user, paypal.get_subscription(user.paypal_subscription_id))
        db.session.commit()
    except PayPalError as e:
        _log("sync", user, user.paypal_subscription_id, f"failed: {e}")
        return jsonify({"msg": "We could not reach PayPal. Please try again in a minute."}), 502
    plan_status_emails(user, before_status, before_rank)
    return jsonify(_subscription_summary(user))


@tcc.route('/subscription/change', methods=['POST'])
@limiter.limit("10 per hour")
@role_required()
def change_subscription():
    user = get_current_user()
    if not user.paypal_subscription_id or user.subscription_status != "active":
        return jsonify({"msg": "You need an active plan to change it. Choose a plan below instead."}), 400
    plan_id = (request.get_json(silent=True) or {}).get("plan_id")
    plan = next((p for p in plan_options_for(user) if p.id == plan_id), None)
    if plan is None or not plan.paypal_id:
        return jsonify({"msg": "That plan is not available."}), 400
    if plan.id == user.current_plan_id:
        return jsonify({"msg": "You are already on this plan."}), 400
    frontend = (os.getenv("FRONTEND_URL") or request.host_url).rstrip("/")
    try:
        approve_url = paypal.revise_subscription(
            user.paypal_subscription_id, plan.paypal_id,
            return_url=f"{frontend}/tai-chi-company/account?plan_changed=1",
            cancel_url=f"{frontend}/tai-chi-company/account",
            brand_name=SiteSettings.get().app_name)
    except PayPalError as e:
        print(f"PayPal revise failed: {e} {e.details}")
        return jsonify({"msg": "PayPal could not change the plan right now. Please try again later."}), 502
    if not approve_url:
        # No approval needed (same price): PayPal changed it already
        before_status, before_rank = user.subscription_status, user.tier_rank
        sync_subscription(user, paypal.get_subscription(user.paypal_subscription_id))
        db.session.commit()
        plan_status_emails(user, before_status, before_rank)
        return jsonify({"msg": "Your plan has been changed.", "subscription": _subscription_summary(user)})
    return jsonify({"approve_url": approve_url})


@tcc.route('/subscription/cancel', methods=['POST'])
@limiter.limit("10 per hour")
@role_required()
def cancel_my_subscription():
    user = get_current_user()
    if not user.paypal_subscription_id or user.subscription_status not in ("active", "past_due"):
        return jsonify({"msg": "You do not have an active plan to cancel."}), 400
    reason = ((request.get_json(silent=True) or {}).get("reason") or "Cancelled by member").strip()
    try:
        paypal.cancel_subscription(user.paypal_subscription_id, reason)
    except PayPalError as e:
        print(f"PayPal cancel failed: {e} {e.details}")
        return jsonify({"msg": "PayPal could not cancel the plan right now. Please try again, or call us."}), 502
    before_status, before_rank = user.subscription_status, user.tier_rank
    user.subscription_status = "cancelled"
    user.cancelled_at = datetime.utcnow()
    user.next_billing_at = None
    db.session.commit()
    plan_status_emails(user, before_status, before_rank)
    until = user.paid_through.strftime("%B %d, %Y") if user.paid_through else "the end of your paid period"
    notify_school("Cancellation", f"{user.name or ''} <{user.email}> cancelled {user.current_plan.tier.name if user.current_plan else 'their plan'}. "
                  f"Access continues until {until}. Reason: {reason}")
    return jsonify({"msg": f"Your plan is cancelled. You can keep watching until {until}.",
                    "subscription": _subscription_summary(user)})


def _user_for_subscription(resource):
    sub_id = resource.get("billing_agreement_id") or resource.get("id")
    user = User.query.filter_by(paypal_subscription_id=sub_id).first() if sub_id else None
    custom_id = str(resource.get("custom_id") or resource.get("custom") or "")  # sales carry it as "custom"
    if user is None and custom_id.isdigit():
        user = db.session.get(User, int(custom_id))
    return user, sub_id


@tcc.route('/paypal/webhook', methods=['POST'])
@limiter.exempt  # comes from PayPal's servers; every event is verified with PayPal before use
def paypal_webhook():
    event = request.get_json(silent=True) or {}
    event_id, event_type = event.get("id"), event.get("event_type", "")
    if not event_id:
        return jsonify({"msg": "bad event"}), 400
    try:
        if not paypal.verify_webhook(request.headers, event):
            return jsonify({"msg": "signature check failed"}), 400
    except PayPalError as e:
        print(f"PayPal webhook could not be verified: {e}")
        return jsonify({"msg": "could not verify"}), 503  # PayPal will retry

    record = WebhookEvent(event_id=event_id, event_type=event_type, payload=event)
    db.session.add(record)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        record = WebhookEvent.query.filter_by(event_id=event_id).first()
        if record.processed_at:
            return jsonify({"ok": True, "duplicate": True})

    resource = event.get("resource") or {}
    email_after = None
    if event_type in SUBSCRIPTION_EVENTS or event_type == "PAYMENT.SALE.COMPLETED":
        user, sub_id = _user_for_subscription(resource)
        if user is not None and sub_id:
            try:
                sub = paypal.get_subscription(sub_id)
            except PayPalError as e:
                db.session.rollback()
                _log("webhook", user, sub_id, f"sync failed for {event_type}: {e}")
                return jsonify({"msg": "sync failed"}), 503  # not marked processed: PayPal retries
            own_new = (user.paypal_subscription_id not in (None, sub_id) and sub.get("custom_id") == str(user.id)
                       and sub.get("status") == "ACTIVE" and user.subscription_status not in ("active", "past_due"))
            if user.paypal_subscription_id not in (None, sub_id) and not own_new:
                pass  # an old, replaced subscription: ignore
            else:
                before = user.subscription_status
                before_rank = user.tier_rank
                if own_new:
                    # The member's new subscription whose confirm never reached us: the stored one is not billing
                    _log("webhook", user, sub_id, f"replacing non-billing {user.paypal_subscription_id}")
                    user.paypal_subscription_id = sub_id
                sync_subscription(user, sub)
                if user.subscription_status == "active" and before != "active" and user.current_plan:
                    notify_school("New subscriber", f"{user.name or ''} <{user.email}> subscribed to "
                                  f"{user.current_plan.tier.name} ({user.current_plan.interval}ly, ${user.current_plan.price}).")
                if event_type == "BILLING.SUBSCRIPTION.CANCELLED" and before != "cancelled":
                    until = user.paid_through.strftime("%B %d, %Y") if user.paid_through else "the end of the paid period"
                    notify_school("Cancellation", f"{user.name or ''} <{user.email}> cancelled through PayPal. "
                                  f"Access continues until {until}.")
                email_after = (user, before, before_rank)
        elif event_type.startswith("BILLING.SUBSCRIPTION."):
            _log("webhook", None, sub_id, f"{event_type}: no member found (custom_id {resource.get('custom_id')!r})")
    record.processed_at = datetime.utcnow()
    db.session.commit()
    if email_after:
        # Member emails (thank you, cancelled, payment problem). The same change never emails twice.
        plan_status_emails(*email_after, event_type=event_type)
    return jsonify({"ok": True})
