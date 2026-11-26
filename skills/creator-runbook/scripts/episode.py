"""Render a channel episode from a text model's data-only response."""

from functools import lru_cache
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import wave

import cut
import speech

SIZES = {"portrait": (720, 1280), "landscape": (1280, 720), "square": (900, 900)}
LAYOUTS = {"statement", "compare", "steps", "media"}


def master_settings(cfg):
    """Resolve a labelled aspect and optional exact delivery raster and frame rate."""
    aspect = cfg.get("format", "portrait")
    if aspect not in SIZES:
        raise ValueError("Unknown delivery format")
    size = cfg.get("size", list(SIZES[aspect]))
    if (
        not isinstance(size, list)
        or len(size) != 2
        or any(type(n) is not int or n < 2 or n % 2 for n in size)
    ):
        raise ValueError("size must be two positive even pixel dimensions")
    w, h = size
    if (
        (aspect == "portrait" and w >= h)
        or (aspect == "landscape" and w <= h)
        or (aspect == "square" and w != h)
    ):
        raise ValueError("size must match the declared format")
    fps = cfg.get("fps", 24)
    if type(fps) is not int or not 1 <= fps <= 120:
        raise ValueError("fps must be an integer between 1 and 120")
    return size, fps


def validate(draft, cfg):
    if not isinstance(draft, dict):
        raise ValueError("Episode must be a JSON object")
    for key in ("title", "angle", "post"):
        cut.required_text(draft, key, "episode")
    if draft.get("channel") != cfg["id"] or draft.get("platform") != cfg["platform"]:
        raise ValueError("Episode channel or platform does not match the assignment")
    if draft.get("language") != cfg["language"]:
        raise ValueError("Episode language label must match the assignment")
    scenes = draft.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise ValueError("Episode needs scenes")
    plan = film_plan(draft, cfg)
    duration = cut.validate(plan)
    goal = cfg.get("seconds", 45)
    if abs(duration - goal) > max(1, goal * 0.15):
        raise ValueError(f"Total picture budget {duration:g}s is outside the {goal:g}s commission")
    for s in scenes:
        if "caption" in s and not isinstance(s["caption"], str):
            raise ValueError("caption must be text")
        layout = s.get("layout")
        if layout not in LAYOUTS:
            raise ValueError(f"{s['id']}: choose a supported layout")
        cut.required_text(s, "heading", s["id"])
        cut.required_text(s, "line", s["id"])
        points = s.get("points", [])
        if not isinstance(points, list) or any(
            not isinstance(x, str) or not x.strip() for x in points
        ):
            raise ValueError("points must be a list of short labels")
        if layout == "compare" and len(points) != 2:
            raise ValueError("A compare shot needs exactly two labels")
        if layout == "steps" and not 2 <= len(points) <= 3:
            raise ValueError("A steps shot needs two or three labels")
        if layout == "media" and not s.get("file"):
            raise ValueError("Media scenes need a channel asset")
        if layout != "media" and s.get("file"):
            raise ValueError("Use the media layout for a supplied picture")
        if (
            cfg.get("delivery", "captioned") == "voiced"
            and not s["voice"].strip()
            and not s.get("audio")
        ):
            raise ValueError(
                "Voiced channels need narration or an explicitly supplied sound source for every scene"
            )


def film_plan(draft, cfg):
    # Only documented fields cross into the rendering engine.
    scenes = []
    for s in draft["scenes"]:
        if not isinstance(s, dict):
            raise ValueError("Scenes must be objects")
        selected = {
            k: s[k]
            for k in (
                "id",
                "seconds",
                "basis",
                "evidence",
                "voice",
                "picture",
                "change",
                "sound",
                "in",
                "presenter_in",
                "audio_in",
                "screen_label",
                "spoken_qualification",
            )
            if k in s
        }
        scenes.append(selected)
    size, fps = master_settings(cfg)
    return {
        "title": draft["title"],
        "fps": fps,
        "size": size,
        "sources": cfg.get("sources", {}),
        "scenes": scenes,
    }


def asset(root, name):
    if not isinstance(name, str) or Path(name).is_absolute():
        raise ValueError("Select a relative file from this channel's assets")
    p = (root / name).resolve()
    if not p.is_relative_to(root.resolve()) or not p.is_file():
        raise ValueError(f"Missing or out-of-channel asset: {name}")
    return str(p)


