"""
Make DRAFT chapters for Tai Chi Company videos from the master files in R2 (taichi-masters).

    python tools/draft_chapters.py --site https://gstaichi.org --email you@example.com --only eight-zhan-zhuang

The drafts are saved on the site but members do not see them: the teacher reviews them in the Studio
(Edit video > Review chapters) and presses "Publish chapters".

For each video, one at a time (so only one master file is on this computer at once):
  1. downloads the master from R2 and checks it for chapter markers already in the file (used as they are),
  2. looks at every keyframe (about one picture every 3 seconds) for title cards (words on a plain
     background, e.g. "2) HEAVEN POSTURE" or "SECTION FOUR Movements 55-78") and reads them with OCR,
  3. transcribes the narration with Whisper and finds where sections, numbered movements and technique
     names are spoken,
  4. combines these into a chapter every few minutes, named after the techniques or sections where possible,
  5. sends the draft to the site and deletes the master from this computer.

Needs Python 3.10+, ffmpeg, and: pip install faster-whisper rapidocr-onnxruntime wordninja numpy pillow
R2 is read with a Cloudflare API token (CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID, from the
environment or the project's .env file). Videos that already have chapters or a draft are skipped
unless --force is given. Everything found (OCR text, transcript, timings) is also kept in
<work>/results/<slug>.json.
"""
import argparse
import difflib
import getpass
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))

MIN_GAP = 60          # seconds: no two chapters closer than this
MAX_GAP = 6 * 60      # seconds: try to add a chapter when there is a longer stretch without one
END_MARGIN = 45       # seconds: no chapter this close to the end (credits, contact card)
INTRO_SECONDS = 90    # title cards this early are the opening titles, not a chapter
OCR_EVERY = 5         # also read every 5th keyframe (about every 15 s) for words over the picture

NUMBER_WORDS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
    "seventeen eighteen nineteen twenty".split())}
ORDINALS = {w: i + 1 for i, w in enumerate(
    "first second third fourth fifth sixth seventh eighth ninth tenth eleventh twelfth".split())}
UNITS = r"(?:section|part|posture|movement|technique|exercise|position|piece|form|stance|animal)"

# Technique names said in the narration. Extra names come from the title cards and the video title.
TECHNIQUES = """
Preparation; Commencement; Opening; Raise Hands; Grasp Bird's Tail; Grasp Sparrow's Tail; Ward Off; Roll Back;
Press; Push; Single Whip; Lift Hands; Play the Lute; Play Pipa; White Crane Spreads Its Wings; Brush Knee;
Brush Knee and Twist Step; Step Up Deflect Parry and Punch; Deflect Parry Punch; Apparent Close Up;
Withdraw and Push; Cross Hands; Embrace Tiger Return to Mountain; Carry Tiger to Mountain; Fist Under Elbow;
Repulse Monkey; Step Back and Repulse Monkey; Slanting Flying; Diagonal Flying; Needle at Sea Bottom;
Fan Through Back; Fan Through Arms; Turn and Chop with Fist; Cloud Hands; Wave Hands Like Clouds;
High Pat on Horse; Separate Right Foot; Separate Left Foot; Kick with Heel; Turn and Kick;
Strike Ears with Fists; Twin Fists Strike Ears; Snake Creeps Down; Single Whip Squatting Down;
Golden Rooster Stands on One Leg; Fair Lady Works at Shuttles; Jade Maiden Works the Shuttles;
Step Up to Seven Stars; Retreat to Ride Tiger; Step Back to Ride Tiger; Turn Body Sweep Lotus; Sweep Lotus;
Lotus Kick; Bend Bow Shoot Tiger; Shoot Tiger; Punch Down; Punch to Groin; Wild Horse Parts Mane;
Part the Wild Horse's Mane; Closing; Conclusion; Push Hands; Single Push Hands; Double Push Hands;
Peng; Lu; Ji; An; Cai; Lie; Zhou; Kao; Zhan Zhuang; Standing Post; Holding the Ball; Embrace the Tree;
Heaven Posture; Earth Posture; Wind Posture; Cloud Posture; Thunder Posture; Tiger Posture; Bird Posture;
Snake Posture; Dragon Posture; Crane Posture; Bear Posture; Monkey Posture; Deer Posture;
Two Hands Hold Up the Heavens; Drawing the Bow; Separate Heaven and Earth; Wise Owl Gazes Backwards;
Sway the Head and Shake the Tail; Two Hands Hold the Feet; Clench the Fists with Angry Eyes;
Bouncing on the Toes; Tiger Frolic; Deer Frolic; Bear Frolic; Monkey Frolic; Bird Frolic; Crane Frolic;
Buddha's Warrior Attendant Pounds Mortar; Lazily Tying Coat; Six Sealing Four Closing; Hidden Hand Punch;
Silk Reeling; Point the Star; Swallow Skims the Water; Dragonfly Touches the Water; Lion Shakes Its Head;
Tiger Embraces Head; Wind Sweeps Plum Blossoms; Yellow Bee Enters the Cave; Black Dragon Swings Its Tail
"""
STOP_LABELS = {"push", "press", "an", "ji", "lu", "peng", "cai", "lie", "zhou", "kao", "opening", "closing", "lift hands"}


