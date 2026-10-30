# Encoding and uploading the video library from your Windows PC

`encode_and_upload.py` turns your master video files into protected streaming files and uploads them
to Cloudflare R2. Each video is converted on **your** computer (so it can take a while), then marked
**Ready** on the site. Videos never go into this code repository or into Codespaces.

What it does for each video in `videos.csv`:

1. Makes up to three sizes (1080p, 720p, 480p). It never makes a size larger than your original,
   and phone videos filmed upright stay upright and are not stretched.
2. Cuts the video into 6-second pieces and locks every piece with a new random key (AES-128).
3. Makes 4 picture options for the video card, taken at 15%, 30%, 50% and 70% of the way through
   (not the first frame, which is often a warning screen or black). The 30% picture is used to start with.
4. Uploads everything to the `taichi-streams` bucket, in a folder named after the video's slug.
5. Sends the key to the site, which stores it encrypted. **The key is never uploaded to R2.**

It skips videos that are already Ready, so you can safely run it again after a problem.

---

## One-time setup (about 20 minutes)

### 1. Install Python, ffmpeg and rclone

Open **PowerShell** (press the Windows key, type `PowerShell`, press Enter) and run these three lines
one at a time. Answer `Y` if asked to accept terms.

```powershell
winget install --id Python.Python.3.12 -e
winget install --id Gyan.FFmpeg -e
winget install --id Rclone.Rclone -e
```

**Close PowerShell and open it again**, then check that all three work:

```powershell
python --version
ffmpeg -version
rclone version
```

Each should print a version number. If one says "not recognized", restart the computer and try again.

### 2. Get this project onto your PC

Either install Git (`winget install --id Git.Git -e`) and run
`git clone https://github.com/baguajoe/GSTAICHI.git`, or on GitHub click **Code → Download ZIP**,
and unzip it (for example to `C:\GSTAICHI`). Use the `tai-chi-company` branch.

### 3. Create an R2 API token

1. Log in to the Cloudflare dashboard: https://dash.cloudflare.com
2. Click **R2 Object Storage**, then **Manage R2 API Tokens** (right side), then **Create API token**.
3. Name it `encoding-pc`, choose **Object Read & Write**, and limit it to the buckets
   `taichi-masters` and `taichi-streams`.
4. Click **Create**. Copy the **Access Key ID**, the **Secret Access Key**, and your **Account ID**
   (shown in the endpoint `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`). The secret is shown only once.

### 4. Connect rclone to R2

In PowerShell, run this as **one line**, replacing the three values in capitals:

```powershell
rclone config create r2 s3 provider=Cloudflare access_key_id=ACCESS_KEY_ID secret_access_key=SECRET_ACCESS_KEY endpoint=https://ACCOUNT_ID.r2.cloudflarestorage.com acl=private no_check_bucket=true
```

Check it works (it should list your buckets):

```powershell
rclone lsd r2:
```

### 5. Make sure you have an admin account on the site

Sign up on the site, then on the server run `flask set-role you@example.com admin`.
The tool signs in with this email and password.

---

## Preparing the video list

Open `tools\videos.csv` in Excel or Notepad. It already lists all 21 videos:

| column | meaning |
|---|---|
| filename | the name of the master file in your videos folder, e.g. `Fundamentals Final.mov` |
| slug | the video's short name in web addresses. **Do not change** the 21 existing slugs |
| title | the title members see |
| section | `beginner`, `intermediate`, `advanced`, `qigong` or `vincents-corner` |
| tier | `1` Beginner, `2` Intermediate, `3` Advanced: the lowest plan that can watch it |

Change the **filename** column so each row matches your file. Rows whose file is missing are reported
and skipped; the others carry on. To add a new video, add a row with a new slug (lowercase letters,
numbers and dashes). If you save from Excel, choose **CSV UTF-8**.

---

## Running it

In PowerShell, go to the project folder and run (one line):

```powershell
cd C:\GSTAICHI
python tools\encode_and_upload.py --videos "D:\Tai Chi Masters" --site https://gstaichi.org --email you@example.com
```

- `--videos` is the folder holding your master files.
- `--site` is the live site address (the same as `BACKEND_URL`).
- It asks for your password. Nothing appears while you type; press Enter when done.

Useful extras:

- `--only fundamentals` to do just one video (repeat `--only` for more).
- `--force` to redo a video that is already Ready (for example after replacing the master file).
- `--preset slow` for slightly better quality at the same size (takes longer). Default is `medium`.
- `--work D:\tcc-temp` if your C: drive is short of space. It needs about twice the size of the largest video.

A 1-hour 1080p video usually takes 30 to 90 minutes to encode, depending on the computer.
You can leave it running overnight. At the end it prints a summary of what was done and any problems.

## If something goes wrong

- **"These programs were not found"**: repeat step 1 and reopen PowerShell.
- **"The site said: Invalid email or password"**: check the email and password you use on the site.
- **"The site said: You do not have permission"**: your account is not an admin yet (step 5).
- **"The upload failed"**: check your internet, then run `rclone lsd r2:`. If that fails, redo step 4.
- **"Problem with this video: ..."**: the file itself could not be read. Try opening it in a video player;
  if it plays, export it again as MP4 (H.264) from your editing program.

Just run the same command again: finished videos are skipped and it continues with the rest.

---

# Draft chapters for the videos (`draft_chapters.py`)

`draft_chapters.py` makes **draft** chapters for the videos already in R2. Members do not see a draft:
the teacher checks it in the Studio (**Edit** the video, then **Review chapters**), changes times and
names, and presses **Publish chapters**.

For each video, one at a time (only one master file is on the computer at once), it:

1. Downloads the master from `taichi-masters` and checks for chapter markers already in the file.
   If there are some, they become the draft as they are.
2. Looks at every keyframe (about one picture every 3 seconds) for title cards, words on a plain
   background such as `2) HEAVEN POSTURE` or `SECTION FOUR Movements 55-78`, and reads them with OCR.
3. Transcribes the narration with Whisper and finds where sections, numbered movements
   ("the third posture") and technique names ("Single Whip") are spoken.
4. Puts these together: a chapter at every title card, then more where a stretch is longer than
   5 minutes (a technique name being said, otherwise a change of scene, otherwise half way). Chapters
   that nothing names are left without a name for the teacher to fill in or delete.
5. Saves the draft on the site and deletes the master from the computer. What it found (OCR text,
   transcript, timings) stays in `<work>/results/<slug>.json`.

Setup, once: `pip install faster-whisper rapidocr-onnxruntime wordninja numpy pillow` (ffmpeg as above).
It reads R2 with a Cloudflare API token that can read R2: set `CLOUDFLARE_API_TOKEN` and
`CLOUDFLARE_ACCOUNT_ID` (or put them in the project's `.env`).

```
python tools/draft_chapters.py --site https://gstaichi.org --email you@example.com --only eight-zhan-zhuang
python tools/draft_chapters.py --site https://gstaichi.org --email you@example.com
```

- Videos that already have chapters or a draft are skipped; `--force` makes a new draft anyway.
- `--model base.en` transcribes about 3 times faster than the default `small.en`, but gets more
  technique names wrong. `--no-narration` skips transcribing.
- `--work D:\tcc-chapters` chooses where the master is downloaded (it needs room for the largest video, 4 GB).
