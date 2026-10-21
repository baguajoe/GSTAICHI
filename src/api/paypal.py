"""Small PayPal REST client for subscriptions (sandbox or live, chosen by PAYPAL_MODE).

Uses the same PayPal account as the book and DVD shop. Live: PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET;
webhook checks also need PAYPAL_WEBHOOK_ID. While PAYPAL_MODE=sandbox the PAYPAL_SANDBOX_* versions are used
when set, so the shop can keep its live PAYPAL_CLIENT_ID during subscription testing.
"""
import os
import time
import requests

_token_cache = {"token": None, "expires": 0, "key": None}


class PayPalError(Exception):
    def __init__(self, message, status=None, details=None):
        super().__init__(message)
        self.status = status
        self.details = details


def is_live():
    return os.getenv("PAYPAL_MODE", "sandbox").lower() == "live"


def setting(name):
    """PAYPAL_<name>, or PAYPAL_SANDBOX_<name> while testing in sandbox mode (if it is set)."""
    if not is_live() and os.getenv(f"PAYPAL_SANDBOX_{name}"):
        return os.getenv(f"PAYPAL_SANDBOX_{name}")
    return os.getenv(f"PAYPAL_{name}")


def api_base():
    override = os.getenv("PAYPAL_API_BASE")  # only for automated tests
    if override:
        return override.rstrip("/")
    return "https://api-m.paypal.com" if is_live() else "https://api-m.sandbox.paypal.com"


def is_configured():
    return bool(setting("CLIENT_ID") and setting("CLIENT_SECRET"))


def _access_token():
    client_id, secret = setting("CLIENT_ID"), setting("CLIENT_SECRET")
    if not client_id or not secret:
        raise PayPalError("PayPal is not set up yet (PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET are missing, "
                          "or PAYPAL_SANDBOX_CLIENT_ID / PAYPAL_SANDBOX_CLIENT_SECRET while testing).")
    cache_key = (api_base(), client_id)
    if _token_cache["token"] and _token_cache["key"] == cache_key and _token_cache["expires"] > time.time() + 60:
        return _token_cache["token"]
    resp = requests.post(f"{api_base()}/v1/oauth2/token", auth=(client_id, secret),
                         data={"grant_type": "client_credentials"}, timeout=20)
    if resp.status_code != 200:
        raise PayPalError("Could not sign in to PayPal. Check the client ID, secret and PAYPAL_MODE "
                          "(sandbox mode uses the PAYPAL_SANDBOX_* keys when they are set).",
                          resp.status_code, resp.text[:500])
    data = resp.json()
    _token_cache.update(token=data["access_token"], expires=time.time() + int(data.get("expires_in", 300)), key=cache_key)
    return data["access_token"]


def _request(method, path, json=None, expected=(200, 201, 204)):
    resp = requests.request(method, f"{api_base()}{path}", json=json, timeout=30, headers={
        "Authorization": f"Bearer {_access_token()}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    })
    if resp.status_code not in expected:
        try:
            details = resp.json()
            message = details.get("message") or details.get("name") or resp.reason
        except ValueError:
            details, message = resp.text[:500], resp.reason
        raise PayPalError(f"PayPal said: {message}", resp.status_code, details)
    return resp.json() if resp.content else {}


def create_product(name, description):
    return _request("POST", "/v1/catalogs/products", {
        "name": name, "description": description[:256], "type": "SERVICE", "category": "EDUCATIONAL_AND_TEXTBOOKS",
    })["id"]


def create_plan(product_id, name, price, interval):
    return _request("POST", "/v1/billing/plans", {
        "product_id": product_id,
        "name": name[:127],
        "status": "ACTIVE",
        "billing_cycles": [{
            "frequency": {"interval_unit": "YEAR" if interval == "year" else "MONTH", "interval_count": 1},
            "tenure_type": "REGULAR",
            "sequence": 1,
            "total_cycles": 0,  # until cancelled
            "pricing_scheme": {"fixed_price": {"value": f"{price:.2f}", "currency_code": "USD"}},
        }],
        "payment_preferences": {"auto_bill_outstanding": True, "payment_failure_threshold": 3},
    })["id"]


def get_subscription(subscription_id):
    return _request("GET", f"/v1/billing/subscriptions/{subscription_id}")


def revise_subscription(subscription_id, plan_id, return_url, cancel_url, brand_name):
    """Starts an upgrade/downgrade. Returns the PayPal page where the member approves the new price."""
    data = _request("POST", f"/v1/billing/subscriptions/{subscription_id}/revise", {
        "plan_id": plan_id,
        "application_context": {"brand_name": brand_name[:127], "return_url": return_url, "cancel_url": cancel_url},
    })
    approve = next((l["href"] for l in data.get("links", []) if l.get("rel") == "approve"), None)
    return approve


def cancel_subscription(subscription_id, reason):
    _request("POST", f"/v1/billing/subscriptions/{subscription_id}/cancel", {"reason": reason[:127]}, expected=(204,))


def verify_webhook(headers, event):
    webhook_id = setting("WEBHOOK_ID")
    if not webhook_id:
        raise PayPalError("PAYPAL_WEBHOOK_ID (or PAYPAL_SANDBOX_WEBHOOK_ID while testing) is not set, "
                          "so PayPal notifications cannot be checked.")
    result = _request("POST", "/v1/notifications/verify-webhook-signature", {
        "auth_algo": headers.get("PAYPAL-AUTH-ALGO"),
        "cert_url": headers.get("PAYPAL-CERT-URL"),
        "transmission_id": headers.get("PAYPAL-TRANSMISSION-ID"),
        "transmission_sig": headers.get("PAYPAL-TRANSMISSION-SIG"),
        "transmission_time": headers.get("PAYPAL-TRANSMISSION-TIME"),
        "webhook_id": webhook_id,
        "webhook_event": event,
    })
    return result.get("verification_status") == "SUCCESS"
