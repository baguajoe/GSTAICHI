"""
Creates the PayPal product and the subscription plans (3 tiers x monthly/annual) and saves the PayPal
plan IDs in the Plan table. Uses PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET and PAYPAL_MODE from the environment,
so run it once with PAYPAL_MODE=sandbox for testing and again with PAYPAL_MODE=live at launch.

    pipenv run python scripts/create_paypal_plans.py            # plans that have no PayPal ID yet
    pipenv run python scripts/create_paypal_plans.py --replace  # all active plans, e.g. after switching to live
    pipenv run python scripts/create_paypal_plans.py --dry-run  # only show what would happen

Prices come from the Plan table (edit them in /admin first). PayPal plans cannot change price later: to change a
price, add a new Plan row in /admin (founding members keep the old one) and run this again.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from app import app  # noqa: E402
from api.models import db, Plan, SiteSettings  # noqa: E402
from api import paypal  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--replace", action="store_true", help="create new PayPal plans even for plans that have an ID")
    parser.add_argument("--product-id", help="reuse an existing PayPal product instead of creating one")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with app.app_context():
        mode = os.getenv("PAYPAL_MODE", "sandbox")
        settings = SiteSettings.get()
        plans = Plan.query.filter(Plan.is_active.is_(True)).all()
        todo = [p for p in plans if args.replace or not p.paypal_plan_id]
        print(f"PayPal mode: {mode}. {len(todo)} of {len(plans)} active plans need a PayPal plan.")
        if not todo:
            return
        for p in todo:
            print(f"  {p.tier.name} {p.interval}: ${p.price}")
        if args.dry_run:
            return
        if not paypal.is_configured():
            sys.exit("Set PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET first (see .env.example).")

        product_id = args.product_id or paypal.create_product(
            settings.app_name, f"{settings.app_name} video lessons from {settings.school_name}".strip())
        print(f"Product: {product_id}")
        for p in todo:
            label = "Monthly" if p.interval == "month" else "Annual"
            founding = " (Founding member)" if p.is_founding else ""
            p.paypal_plan_id = paypal.create_plan(product_id, f"{settings.app_name} {p.tier.name} {label}{founding}",
                                                  float(p.price), p.interval)
            db.session.commit()  # save each one as it is made, so a failure part-way loses nothing
            print(f"  {p.tier.name} {label}: {p.paypal_plan_id}")
        print("Done. The plan IDs are saved; members can subscribe now.")


if __name__ == "__main__":
    main()
