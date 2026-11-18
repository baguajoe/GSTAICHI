"""Email routes: the one-click "Stop these emails" link for the weekly "New this week" email (works without
signing in). New videos and articles are no longer emailed one by one: they go into the weekly digest."""
import html
from flask import request, Response
from .models import db
from .extensions import limiter
from .member_emails import user_from_unsubscribe_token, app_url
from .taichi_company import tcc

PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>{title}</title>
<style>
 body{{margin:0;background:#f4efe9;font-family:Arial,Helvetica,sans-serif;color:#1a1a1a}}
 header{{background:#590d0d;color:#fff;padding:22px 24px;font:bold 26px Georgia,serif}}
 main{{max-width:600px;margin:24px auto;background:#fff;border-radius:10px;padding:28px 24px}}
 h1{{color:#590d0d;font-size:28px;margin-top:0}} p{{font-size:20px;line-height:1.6}}
 button,a.btn{{display:inline-block;min-height:56px;padding:14px 26px;font-size:20px;font-weight:bold;border-radius:8px;
   border:2px solid #590d0d;background:#fff;color:#590d0d;cursor:pointer;text-decoration:none;margin:6px 0}}
 a{{color:#590d0d}}
</style></head><body><header>The Tai Chi Company</header><main>{body}</main></body></html>"""


def _page(title, body, status=200):
    return Response(PAGE.format(title=html.escape(title), body=body), status=status, mimetype="text/html")


@tcc.route('/email/unsubscribe', methods=['GET', 'POST'])
@limiter.limit("30 per minute")
def email_unsubscribe():
    """GET (the link in the email) and POST (one-click from the mail app) both turn off the "New this week" email.
    POST with action=resubscribe turns them back on."""
    token = request.values.get("t", "")
    user = user_from_unsubscribe_token(token)
    if user is None:
        return _page("Link not valid", "<h1>This link is not valid</h1><p>Please manage your emails on your "
                     f"<a href=\"{html.escape(app_url('/account#emails'))}\">Account page</a>.</p>", 400)
    resubscribe = request.method == "POST" and request.form.get("action") == "resubscribe"
    user.email_new_videos = bool(resubscribe)
    db.session.commit()
    account = html.escape(app_url("/account#emails"))
    if resubscribe:
        return _page("Emails turned on", "<h1>The weekly email is on again</h1>"
                     "<p>Thank you! Once a week we will email you the new articles and videos.</p>"
                     f"<p><a href=\"{account}\">Manage all your email choices</a></p>")
    safe = html.escape(token)
    return _page("You will not get these emails", "<h1>Done. You will not get the weekly email</h1>"
                 f"<p>We have stopped the \"New this week\" emails to {html.escape(user.email)}.</p>"
                 "<p>You will still get emails about your account and payments.</p>"
                 f"<form method=\"post\"><input type=\"hidden\" name=\"t\" value=\"{safe}\">"
                 "<button type=\"submit\" name=\"action\" value=\"resubscribe\">Oops, keep sending them</button></form>"
                 f"<p><a href=\"{account}\">Manage all your email choices</a></p>")

