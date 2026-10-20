"""
Encode master videos on this computer and upload them to Cloudflare R2 for Tai Chi Company.

Runs on Windows, Mac or Linux with Python 3.10+, ffmpeg and rclone. See tools/README.md for setup.

    python tools/encode_and_upload.py --videos "D:\\Tai Chi Masters" --site https://gstaichi.org --email you@example.com

For each row of videos.csv it:
  1. converts the file into encrypted multi-bitrate streaming files (src/api/video_pipeline.py),
  2. uploads them to <bucket>/<slug>/ with rclone,
  3. sends the details and the video key to the site (admin account required), which marks the video Ready.
Videos that are already Ready on the site are skipped, so it is safe to run again after a problem.
The video key is sent only to the site, over HTTPS. It is never uploaded to R2 or kept on this computer.
"""
import argparse
import csv
import getpass
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))
from api.video_pipeline import encode_video, PipelineError  # noqa: E402

SECTIONS = ("beginner", "intermediate", "advanced", "qigong", "vincents-corner")


def say(msg=""):
    print(msg, flush=True)


def api(site, path, token=None, body=None):
    req = urllib.request.Request(site.rstrip("/") + path, method="POST" if body is not None else "GET")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=120) as resp:
            return json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read().decode()).get("msg")
        except Exception:
            msg = None
        raise RuntimeError(f"The site said: {msg or e.reason} (HTTP {e.code})") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"Could not reach {site}: {e.reason}") from None


def read_csv(path):
    rows, problems = [], []
    with open(path, newline="", encoding="utf-8-sig") as f:  # utf-8-sig: files saved by Excel
        for n, row in enumerate(csv.DictReader(f), start=2):
            row = {k.strip().lower(): (v or "").strip() for k, v in row.items() if k}
            if not row.get("slug"):
                continue
            if row.get("section") not in SECTIONS:
                problems.append(f"line {n}: section must be one of {', '.join(SECTIONS)}")
            if row.get("tier") and not row["tier"].isdigit():
                problems.append(f"line {n}: tier must be a number (1 Beginner, 2 Intermediate, 3 Advanced)")
            rows.append(row)
    return rows, problems


def check_programs():
    missing = [p for p in ("ffmpeg", "ffprobe", "rclone") if shutil.which(p) is None]
    if missing:
        say(f"These programs were not found: {', '.join(missing)}.")
        say("Install them as described in tools/README.md, then close and reopen this window.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Encode and upload Tai Chi Company videos.")
    parser.add_argument("--csv", default=os.path.join(HERE, "videos.csv"), help="list of videos (default tools/videos.csv)")
    parser.add_argument("--videos", required=True, help="folder that holds the master video files")
    parser.add_argument("--site", required=True, help="the site address, e.g. https://gstaichi.org")
    parser.add_argument("--email", required=True, help="your admin email for the site")
    parser.add_argument("--remote", default="r2", help="rclone remote name (default r2)")
    parser.add_argument("--bucket", default="taichi-streams", help="R2 bucket for streams (default taichi-streams)")
    parser.add_argument("--work", default=os.path.join(os.path.expanduser("~"), "tcc-encode"),
                        help="folder for temporary files (default: tcc-encode in your home folder)")
    parser.add_argument("--preset", default="medium", help="x264 speed/quality preset (default medium)")
    parser.add_argument("--only", action="append", help="only this slug (can be given more than once)")
    parser.add_argument("--force", action="store_true", help="encode again even if the video is already Ready")
    parser.add_argument("--keep", action="store_true", help="keep the encoded files on this computer afterwards")
    args = parser.parse_args()

    check_programs()
    rows, problems = read_csv(args.csv)
    if problems:
        say("Please fix these lines in the video list:")
        for p in problems:
            say("  " + p)
        sys.exit(1)
    if args.only:
        rows = [r for r in rows if r["slug"] in args.only]

    password = os.getenv("TCC_PASSWORD") or getpass.getpass(f"Password for {args.email}: ")
    try:
        token = api(args.site, "/api/login", body={"email": args.email, "password": password})["token"]
        status = api(args.site, "/api/tcc/admin/videos/status", token)
    except RuntimeError as e:
        say(str(e))
        sys.exit(1)
    ready = {v["slug"] for v in status["videos"] if v["ready"]}
    key_uri_base = status["key_uri_base"]
    os.makedirs(args.work, exist_ok=True)

    done, skipped, failed = [], [], []
    for i, row in enumerate(rows, start=1):
        slug = row["slug"]
        say(f"\n[{i}/{len(rows)}] {row.get('title') or slug}")
        if slug in ready and not args.force:
            say("  Already Ready on the site, skipping.")
            skipped.append(slug)
            continue
        src = os.path.join(args.videos, row.get("filename") or "")
        if not row.get("filename") or not os.path.isfile(src):
            say(f"  Video file not found: {src}  (check the filename column)")
            failed.append((slug, "file not found"))
            continue

        out_dir = os.path.join(args.work, slug)
        shutil.rmtree(out_dir, ignore_errors=True)
        started = time.time()
        try:
            say("  Encoding (this can take a while)...")
            result = encode_video(src, out_dir, slug, key_uri_base + slug, preset=args.preset, log=lambda m: None)
            say(f"  Encoded in {int(time.time() - started) // 60} min. Uploading...")
            # sync makes the bucket folder match exactly, removing files left from an earlier encode
            subprocess.run(["rclone", "sync", out_dir, f"{args.remote}:{args.bucket}/{slug}",
                            "--transfers", "8", "--checkers", "8", "--stats-one-line", "--stats", "10s"], check=True)
            body = dict(result, title=row.get("title"), section=row.get("section"),
                        tier_rank=int(row["tier"]) if row.get("tier") else None)
            api(args.site, "/api/tcc/admin/videos/import", token, body)
            say("  Done. The video is Ready on the site.")
            done.append(slug)
        except PipelineError as e:
            say(f"  Problem with this video: {e}")
            failed.append((slug, str(e)))
        except subprocess.CalledProcessError:
            say("  The upload failed. Check your internet connection and rclone setup, then run again.")
            failed.append((slug, "upload failed"))
        except RuntimeError as e:
            say(f"  {e}")
            failed.append((slug, str(e)))
        finally:
            result = None  # drop the key from memory as soon as possible
            if not args.keep:
                shutil.rmtree(out_dir, ignore_errors=True)

    say("\n==== Summary ====")
    say(f"Ready now: {len(done)}   Already done: {len(skipped)}   Problems: {len(failed)}")
    for slug, reason in failed:
        say(f"  {slug}: {reason}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
