"""
Background worker: turns Studio uploads into protected streaming videos.

Runs on Render as a Background Worker with ffmpeg installed (see Dockerfile.worker and render.yaml):
    python src/worker.py           # run forever, checking for new jobs every 15 seconds
    python src/worker.py --once    # process what is waiting, then stop (useful for testing)

For each queued EncodingJob it downloads the master from taichi-masters, runs src/api/video_pipeline.py,
uploads the result to taichi-streams/<slug>/ and marks the video Ready. Failures are retried up to 3 times;
then the video is marked Failed with a plain-English reason and the uploader is emailed.
"""
import argparse
import os
import shutil
import sys
import tempfile
import time
import traceback
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app  # noqa: E402
from api.models import db, EncodingJob, Video, PlaybackSession, Question, SiteSettings  # noqa: E402
from api.video_pipeline import encode_video, PipelineError  # noqa: E402
from api.tcc_encoding import apply_encode_result  # noqa: E402
from api.tcc_questions import notify_member_answered  # noqa: E402
from api.notify import email, signature  # noqa: E402
from api import r2  # noqa: E402

MAX_ATTEMPTS = 3
POLL_SECONDS = 15
STUCK_AFTER = timedelta(hours=4)  # a job "running" this long means the worker was restarted mid-job


def log(msg):
    print(f"{datetime.utcnow():%Y-%m-%d %H:%M:%S} {msg}", flush=True)


def claim_job():
    """Takes the oldest queued job. SKIP LOCKED lets several workers run side by side safely."""
    job = (EncodingJob.query.filter_by(status="queued").order_by(EncodingJob.created_at)
           .with_for_update(skip_locked=True).first())
    if job is None:
        db.session.rollback()
        return None
    job.status = "running"
    job.attempts = (job.attempts or 0) + 1
    job.started_at = datetime.utcnow()
    job.error = None
    db.session.commit()
    return job


def plain_reason(error):
    if isinstance(error, PipelineError):
        return str(error)
    text = f"{type(error).__name__}: {error}"
    if "NoSuchKey" in text or "404" in text:
        return "The uploaded file could not be found in storage. Please upload it again."
    if "R2NotConfigured" in text:
        return "Video storage is not set up yet. Please ask the site administrator."
    if "No space left" in text:
        return "The video is too big for the processing computer. Please ask the site administrator."
    if "KeyVault" in text or "KEY_ENCRYPTION_SECRET" in text:
        return "The site is missing a security setting (KEY_ENCRYPTION_SECRET). Please ask the site administrator."
    return "Something went wrong while preparing the video. It will be tried again automatically."


def email_uploader(video, ready, reason=None):
    uploader = video.uploader
    if uploader is None:
        return
    settings = SiteSettings.get()
    frontend = (os.getenv("FRONTEND_URL") or "").rstrip("/")
    if ready:
        when = ("It is published now." if not video.publish_at or video.publish_at <= datetime.utcnow()
                else f"It will appear for members on {video.publish_at:%B %d, %Y at %H:%M} (UTC).")
        subject = f"Your video is ready: {video.title}"
        body = f"Good news! \"{video.title}\" is ready. {when}\n\nWatch it: {frontend}/tai-chi-company/watch/{video.slug}"
    else:
        subject = f"Your video could not be prepared: {video.title}"
        body = (f"\"{video.title}\" could not be prepared after {MAX_ATTEMPTS} tries.\n\nReason: {reason}\n\n"
                f"Open the Studio and press Retry, or upload the file again: {frontend}/tai-chi-company/studio")
    email(uploader.email, f"[{settings.app_name}] {subject}", f"{body}\n\n{signature()}")


def process(job):
    video = db.session.get(Video, job.video_id)
    if video is None or not video.master_r2_key:
        job.status, job.error, job.finished_at = "failed", "Video or uploaded file missing.", datetime.utcnow()
        db.session.commit()
        return
    slug, master_key, chapters = video.slug, video.master_r2_key, video.chapters
    log(f"Job {job.id}: encoding {slug} (try {job.attempts} of {MAX_ATTEMPTS})")
    # End the read transaction before the long download and encode, and touch no database objects until
    # it is done. An open transaction holds locks on the video table for the whole encode, which blocks
    # migrations (every Render deploy runs one).
    db.session.commit()
    work = tempfile.mkdtemp(prefix=f"tcc-{slug}-")
    try:
        ext = os.path.splitext(master_key)[1] or ".mp4"
        src = os.path.join(work, f"master{ext}")
        r2.download(r2.masters_bucket(), master_key, src)
        base = (os.getenv("BACKEND_URL") or "").rstrip("/")
        if not base:
            raise PipelineError("BACKEND_URL is not set on the worker, so the video key address cannot be made.")
        result = encode_video(src, os.path.join(work, "out"), slug, f"{base}/api/tcc/key/{slug}",
                              chapters=chapters, preset=os.getenv("ENCODE_PRESET", "veryfast"), log=log)
        r2.delete_prefix(r2.streams_bucket(), slug)  # remove files from an earlier encode
        r2.upload_folder(os.path.join(work, "out"), r2.streams_bucket(), slug)
        apply_encode_result(video, result)
        result = None
        job.status, job.finished_at = "done", datetime.utcnow()
        db.session.commit()
        log(f"Job {job.id}: {video.slug} is ready")
        email_uploader(video, ready=True)
        for question in Question.query.filter_by(answer_video_id=video.id, member_notified_at=None).all():
            notify_member_answered(question)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        reason = plain_reason(e)
        log(f"Job {job.id}: failed: {e}\n{traceback.format_exc()}")
        job = db.session.get(EncodingJob, job.id)
        video = db.session.get(Video, job.video_id)
        job.error = f"{reason}\n\n{type(e).__name__}: {e}"[:4000]
        if job.attempts < MAX_ATTEMPTS and not isinstance(e, PipelineError):
            job.status = "queued"  # try again
        else:
            job.status, job.finished_at = "failed", datetime.utcnow()
            video.status, video.failure_reason = "failed", reason
        db.session.commit()
        if job.status == "failed":
            email_uploader(video, ready=False, reason=reason)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def housekeeping():
    now = datetime.utcnow()
    for job in EncodingJob.query.filter(EncodingJob.status == "running", EncodingJob.started_at < now - STUCK_AFTER).all():
        job.status = "queued" if job.attempts < MAX_ATTEMPTS else "failed"
        log(f"Job {job.id} was stuck; now {job.status}")
    for session in PlaybackSession.query.filter(PlaybackSession.is_active.is_(True),
                                                PlaybackSession.last_heartbeat_at < now - timedelta(minutes=2)).all():
        session.end("timeout")
    db.session.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="process waiting jobs, then exit")
    args = parser.parse_args()
    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        sys.exit("ffmpeg and ffprobe must be installed on the worker.")
    log("Worker started")
    with app.app_context():
        while True:
            try:
                housekeeping()
                job = claim_job()
            except Exception as e:
                db.session.rollback()
                log(f"Database problem: {e}")
                job = None
                time.sleep(POLL_SECONDS)
            if job is not None:
                process(job)
                continue
            if args.once:
                break
            time.sleep(POLL_SECONDS)
    log("Worker stopped")


if __name__ == "__main__":
    main()
