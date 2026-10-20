"""
Video encoding pipeline shared by tools/encode_and_upload.py (run on a PC) and src/worker.py (Render worker).

Standard library only, plus the ffmpeg and ffprobe programs, so it runs anywhere ffmpeg is installed.

encode_video() turns one master file into:
    <out_dir>/master.m3u8              multi-bitrate HLS playlist
    <out_dir>/v0/index.m3u8, seg_*.ts  one folder per rendition, 6 second AES-128 encrypted segments
    <out_dir>/thumbs/thumb_<pct>_<size>.jpg   4 thumbnail options x 2 sizes
    <out_dir>/chapters.vtt             only if chapters were given
and returns the AES key separately. The key is written only to a private temporary folder for ffmpeg
and deleted afterwards; it never goes into <out_dir>, so it can never be uploaded with the stream files.
"""
import json
import os
import secrets
import shutil
import subprocess
import tempfile

SEGMENT_SECONDS = 6
THUMBNAIL_PERCENTS = (15, 30, 50, 70)  # not the first frame: many videos open with warnings or black title cards
DEFAULT_THUMBNAIL_PERCENT = 30
THUMBNAIL_SIZES = (1280, 480)

# (short side of the picture, video bitrate kbps, audio bitrate kbps). Short side, so phone videos filmed
# upright get the same quality steps as landscape ones.
LADDER = (
    (1080, 5000, 160),
    (720, 2800, 128),
    (480, 1400, 96),
)


class PipelineError(Exception):
    """A problem with the video file itself, explained in plain English for the teacher."""


def _run(cmd, log=None):
    if log:
        log("  $ " + " ".join(str(c) for c in cmd))
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd, result.stdout, result.stderr)
    return result.stdout


def probe(path, ffprobe="ffprobe"):
    """Size as shown on screen (rotation applied), duration and whether there is sound."""
    try:
        out = _run([ffprobe, "-v", "error", "-print_format", "json", "-show_streams", "-show_format", path])
    except subprocess.CalledProcessError as e:
        raise PipelineError("This file could not be read as a video. It may be damaged or in an unusual format.") from e
    info = json.loads(out)
    video = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"
                  and not (s.get("disposition") or {}).get("attached_pic")), None)
    if video is None:
        raise PipelineError("This file has no video picture in it.")
    width, height = int(video["width"]), int(video["height"])

    rotation = 0
    for side in video.get("side_data_list") or []:
        if "rotation" in side:
            rotation = int(float(side["rotation"]))
    if not rotation and (video.get("tags") or {}).get("rotate"):
        rotation = int(video["tags"]["rotate"])
    if abs(rotation) % 180 == 90:
        width, height = height, width  # phones store upright video sideways plus a rotation flag

    duration = float(info.get("format", {}).get("duration") or video.get("duration") or 0)
    if duration <= 0:
        raise PipelineError("The length of this video could not be read. The file may be incomplete.")
    has_audio = any(s.get("codec_type") == "audio" for s in info.get("streams", []))
    return {"width": width, "height": height, "duration": duration, "has_audio": has_audio}


def _even(n):
    return max(2, int(round(n / 2.0)) * 2)


def plan_renditions(width, height):
    """Renditions at or below the source size only. Never upscales, never stretches."""
    short_side = min(width, height)
    plan = []
    for target, video_kbps, audio_kbps in LADDER:
        if target > short_side:
            continue
        scale = target / short_side
        plan.append({
            "name": f"{target}p",
            "width": _even(width * scale),
            "height": _even(height * scale),
            "video_kbps": video_kbps,
            "audio_kbps": audio_kbps,
        })
    if not plan:
        # Smaller than 480p: keep the original size
        plan.append({"name": f"{short_side}p", "width": _even(width), "height": _even(height),
                     "video_kbps": LADDER[-1][1], "audio_kbps": LADDER[-1][2]})
    return plan


def chapters_to_vtt(chapters, duration):
    """chapters: [{"start": seconds, "label": "..."}] -> WebVTT text."""
    def stamp(t):
        t = max(0.0, float(t))
        h, rem = divmod(t, 3600)
        m, s = divmod(rem, 60)
        return f"{int(h):02d}:{int(m):02d}:{s:06.3f}"

    items = sorted((c for c in chapters if str(c.get("label", "")).strip()), key=lambda c: float(c["start"]))
    lines = ["WEBVTT", ""]
    for i, chapter in enumerate(items):
        start = float(chapter["start"])
        end = float(items[i + 1]["start"]) if i + 1 < len(items) else duration
        if end <= start:
            continue
        lines += [str(i + 1), f"{stamp(start)} --> {stamp(end)}", str(chapter["label"]).strip(), ""]
    return "\n".join(lines)


