"""Email routes: the one-click "Stop these emails" link (works without signing in) and the Studio's
"Email members about this video?" Yes / No."""
import html
from flask import jsonify, request, Response
from .models import db, Video
from .extensions import limiter
from .member_emails import user_from_unsubscribe_token, announce_video, announcement_summary, app_url
from .tcc_auth import role_required, get_current_user
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
    """GET (the link in the email) and POST (one-click from the mail app) both turn off new-video emails.
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
        return _page("Emails turned on", "<h1>New-video emails are on again</h1>"
                     "<p>Thank you! We will email you when new videos are added.</p>"
                     f"<p><a href=\"{account}\">Manage all your email choices</a></p>")
    safe = html.escape(token)
    return _page("You will not get these emails", "<h1>Done. You will not get new-video emails</h1>"
                 f"<p>We have stopped the new-video emails to {html.escape(user.email)}.</p>"
                 "<p>You will still get emails about your account and payments.</p>"
                 f"<form method=\"post\"><input type=\"hidden\" name=\"t\" value=\"{safe}\">"
                 "<button type=\"submit\" name=\"action\" value=\"resubscribe\">Oops, keep sending them</button></form>"
                 f"<p><a href=\"{account}\">Manage all your email choices</a></p>")


@tcc.route('/studio/videos/<int:video_id>/announce', methods=['POST'])
@role_required("teacher", "admin")
def studio_announce(video_id):
    """{"send": true} emails members about the video (in batches); {"send": false} records "No"."""
    video = db.session.get(Video, video_id)
    if video is None:
        return jsonify({"msg": "Video not found."}), 404
    if (request.get_json(silent=True) or {}).get("send"):
        announcement, error = announce_video(video, get_current_user())
        if error:
            return jsonify({"msg": error}), 400
        msg = (f"Thank you. {announcement.total} members will get an email, a few at a time."
               if announcement.total else "No members have new-video emails turned on, so no emails were sent.")
    else:
        if video.announce_choice != "yes":
            video.announce_choice = "no"
            db.session.commit()
        msg = "OK. Members will not be emailed about this video."
    return jsonify({"msg": msg, "announcement": announcement_summary(video)})