def say(msg=""):
    print(msg, flush=True)


def clock(seconds):
    s = int(seconds)
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"


def letters(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def load_dotenv():
    """Reads KEY=value lines from the project's .env (only keys not already set)."""
    path = os.path.join(HERE, "..", ".env")
    if not os.path.exists(path):
        return
    for line in open(path, encoding="utf-8"):
        m = re.match(r"^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$", line)
        if m and m.group(1) not in os.environ:
            os.environ[m.group(1)] = m.group(2).strip('"').strip("'")


# ----- the site -----

def api(site, path, token=None, body=None, method=None):
    req = urllib.request.Request(site.rstrip("/") + path, method=method or ("POST" if body is not None else "GET"))
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


# ----- R2 through the Cloudflare API -----

class R2:
    def __init__(self, bucket):
        self.token, self.account = os.getenv("CLOUDFLARE_API_TOKEN"), os.getenv("CLOUDFLARE_ACCOUNT_ID")
        if not self.token or not self.account:
            raise RuntimeError("Please set CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID (a token that can read R2).")
        self.base = f"https://api.cloudflare.com/client/v4/accounts/{self.account}/r2/buckets/{bucket}/objects"

    def _open(self, url):
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {self.token}"})
        return urllib.request.urlopen(req, timeout=300)

    def list(self):
        objects, cursor = [], None
        while True:
            url = self.base + "?per_page=1000" + (f"&cursor={urllib.parse.quote(cursor)}" if cursor else "")
            with self._open(url) as resp:
                data = json.loads(resp.read().decode())
            objects += [{"key": o["key"], "size": int(o["size"])} for o in data.get("result") or []]
            cursor = (data.get("result_info") or {}).get("cursor")
            if not cursor or not (data.get("result_info") or {}).get("is_truncated"):
                return objects

    def download(self, key, path, size):
        started, done = time.time(), 0
        with self._open(f"{self.base}/{urllib.parse.quote(key)}") as resp, open(path, "wb") as f:
            while True:
                chunk = resp.read(8 * 1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                print(f"\r   downloading {done / 1e9:.2f} of {size / 1e9:.2f} GB", end="", flush=True)
        print()
        if done != size:
            raise RuntimeError(f"The download stopped early ({done} of {size} bytes).")
        return time.time() - started


# ----- looking at the picture -----

def chapter_markers(master):
    out = run(["ffprobe", "-v", "error", "-show_chapters", "-of", "json", master])
    chapters = json.loads(out.stdout or "{}").get("chapters") or []
    return [{"start": round(float(c["start_time"]), 1), "label": (c.get("tags") or {}).get("title", "").strip(),
             "source": "marker", "detail": "Chapter marker inside the video file"} for c in chapters]


def duration_of(master):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", master])
    return float(out.stdout.strip())


def keyframes(master, folder):
    """Saves every keyframe as a small picture and returns [(time, path)]."""
    os.makedirs(folder, exist_ok=True)
    out = run(["ffmpeg", "-v", "info", "-y", "-skip_frame", "nokey", "-i", master, "-an",
               "-vf", "scale=640:-2,showinfo", "-vsync", "vfr", "-q:v", "3", os.path.join(folder, "%06d.jpg")])
    times = [float(t) for t in re.findall(r"pts_time:([\d.]+)", out.stderr)]
    return [(t, os.path.join(folder, f"{i + 1:06d}.jpg")) for i, t in enumerate(times)
            if os.path.exists(os.path.join(folder, f"{i + 1:06d}.jpg"))]


def frame_stats(path):
    import numpy as np
    from PIL import Image
    gray = np.asarray(Image.open(path).convert("L").resize((160, 90)), dtype=np.float32)
    median = float(np.median(gray))
    plain = float(np.mean(np.abs(gray - median) < 18))   # share of the picture that is one flat colour
    hist = np.histogram(gray, bins=32, range=(0, 256))[0] / gray.size
    edges = float(np.mean(np.abs(np.diff(gray, axis=1)) > 40))  # text makes sharp edges
    layout = np.asarray(Image.fromarray(gray.astype("uint8")).resize((32, 18)), dtype=np.float32)
    return {"plain": plain, "median": median, "hist": hist, "edges": edges, "layout": layout}


def is_card(stats):
    """Words on a plain (usually black) background: mostly one flat colour, but not completely empty."""
    return stats["plain"] > 0.80 and 0.002 < stats["edges"] < 0.12


def picture_change(a, b):
    """0 = same, 1 = completely different. The colours alone miss a new camera angle in the same room,
    so the rough layout of the picture is compared too (someone moving changes it only a little)."""
    colours = float(abs(a["hist"] - b["hist"]).sum()) / 2
    layout = float(abs(a["layout"] - b["layout"]).mean()) / 40
    return min(1.0, max(colours, layout))


def scene_cuts(frames, stats):
    """Keyframes where the picture changes a lot more than it does around them (a new shot)."""
    import numpy as np
    change = [0.0] + [picture_change(stats[i - 1], stats[i]) for i in range(1, len(frames))]
    cuts = []
    for i in range(1, len(frames)):
        around = change[max(1, i - 5):i] + change[i + 2:i + 7]
        if change[i] > 0.55 and change[i] > 2.5 * float(np.median(around or [0])):
            cuts.append(frames[i][0])
    return cuts


def full_frame(master, t, path):
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", master, "-frames:v", "1", "-q:v", "2", path])
    return path


def exact_cut(master, after, before):
    """The time of the biggest picture change between two keyframes (when a title card starts)."""
    out = run(["ffmpeg", "-v", "info", "-ss", f"{max(0, after):.3f}", "-t", f"{before - after + 0.05:.3f}", "-i", master,
               "-an", "-vf", "scale=320:-2,select='gte(scene,0)',metadata=print:key=lavfi.scene_score", "-f", "null", "-"])
    best, best_t = 0.12, None
    for t, score in re.findall(r"pts_time:([\d.]+)\s*\n.*?lavfi\.scene_score=([\d.]+)", out.stderr):
        t, score = after + float(t), float(score)
        if score > best and after + 0.2 < t <= before + 0.05:  # skip the first frame (it has nothing to compare with)
            best, best_t = score, t
    return best_t


# ----- reading words -----

class Reader:
    """OCR. The models are loaded when first needed (after the narration, to keep memory free for Whisper)."""
    def __init__(self):
        import rapidocr_onnxruntime  # noqa: F401 (fail early if it is missing)
        import wordninja
        self.ocr, self.split = None, wordninja.split

    def lines(self, path, min_score=0.8):
        if self.ocr is None:
            from rapidocr_onnxruntime import RapidOCR
            self.ocr = RapidOCR()
        result, _ = self.ocr(path)
        lines = []
        for _box, text, score in result or []:
            text = text.strip()
            if float(score) < min_score or len(re.findall(r"[A-Za-z]", text)) < 3:
                continue  # Chinese banners on the wall, smudges
            # OCR sometimes runs words together ("PERFORMEDBY:MASTERVINCENTCHU")
            text = " ".join(self.unjoin(w) if len(w) > 12 and w.isalpha() else w
                            for w in re.split(r"(?<=[:,)])|\s+", text) if w)
            lines.append(re.sub(r"\s+", " ", text).strip())
        return lines

    def unjoin(self, word):
        # the word splitter does not know these ("TAICHI" -> "T AICHI")
        parts = re.split(f"({KNOWN_WORDS})", word, flags=re.I)
        return " ".join(p if re.fullmatch(KNOWN_WORDS, p, flags=re.I) else " ".join(self.split(p)) for p in parts if p)


KNOWN_WORDS = r"TAI|CHI|CHUAN|QIGONG|GONG|ZHAN|ZHUANG|GIN|SOON|WU|YANG|CHEN|DUAN|JIN|BA"
SMALL_WORDS = {"a", "an", "and", "at", "by", "for", "in", "of", "on", "the", "to", "with", "its", "up"}


def nice(text):
    """'2) HEAVEN POSTURE' -> '2. Heaven Posture'; 'SECTION FOUR Movements 55-78' -> 'Section Four: Movements 55–78'"""
    text = re.sub(r"\s+", " ", text).strip(" -:")
    words = text.split(" ")
    text = " ".join((w.lower() if (i and w.lower() in SMALL_WORDS) else w[:1] + w[1:].lower()) if w.isupper() and len(w) > 1
                    else w for i, w in enumerate(words))
    text = re.sub(r"^(\d+)\s*[).:\-]\s*", r"\1. ", text)
    text = re.sub(r"^((?:Section|Part)\s+\w+)\s+(?=[A-Z])", r"\1: ", text)
    text = re.sub(r"(\d)\s*-\s*(\d)", "\\1–\\2", text)
    return text[:120]


# ----- listening -----

CHUNK_SECONDS = 300  # Whisper hears the audio 5 minutes at a time, so a 2-hour video needs no more memory


def pick_model(name):
    """auto: small.en (hears names better, needs about 800 MB) when there is room, else base.en (about 500 MB).
    A Codespace stops a program that leaves it with less than about 800 MB free."""
    if name != "auto":
        return name
    try:
        free_mb = int(re.search(r"MemAvailable:\s+(\d+)", open("/proc/meminfo").read()).group(1)) // 1024
    except (OSError, AttributeError):
        return "small.en"  # Windows and Mac: assume a normal computer
    return "small.en" if free_mb >= 2500 else "base.en"


def transcribe(master, folder, model_name, prompt, duration):
    """Runs Whisper in a separate process: it needs about 1 GB, which a small computer (or Codespace) only has
    when nothing else of ours is loaded, and all of it is given back when the process ends."""
    pieces, out = [], os.path.join(folder, "words.json")
    for n, offset in enumerate(range(0, int(duration) + 1, CHUNK_SECONDS)):
        wav = os.path.join(folder, f"audio-{n:03d}.wav")
        run(["ffmpeg", "-v", "error", "-y", "-ss", str(offset), "-t", str(CHUNK_SECONDS), "-i", master,
             "-vn", "-ac", "1", "-ar", "16000", wav])
        if os.path.exists(wav) and os.path.getsize(wav) > 1000:
            pieces += [wav, str(offset)]
    done = subprocess.run([sys.executable, os.path.abspath(__file__), "--listen-only", out, model_name, prompt] + pieces)
    for wav in pieces[::2]:
        os.remove(wav)
    if done.returncode != 0 or not os.path.exists(out):
        raise RuntimeError(f"Transcribing stopped (exit code {done.returncode}). If the computer is short of memory, "
                           "close other programs or try --model base.en.")
    with open(out, encoding="utf-8") as f:
        return json.load(f)


def listen_only(out, model_name, prompt, *pieces):
    """The Whisper process. pieces: audio file, its start time in the video, audio file, start time, ..."""
    from faster_whisper import WhisperModel
    model = WhisperModel(model_name, device="cpu", compute_type="int8", cpu_threads=min(2, os.cpu_count() or 1))
    words = []
    for wav, offset in zip(pieces[::2], map(float, pieces[1::2])):
        segments, _info = model.transcribe(wav, language="en", vad_filter=True, word_timestamps=True, beam_size=1,
                                           condition_on_previous_text=False, initial_prompt=prompt[:800])
        for seg in segments:
            if seg.no_speech_prob > 0.6 or seg.avg_logprob < -1.0:
                continue  # music or noise that Whisper guessed words for
            words += [{"t": round(offset + w.start, 2), "w": w.word.strip()} for w in seg.words or []]
            print(f"\r   listening… {clock(offset + seg.end)}", end="", flush=True)
    print()
    with open(out, "w", encoding="utf-8") as f:
        json.dump(words, f)


def number_from(word):
    word = word.lower().strip(".,")
    if word.isdigit():
        return int(word)
    if re.fullmatch(r"\d+(st|nd|rd|th)", word):
        return int(word[:-2])
    return NUMBER_WORDS.get(word) or ORDINALS.get(word)


def spoken_cues(words, names):
    """Where the narration announces a section, a numbered movement, or says a technique name."""
    cues = []
    text_words = [letters(w["w"]) for w in words]

    def quote(i, n=12):
        return "“" + " ".join(w["w"] for w in words[max(0, i - 2):i + n]).strip() + "…”"

    for i, w in enumerate(text_words):
        nxt = text_words[i + 1:i + 4]
        # "section two", "posture number three", "movement 23"
        if re.fullmatch(UNITS, w) and nxt:
            k = 1 if nxt[0] == "number" else 0
            # "posture three", "section 2"; not "the position first, you…" (an ordinal comes before: "the first posture")
            n = number_from(nxt[k]) if len(nxt) > k and nxt[k] not in ORDINALS else None
            if n:
                cues.append({"t": words[i]["t"], "kind": "number", "label": f"{w.title()} {n}", "detail": quote(i)})
                continue
        # "the second posture", "the third section"
        if w in ORDINALS and nxt and re.fullmatch(UNITS, nxt[0]):
            cues.append({"t": words[i]["t"], "kind": "number", "label": f"{nxt[0].title()} {ORDINALS[w]}", "detail": quote(i)})
    # technique names, allowing for small transcription differences
    for name in names:
        target = letters(name).split()
        if not target or (len(target) == 1 and len(target[0]) < 5) or letters(name) in STOP_LABELS:
            continue
        size = len(target)
        for i in range(len(text_words) - size + 1):
            window = " ".join(text_words[i:i + size])
            if window[:1] != target[0][:1]:
                continue
            if difflib.SequenceMatcher(None, window, " ".join(target)).ratio() >= 0.86:
                cues.append({"t": words[i]["t"], "kind": "name", "label": name, "detail": quote(i)})
    return sorted(cues, key=lambda c: c["t"])


# ----- putting it together -----

def find_cards(master, frames, reader, folder):
    """Title cards, and words that stay on screen most of the time (logos, banners), which are ignored."""
    stats = [frame_stats(p) for _t, p in frames]
    cards, seen_lines, sampled = [], {}, 0
    i = 0
    while i < len(frames):
        t, path = frames[i]
        if is_card(stats[i]):
            # one card can stay up for several keyframes; read the clearest (middle) one at full size
            j = i
            while j + 1 < len(frames) and is_card(stats[j + 1]) and picture_change(stats[j], stats[j + 1]) < 0.08:
                j += 1
            mid_t = frames[(i + j) // 2][0] + 0.5
            lines = reader.lines(full_frame(master, mid_t, os.path.join(folder, "card.jpg")))
            if lines:
                cut = exact_cut(master, frames[i - 1][0], t) if i else 0.0
                cards.append({"t": round(cut if cut is not None else t, 2), "lines": lines, "until": frames[j][0]})
            i = j + 1
            continue
        if i % OCR_EVERY == 0:
            sampled += 1
            for line in reader.lines(path, min_score=0.85):
                seen_lines.setdefault(letters(line), []).append((t, line))
        i += 1
    # words over the picture that appear for a short time only (a caption), not a banner on the wall
    often = [key for key, hits in seen_lines.items() if len(hits) > max(2, 0.05 * sampled)]
    overlays = []
    for key, hits in seen_lines.items():
        if key in often or len(key.replace(" ", "")) < 8 or " " not in key:
            continue
        # a partly hidden banner ("GIN SOOM") reads differently each time: still the banner
        compact = key.replace(" ", "")
        if any(difflib.SequenceMatcher(None, compact, k.replace(" ", "")).find_longest_match(
                0, len(compact), 0, len(k.replace(" ", ""))).size >= 0.6 * len(compact) for k in often):
            continue
        overlays.append({"t": hits[0][0], "lines": [hits[0][1]]})
    return cards, overlays, stats


def same_name(a, b):
    """'1. Wu Chi' and 'Wu Chi' are the same technique."""
    strip = lambda t: re.sub(r"^\d+\s*", "", letters(t))  # noqa: E731
    return bool(a and b) and difflib.SequenceMatcher(None, strip(a), strip(b)).ratio() > 0.8


def build_chapters(duration, cards, overlays, cues, frames, stats, master, words=()):
    chapters = [{"start": 0.0, "label": "Introduction", "source": "title", "detail": ""}]
    intro_lines = [line for c in cards if c["t"] < INTRO_SECONDS for line in c["lines"]]
    chapters[0]["detail"] = ("“" + " / ".join(intro_lines) + "”") if intro_lines else "Start of the video"

    def room(t, against=None):
        return all(abs(t - c["start"]) >= MIN_GAP for c in (against if against is not None else chapters))

    def add(t, label, source, detail):
        chapters.append({"start": round(t, 1), "label": label, "source": source, "detail": detail})
        chapters.sort(key=lambda c: c["start"])

    # 1. title cards: the strongest sign that a new part starts
    for card in cards:
        if card["t"] < INTRO_SECONDS or card["t"] > duration - END_MARGIN:
            continue
        label = nice(" ".join(card["lines"]) if len(card["lines"]) <= 2 else card["lines"][0])
        if all(abs(card["t"] - c["start"]) >= 15 for c in chapters):  # cards can be close together
            add(card["t"], label, "title", "“" + " / ".join(card["lines"]) + "”")
    # 2. words over the picture and spoken announcements ("section two", "the third posture"), first time only
    announced = set()
    carded = {int(m.group(1)) for c in chapters if c["source"] == "title" for m in [re.match(r"^(\d+)\.", c["label"])] if m}
    for item in [{"t": o["t"], "label": nice(o["lines"][0]), "source": "title", "detail": "“" + o["lines"][0] + "”"}
                 for o in overlays] + [{"t": c["t"], "label": c["label"], "source": "speech", "detail": c["detail"]}
                                       for c in cues if c["kind"] == "number"]:
        number = re.search(r"(\d+)$", item["label"])
        if item["label"] in announced or (item["source"] == "speech" and number and int(number.group(1)) in carded):
            continue  # said again, or the title card for this number is already a chapter
        announced.add(item["label"])
        if INTRO_SECONDS / 2 < item["t"] < duration - END_MARGIN and room(item["t"]):
            add(item["t"], item["label"], item["source"], item["detail"])

    # 3. long stretches without a chapter: a technique name being said, else a change of scene, else an even split
    cuts = scene_cuts(frames, stats)
    names = [c for c in cues if c["kind"] == "name"]
    for _ in range(200):
        bounds = [c["start"] for c in chapters] + [duration]
        gaps = [(b - a, a, b) for a, b in zip(bounds, bounds[1:]) if b - a > MAX_GAP]
        if not gaps:
            break
        _size, a, b = max(gaps)
        mid = (a + b) / 2
        inside = lambda t: a + MIN_GAP <= t <= b - MIN_GAP and t < duration - END_MARGIN  # noqa: E731
        # a name said for the first time in this stretch, nearest the middle
        here = next((c["label"] for c in chapters if c["start"] == a), "")
        firsts, said = [], set()
        for c in names:
            if a <= c["t"] <= b and c["label"] not in said and not same_name(c["label"], here):
                said.add(c["label"])
                if inside(c["t"]):
                    firsts.append(c)
        if firsts:
            c = min(firsts, key=lambda c: abs(c["t"] - mid))
            add(c["t"], c["label"], "speech", c["detail"])
            continue
        options = [t for t in cuts if inside(t)]
        if options:
            t = min(options, key=lambda t: abs(t - mid))
            before = max([f for f, _p in frames if f < t], default=a)
            t = exact_cut(master, before, t) or t
            add(t, "", "scene", "Change of scene. No title card or narration says what this part is: watch it and name it, "
                                "or delete it.")
            continue
        add(mid, "", "even", "Nothing marks a new part here; this was added so the long stretch has a chapter. "
                             "Move it to where the next technique starts and name it, or delete it.")

    # 4. tidy up: the same name twice in a row is one chapter
    tidy = []
    for c in chapters:
        if tidy and same_name(c["label"], tidy[-1]["label"]):
            continue
        tidy.append(c)
    # 5. for a chapter with no name, what is said just after it starts helps the teacher name it
    for c in tidy:
        if not c["label"]:
            said = [w["w"] for w in words if c["start"] <= w["t"] < c["start"] + 20]
            if said:
                c["detail"] += " Heard just after: “" + " ".join(said[:25]) + "…”"
    return tidy


def analyse(master, folder, slug, title, reader, model_name, listen=True):
    timings, started = {}, time.time()
    duration = duration_of(master)
    markers = chapter_markers(master)
    if markers:
        return {"duration": duration, "chapters": markers, "markers": True, "timings": {}}

    names = [n.strip() for n in TECHNIQUES.replace("\n", " ").split(";") if n.strip()]
    words = []
    if listen:  # first, while nothing else is loaded (Whisper needs the memory)
        t0 = time.time()
        say("   listening to the narration…")
        words = transcribe(master, folder, model_name, f"{title}. Tai chi chuan instruction. " + ", ".join(names) + ".",
                           duration)
        timings["narration"] = round(time.time() - t0)

    t0 = time.time()
    frames = keyframes(master, os.path.join(folder, "frames"))
    timings["keyframes"] = round(time.time() - t0)
    say(f"   {len(frames)} keyframes; looking for title cards…")
    t0 = time.time()
    cards, overlays, stats = find_cards(master, frames, reader, folder)
    timings["title_cards"] = round(time.time() - t0)
    for c in cards:
        say(f"     {clock(c['t'])}  card: {' / '.join(c['lines'])}")

    # the names on the title cards are listened for too
    names += [re.sub(r"^\d+\.\s*", "", nice(line)) for c in cards for line in c["lines"] if len(line) < 40]
    cues = spoken_cues(words, list(dict.fromkeys(names))) if words else []
    if listen:
        say(f"   heard {len(words)} words, {len(cues)} mentions of sections or techniques")

    chapters = build_chapters(duration, cards, overlays, cues, frames, stats, master, words)
    timings["total"] = round(time.time() - started)
    shutil.rmtree(os.path.join(folder, "frames"), ignore_errors=True)
    return {"duration": duration, "chapters": chapters, "markers": False, "timings": timings,
            "cards": cards, "overlays": overlays, "cues": cues,
            "transcript": " ".join(w["w"] for w in words), "words": words}


def notes_for(result, model_name):
    if result["markers"]:
        return "These chapters were already inside the video file."
    kinds = {}
    for c in result["chapters"]:
        kinds[c["source"]] = kinds.get(c["source"], 0) + 1
    titled = kinds.get("title", 0) - 1  # not counting the Introduction
    parts = [f"{titled} chapter{'s' * (titled != 1)} from title cards"]
    parts.append(f"narration transcribed ({model_name}), {len(result['words'])} words" if result["words"]
                 else "no narration found")
    if kinds.get("scene") or kinds.get("even"):
        unnamed = kinds.get("scene", 0) + kinds.get("even", 0)
        parts.append("1 chapter has no name yet" if unnamed == 1 else f"{unnamed} chapters have no name yet")
    return "Made automatically: " + "; ".join(parts) + "."


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--listen-only":  # the Whisper process started by transcribe()
        listen_only(*sys.argv[2:])
        return
    parser = argparse.ArgumentParser(description="Make draft chapters for Tai Chi Company videos.")
    parser.add_argument("--site", default=None, help="the site address (default BACKEND_URL)")
    parser.add_argument("--email", help="your admin or teacher email for the site")
    parser.add_argument("--work", default=os.path.join(os.path.expanduser("~"), "tcc-chapters"),
                        help="folder for the downloaded master (one at a time) and the results")
    parser.add_argument("--bucket", default="taichi-masters")
    parser.add_argument("--model", default="auto",
                        help="Whisper model: small.en hears names better, base.en is 3x faster and needs less memory "
                             "(default auto: small.en if there is at least 2.5 GB of memory free)")
    parser.add_argument("--only", action="append", help="only this slug (can be given more than once)")
    parser.add_argument("--force", action="store_true", help="make a new draft even if the video has chapters or a draft")
    parser.add_argument("--no-narration", action="store_true", help="skip transcribing (title cards and scenes only)")
    parser.add_argument("--no-send", action="store_true", help="only save the results on this computer")
    parser.add_argument("--master", help="use this master file on this computer instead of downloading (with one --only)")
    args = parser.parse_args()
    args.model = pick_model(args.model)
    load_dotenv()
    site = (args.site or os.getenv("BACKEND_URL") or "").rstrip("/")

    missing = [p for p in ("ffmpeg", "ffprobe") if not shutil.which(p)]
    if missing:
        sys.exit(f"These programs were not found: {', '.join(missing)}")
    try:
        reader = Reader()
        if not args.no_narration:
            import faster_whisper  # noqa: F401
    except ImportError as e:
        sys.exit(f"Missing a Python package ({e.name}). Run: pip install faster-whisper rapidocr-onnxruntime wordninja numpy pillow")

    token, videos = None, {}
    if not args.no_send:
        if not site:
            sys.exit("Please give --site (the site address).")
        token = os.getenv("TCC_TOKEN")
        if not token:
            if not args.email:
                sys.exit("Please give --email (your admin email for the site).")
            token = api(site, "/api/login", body={"email": args.email, "password": getpass.getpass("Password: ")})["token"]
        videos = {v["slug"]: v for v in api(site, "/api/tcc/studio/videos", token)}

    r2 = R2(args.bucket)
    masters = {}
    for o in r2.list():  # newest master in each video's folder (the key ends in the upload time)
        slug = o["key"].split("/")[0]
        if "/master-" in o["key"] and (slug not in masters or o["key"] > masters[slug]["key"]):
            masters[slug] = o
    slugs = [s for s in sorted(masters) if not args.only or s in args.only]
    if args.master and len(slugs) != 1:
        sys.exit("--master needs exactly one --only slug.")
    results_dir = os.path.join(args.work, "results")
    os.makedirs(results_dir, exist_ok=True)

    done, problems = [], []
    for n, slug in enumerate(slugs, start=1):
        obj, video = masters[slug], videos.get(slug)
        say(f"\n[{n}/{len(slugs)}] {slug}  ({obj['size'] / 1e9:.2f} GB, narration with {args.model})")
        if not args.no_send:
            if video is None:
                problems.append((slug, "not found on the site"))
                say("   skipped: no video with this slug on the site")
                continue
            if not args.force and (video.get("chapters") or video.get("chapters_draft")):
                say("   skipped: already has chapters or a draft (use --force to make a new draft)")
                continue
        folder = os.path.join(args.work, slug)
        os.makedirs(folder, exist_ok=True)
        master = args.master or os.path.join(folder, "master" + os.path.splitext(obj["key"])[1])
        try:
            fetch = 0 if args.master else r2.download(obj["key"], master, obj["size"])
            result = analyse(master, folder, slug, (video or {}).get("title") or slug, reader, args.model,
                             listen=not args.no_narration)
            result["timings"]["download"] = round(fetch)
            result.update({"slug": slug, "master_key": obj["key"], "size": obj["size"], "model": args.model,
                           "notes": notes_for(result, args.model), "made_at": time.strftime("%Y-%m-%d %H:%M")})
            with open(os.path.join(results_dir, f"{slug}.json"), "w", encoding="utf-8") as f:
                json.dump(result, f, indent=1, default=float)
            say(f"   {len(result['chapters'])} draft chapters:")
            for c in result["chapters"]:
                say(f"     {clock(c['start']):>8}  {c['label'] or '(no name yet)':40s}  [{c['source']}]")
            if not args.no_send:
                api(site, f"/api/tcc/studio/videos/{video['id']}/chapters-draft", token, method="PUT",
                    body={"chapters": result["chapters"], "notes": result["notes"]})
                say("   saved as a draft on the site")
            say(f"   took {result['timings']}")
            done.append(slug)
        except Exception as e:  # keep going with the other videos
            problems.append((slug, str(e)))
            say(f"   Problem with this video: {e}")
        finally:
            shutil.rmtree(folder, ignore_errors=True)  # a downloaded master is never kept

    say(f"\nDone: {len(done)} videos.")
    for slug, why in problems:
        say(f"  {slug}: {why}")


if __name__ == "__main__":
    main()