SERIF = [
    r"C:\Windows\Fonts\NotoSerif-Regular.ttf",
    r"C:\Windows\Fonts\georgia.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "NotoSerif-Regular.ttf",
    "Georgia.ttf",
    "DejaVuSerif.ttf",
    "DejaVuSans.ttf",
    "arial.ttf",
]
SERIF_BOLD = [
    r"C:\Windows\Fonts\NotoSerif-Bold.ttf",
    r"C:\Windows\Fonts\georgiab.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    "NotoSerif-Bold.ttf",
    "georgiab.ttf",
    "DejaVuSerif-Bold.ttf",
    "DejaVuSans-Bold.ttf",
    "arialbd.ttf",
]


@lru_cache(maxsize=256)
def font(size, bold, custom):
    from PIL import ImageFont

    if custom:
        return ImageFont.truetype(custom, size)
    for item in SERIF_BOLD if bold else SERIF:
        try:
            return ImageFont.truetype(item, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def tracked(draw, text, x, y, face, fill, gap):
    for ch in text:
        draw.text((x, y), ch, font=face, fill=fill)
        x += draw.textlength(ch, font=face) + gap
    return x


def lines_for(draw, text, face, width):
    tokens = text.split()
    result = []
    current = ""
    for token in tokens:
        candidate = (current + " " + token).strip()
        if draw.textlength(candidate, font=face) <= width:
            current = candidate
            continue
        if current:
            result.append(current)
        current = ""
        for char in token:
            if current and draw.textlength(current + char, font=face) > width:
                result.append(current)
                current = ""
            current += char
    if current:
        result.append(current)
    return result


def fit(draw, text, box, size, color, custom, bold=False):
    x, y, width, height = box
    for n in range(size, 15, -2):
        f = font(n, bold, custom)
        lines = lines_for(draw, text, f, width)
        step = int(n * 1.27)
        if len(lines) * step <= height:
            for i, line in enumerate(lines):
                draw.text((x, y + i * step), line, font=f, fill=color, anchor="lt")
            return
    raise ValueError(f"Shorten on-screen text to fit the frame: {text[:48]}")


def make_cards(stage, cfg, s, idx, ff):
    from PIL import Image, ImageDraw

    (w, h), fps = master_settings(cfg)
    accent = cfg.get("accent", "#C3E690")
    custom = cfg.get("font") or ""
    mx = int(w * 0.09)
    usable = w - mx * 2
    points = s.get("points", []) if s["layout"] in ("compare", "steps") else []

    def plate(shown):
        im = Image.new("RGB", (w, h), "#100E0C")
        d = ImageDraw.Draw(im)
        kicker_size = max(16, min(28, w // 46))
        kicker = font(kicker_size, False, custom)
        tracked(d, cfg["name"].upper(), mx, int(h * 0.14), kicker, accent, max(2, kicker_size // 7))
        rule_y = int(h * 0.14) + kicker_size + int(h * 0.025)
        d.line((mx, rule_y, mx + int(w * 0.08), rule_y), fill=accent, width=1)
        fit(
            d,
            s["heading"],
            (mx, int(h * 0.28), usable, int(h * (0.22 if points else 0.28))),
            min(68, w // 14),
            "#F3EDE2",
            custom,
            True,
        )
        if points:
            top = int(h * 0.54)
            step = int(h * 0.09)
            for i, label in enumerate(points[:shown]):
                y = top + i * step
                num = font(max(16, min(28, w // 42)), False, custom)
                d.text((mx, y), f"{i + 1:02d}", font=num, fill=accent)
                fit(
                    d,
                    label,
                    (mx + int(w * 0.07), y, usable - int(w * 0.08), int(step * 0.8)),
                    min(32, w // 28),
                    "#F3EDE2",
                    custom,
                )
        fit(
            d,
            s["line"],
            (mx, int(h * 0.78), int(usable * 0.86), int(h * 0.12)),
            min(28, w // 32),
            "#C4B49A",
            custom,
        )
        return im

    total = round(s["seconds"] * fps)
    # Cache static states. The reveal is timed in frames, then holds for reading.
    states = [plate(i).tobytes() for i in range(len(points) + 1)]
    target = stage / f"card-{idx}.mp4"
    args = [
        ff,
        "-nostdin",
        "-loglevel",
        "error",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{w}x{h}",
        "-r",
        str(fps),
        "-i",
        "pipe:0",
        "-an",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "18",
        "-pix_fmt",
        "yuv420p",
        str(target),
    ]
    with subprocess.Popen(args, stdin=subprocess.PIPE) as enc:
        try:
            for k in range(total):
                visible = min(len(points), int(k * (len(points) + 1) / max(1, total * 0.65)) + 1)
                enc.stdin.write(states[visible])
        finally:
            enc.stdin.close()
        if enc.wait():
            raise ValueError("Could not encode card sequence")
    return str(target)


def synthesize(path, text, cfg, seconds, ff):
    raw = os.environ.get("CREATOR_TTS_COMMAND")
    if raw:
        cmd = json.loads(raw)
        if not isinstance(cmd, list) or not cmd or not all(isinstance(x, str) for x in cmd):
            raise ValueError("CREATOR_TTS_COMMAND must be a JSON argv array")
        args = [
            x.replace("{wav}", str(path)).replace("{voice}", str(cfg.get("voice_model", "")))
            for x in cmd
        ]
        speech.run(args, text)
    else:
        speech.record(path, text, cfg.get("voice_model", ""), ff)
    with wave.open(str(path), "rb") as w:
        params = w.getparams()
        frames = w.readframes(params.nframes)
    required = round(seconds * params.framerate)
    if params.nframes > required:
        raise ValueError(
            f"Narration takes {params.nframes/params.framerate:.2f}s, longer than {seconds:g}s; shorten the line or rebudget the shot"
        )
    silence = bytes([128 if params.sampwidth == 1 else 0]) * params.sampwidth * params.nchannels
    with wave.open(str(path), "wb") as out:
        out.setparams(params)
        out.writeframes(frames + silence * (required - params.nframes))
    return params.nframes / params.framerate


def stamp(seconds):
    ms = round(seconds * 1000)
    return f"{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}"


def build(stage, asset_root, cfg, draft, executable):
    ff = shutil.which(executable)
    if not ff:
        raise ValueError("Host is missing FFmpeg. Configure CREATOR_FFMPEG")
    plan = film_plan(draft, cfg)
    captions = []
    elapsed = 0
    with tempfile.TemporaryDirectory(dir=stage) as tmp:
        work = Path(tmp)
        for i, (s, shot) in enumerate(zip(draft["scenes"], plan["scenes"])):
            seconds = s["seconds"]
            speech_len = seconds
            shot["file"] = (
                asset(asset_root, s["file"])
                if s["layout"] == "media"
                else make_cards(work, cfg, s, i, ff)
            )
            if s.get("presenter"):
                shot["presenter"] = asset(asset_root, s["presenter"])
            audio = s.get("audio")
            if audio in ("@picture", "@presenter"):
                shot["audio"] = audio
            elif audio:
                shot["audio"] = asset(asset_root, audio)
            elif cfg.get("delivery", "captioned") == "voiced":
                path = work / f"voice-{i}.wav"
                speech_len = synthesize(path, s["voice"], cfg, seconds, ff)
                shot["audio"] = str(path)
            text = s.get("caption", s["voice"] if shot.get("audio") else s["line"])
            if text:
                captions.append(
                    f"{len(captions)+1}\n{stamp(elapsed)} --> {stamp(elapsed+speech_len)}\n{text}"
                )
            elapsed += seconds
        cut.validate(plan)
        cut.render(ff, plan, work, stage / "video.mp4")
    (stage / "captions.srt").write_text("\n\n".join(captions) + "\n", encoding="utf-8")
    (stage / "post.txt").write_text(draft["post"].strip() + "\n", encoding="utf-8")
    (stage / "episode.json").write_text(
        json.dumps(draft, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (stage / "channel.json").write_text(
        json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (stage / "script.txt").write_text(
        "\n\n".join(s["voice"] for s in draft["scenes"] if s["voice"]) + "\n", encoding="utf-8"
    )