def _encode_hls(src, out_dir, plan, has_audio, key_uri, key_hex, iv_hex, ffmpeg, preset, log):
    key_dir = tempfile.mkdtemp(prefix="tcc-key-")
    try:
        key_file = os.path.join(key_dir, "video.key")
        with open(key_file, "wb") as f:
            f.write(bytes.fromhex(key_hex))
        key_info = os.path.join(key_dir, "key_info.txt")
        with open(key_info, "w") as f:
            f.write(f"{key_uri}\n{key_file}\n{iv_hex}\n")

        n = len(plan)
        splits = "".join(f"[s{i}]" for i in range(n))
        filters = [f"[0:v]split={n}{splits}"]
        for i, r in enumerate(plan):
            filters.append(f"[s{i}]scale={r['width']}:{r['height']}:flags=lanczos,setsar=1,format=yuv420p[v{i}]")

        cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", src,
               "-filter_complex", ";".join(filters)]
        stream_map = []
        for i, r in enumerate(plan):
            cmd += ["-map", f"[v{i}]",
                    f"-c:v:{i}", "libx264", f"-profile:v:{i}", "high", f"-preset:v:{i}", preset,
                    f"-b:v:{i}", f"{r['video_kbps']}k", f"-maxrate:v:{i}", f"{int(r['video_kbps'] * 1.07)}k",
                    f"-bufsize:v:{i}", f"{int(r['video_kbps'] * 1.5)}k"]
            if has_audio:
                cmd += ["-map", "0:a:0", f"-c:a:{i}", "aac", f"-b:a:{i}", f"{r['audio_kbps']}k", f"-ac:a:{i}", "2"]
                stream_map.append(f"v:{i},a:{i},name:{r['name']}")
            else:
                stream_map.append(f"v:{i},name:{r['name']}")
        cmd += [
            # a keyframe exactly every segment, so every rendition switches cleanly
            "-force_key_frames", f"expr:gte(t,n_forced*{SEGMENT_SECONDS})", "-sc_threshold", "0",
            "-f", "hls", "-hls_time", str(SEGMENT_SECONDS), "-hls_playlist_type", "vod",
            "-hls_flags", "independent_segments", "-hls_segment_type", "mpegts",
            "-hls_key_info_file", key_info,
            "-hls_segment_filename", os.path.join(out_dir, "%v", "seg_%04d.ts"),
            "-master_pl_name", "master.m3u8",
            "-var_stream_map", " ".join(stream_map),
            os.path.join(out_dir, "%v", "index.m3u8"),
        ]
        try:
            _run(cmd, log)
        except subprocess.CalledProcessError as e:
            raise PipelineError("The video could not be converted for streaming. The file may be damaged.") from e
    finally:
        shutil.rmtree(key_dir, ignore_errors=True)


def _make_thumbnails(src, out_dir, slug, info, ffmpeg, log):
    thumbs_dir = os.path.join(out_dir, "thumbs")
    os.makedirs(thumbs_dir, exist_ok=True)
    long_side = max(info["width"], info["height"])
    options = []
    for pct in THUMBNAIL_PERCENTS:
        at = info["duration"] * pct / 100.0
        option = {"percent": pct}
        for size in THUMBNAIL_SIZES:
            box = min(size, long_side)  # never upscale
            name = f"thumb_{pct}_{size}.jpg"
            try:
                _run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{at:.2f}", "-i", src,
                      "-frames:v", "1", "-vf",
                      f"scale=w={box}:h={box}:force_original_aspect_ratio=decrease:force_divisible_by=2:flags=lanczos",
                      "-q:v", "3", os.path.join(thumbs_dir, name)], log)
            except subprocess.CalledProcessError as e:
                raise PipelineError("Pictures for the video could not be made. The file may be damaged.") from e
            option["large" if size == THUMBNAIL_SIZES[0] else "small"] = f"{slug}/thumbs/{name}"
        options.append(option)
    return options


def encode_video(src, out_dir, slug, key_uri, chapters=None, ffmpeg="ffmpeg", ffprobe="ffprobe",
                 preset="medium", log=print):
    """
    Encode one video. out_dir must be empty or missing; its contents are what gets uploaded to
    <streams bucket>/<slug>/. Returns a dict for the admin import endpoint, including key_hex/iv_hex,
    which must be sent to the server and never stored next to the stream files.
    """
    if not os.path.isfile(src):
        raise PipelineError(f"The video file was not found: {src}")
    if os.path.isdir(out_dir) and os.listdir(out_dir):
        raise PipelineError(f"The output folder is not empty: {out_dir}")
    os.makedirs(out_dir, exist_ok=True)

    info = probe(src, ffprobe)
    plan = plan_renditions(info["width"], info["height"])
    log(f"  {info['width']}x{info['height']}, {info['duration']:.0f} seconds, "
        f"renditions: {', '.join(r['name'] for r in plan)}")

    key_hex = secrets.token_hex(16)  # AES-128 key, new for every video
    iv_hex = secrets.token_hex(16)
    _encode_hls(src, out_dir, plan, info["has_audio"], key_uri, key_hex, iv_hex, ffmpeg, preset, log)
    thumbnails = _make_thumbnails(src, out_dir, slug, info, ffmpeg, log)
    default_thumb = next(t for t in thumbnails if t["percent"] == DEFAULT_THUMBNAIL_PERCENT)

    chapters_vtt_path = None
    if chapters:
        with open(os.path.join(out_dir, "chapters.vtt"), "w", encoding="utf-8") as f:
            f.write(chapters_to_vtt(chapters, info["duration"]))
        chapters_vtt_path = f"{slug}/chapters.vtt"

    # Safety net: the key must never sit in the folder that gets uploaded
    for root, _dirs, files in os.walk(out_dir):
        for name in files:
            if name.endswith(".key") or name == "key_info.txt":
                raise PipelineError("Internal error: a key file ended up in the upload folder.")

    return {
        "slug": slug,
        "width": info["width"],
        "height": info["height"],
        "duration_seconds": int(round(info["duration"])),
        "renditions": [{k: r[k] for k in ("name", "width", "height", "video_kbps")} for r in plan],
        "hls_master_path": f"{slug}/master.m3u8",
        "thumbnail_options": thumbnails,
        "thumbnail_path": default_thumb["large"],
        "chapters_vtt_path": chapters_vtt_path,
        "key_hex": key_hex,
        "iv_hex": iv_hex,
    }
