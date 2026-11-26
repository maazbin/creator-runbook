"""Rebuild two original twelve-second commissions in a private directory."""

import argparse
from array import array
from functools import lru_cache
import json
import math
import os
from pathlib import Path
import random
import subprocess
import sys
import wave

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "skills/creator-runbook/scripts"))
import channels


@lru_cache
def face(size, family="sans"):
    faces = {
        "sans": ["DejaVuSans.ttf", "arial.ttf"],
        "bold": ["DejaVuSans-Bold.ttf", "arialbd.ttf"],
        "serif": ["DejaVuSerif.ttf", "georgia.ttf"],
        "mono": ["DejaVuSansMono.ttf", "consola.ttf"],
    }
    for name in faces[family]:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def dot(draw, x, y, radius, fill):
    draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=fill)


def motion_frame(t):
    ink, paper, orange, blue = "#20282D", "#F2EEE5", "#B53716", "#2057A1"
    im = Image.new("RGB", (1280, 720), paper)
    d = ImageDraw.Draw(im)
    d.text((70, 53), "MOTION NOTES", fill=ink, font=face(23, "bold"))
    d.text((1210, 56), "TIMING STUDY", fill=ink, font=face(20, "mono"), anchor="rt")
    d.line((70, 99, 1210, 99), fill=ink, width=2)
    title = (
        "Which arrives first?"
        if t < 4
        else "Watch the lower dot." if t < 8 else "A tie. Exactly two seconds."
    )
    d.text((68, 128), title, fill=ink, font=face(69, "serif"))
    p = min(1, max(0, (t - 4) / 2))
    origin, end = 260, 1150
    for index, (label, value, color) in enumerate(
        [("LINEAR", p, blue), ("EASE", p * p * (3 - 2 * p), orange)]
    ):
        y = 340 + index * 141
        d.text((73, y - 12), label, fill=color, font=face(23, "mono"))
        d.line((origin, y, end, y), fill="#B2ACA0", width=2)
        for n in range(11):
            x = origin + (end - origin) * n / 10
            d.line((x, y + 16, x, y + 21 + (n % 5 == 0) * 5), fill="#ACA69A", width=2)
        x = origin + (end - origin) * value
        if value:
            d.line((origin, y, x, y), fill=color, width=4)
        dot(d, x, y, 18, color)
        dot(d, x - 4, y - 5, 4, paper)
    d.line((70, 578, 1210, 578), fill="#B2ACA0", width=2)
    caption = (
        "Same distance. Make your prediction."
        if t < 4
        else (
            "One moves steadily. One changes pace."
            if t < 8
            else "Easing changes the journey. The clock stays the same."
        )
    )
    d.text((70, 607), caption, fill=ink, font=face(27))
    d.text((1209, 607), f"{2*p:.2f} s", fill=blue, font=face(27, "mono"), anchor="rt")
    return im


@lru_cache
def night_sky():
    width, height = 720, 1280
    im = Image.new("RGB", (width, height))
    d = ImageDraw.Draw(im)
    for y in range(height):
        k = min(1, y / 800)
        d.line((0, y, width, y), fill=(int(14 + 35 * k), int(22 + 45 * k), int(46 + 37 * k)))
    rng = random.Random(18)
    for _ in range(118):
        x, y = rng.randrange(720), rng.randrange(35, 695)
        c = rng.randrange(100, 192)
        dot(d, x, y, rng.choice([1, 1, 1, 2]), (c, c, c + 15))
    for base, amp, fill, phase in [
        (694, 49, "#344B61", 0),
        (721, 39, "#293E51", 1),
        (747, 31, "#213549", 2),
    ]:
        ridge = [
            (x, base + amp * (0.47 * math.sin(x / 76 + phase) + 0.53 * math.sin(x / 155 - phase)))
            for x in range(-1, 736, 8)
        ]
        d.polygon(ridge + [(736, 820), (-1, 820)], fill=fill)
    d.rectangle((0, 770, width, height), fill="#152937")
    return im


def night_frame(t):
    im = night_sky().copy()
    d = ImageDraw.Draw(im, "RGBA")
    # Ripples have fixed positions and advancing phase, preserving the horizon.
    for i in range(78):
        y = 775 + (i * 37) % 485
        x = (i * 113 + 6 * math.sin(t * 0.72 + i)) % 720
        d.line((x, y, x + 12 + (y - 770) * 0.11, y), fill=(111, 147, 156, 70), width=1 + (y > 910))
    d.polygon([(0, 761), (68, 737), (131, 743), (176, 753), (218, 775), (0, 795)], fill="#101D28")
    d.polygon([(71, 739), (78, 624), (99, 624), (109, 743)], fill="#D2C7A5")
    d.rectangle((75, 609, 102, 626), fill="#334053")
    d.polygon([(70, 610), (88, 594), (106, 610)], fill="#162535")
    glow = 0.65 + 0.35 * math.sin(t * 2.4)
    d.polygon(
        [(89, 617), (485, 569 + 12 * math.sin(t)), (530, 614 + 12 * math.sin(t))],
        fill=(255, 218, 136, int(22 * glow)),
    )
    dot(d, 89, 617, 9, (255, 213, 132, 210))
    dot(d, 89, 617, 4, "#FFF4CF")
    p = max(0, min(1, (t - 4) / 6.6))
    boat_x = 675 - 462 * (p * p * (3 - 2 * p))
    boat_y = 775 + 5 * math.sin(t * 1.5)
    if t >= 4:
        d.polygon(
            [
                (boat_x - 26, boat_y),
                (boat_x + 24, boat_y),
                (boat_x + 15, boat_y + 8),
                (boat_x - 16, boat_y + 8),
            ],
            fill="#0A141E",
        )
        d.line((boat_x, boat_y, boat_x, boat_y - 26), fill="#C5B99A", width=2)
        b = 0.5 + 0.5 * math.sin(t * 4)
        dot(d, boat_x, boat_y - 23, 4 + b * 2, "#FFE2A3")
        for j in range(6):
            y = boat_y + 12 + j * 7
            d.line(
                (boat_x - 5 + j * 0.4, y, boat_x + 5 + j * 0.5, y),
                fill=(239, 198, 119, int(80 - 9 * j)),
            )
    d.text((66, 122), "LAST LIGHT", fill="#DBBC82", font=face(23, "mono"))
    lines = (
        ("One light", "stayed on.")
        if t < 4
        else ("Far offshore,", "a blink.") if t < 8 else ("Tonight, someone", "answered.")
    )
    for i, line in enumerate(lines):
        d.text((61, 191 + i * 73), line, fill="#F1E8D7", font=face(58, "serif"))
    return im


def score(path, night):
    sr = 24000
    cue_notes = (
        [(0, 196), (2.8, 246.94), (4.1, 392), (6.8, 293.66), (8.05, 246.94), (9.15, 392)]
        if night
        else [
            (0.25, 330),
            (0.55, 440),
            (3.82, 294),
            (4, 440),
            (4.5, 440),
            (5, 440),
            (5.5, 440),
            (6, 659.25),
            (8, 523.25),
        ]
    )
    samples = array("h")
    for i in range(sr * 12):
        t = i / sr
        v = 0.012 * math.sin(2 * math.pi * 97.998 * t) * (0.5 + 0.5 * math.sin(t)) if night else 0
        for start, hz in cue_notes:
            u = t - start
            if 0 <= u < 2.2:
                env = min(1, u / 0.018) * math.exp(-u * (2.2 if night else 5.3))
                v += (
                    0.17
                    * env
                    * (math.sin(2 * math.pi * hz * u) + 0.25 * math.sin(2 * math.pi * hz * 2 * u))
                )
        samples.append(round(32767 * v * min(1, t / 0.1, (12 - t) / 0.5)))
    if sys.byteorder != "little":
        samples.byteswap()
    with wave.open(str(path), "wb") as f:
        f.setparams((1, 2, sr, 0, "NONE", "not compressed"))
        f.writeframes(samples.tobytes())


def produce(root, ff, name):
    cfg = json.loads((HERE / name / "profile.json").read_text(encoding="utf-8"))
    draft = json.loads((HERE / name / "episode.json").read_text(encoding="utf-8"))
    db = channels.connect(root)
    try:
        channels.configure(db, cfg)
        job = channels.claim(db, name, "first-cut")
        if "token" not in job:
            if job["status"] == "ready":
                return job["path"]
            raise ValueError(f"Demo request is {job['status']}; choose a fresh demo directory")
        night = name == "last-light"
        artwork = night_frame if night else motion_frame
        folder = root / "assets" / name
        folder.mkdir(parents=True, exist_ok=True)
        score(folder / "score.wav", night)
        cmd = [
            ff,
            "-loglevel",
            "error",
            "-y",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            "720x1280" if night else "1280x720",
            "-r",
            "24",
            "-i",
            "pipe:0",
            "-i",
            str(folder / "score.wav"),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            str(folder / "original.mp4"),
        ]
        with subprocess.Popen(cmd, stdin=subprocess.PIPE) as enc:
            try:
                for frame in range(12 * 24):
                    enc.stdin.write(artwork(frame / 24).tobytes())
            finally:
                enc.stdin.close()
            if enc.wait():
                raise RuntimeError("Original animation encode failed")
        return channels.deliver(db, root, job["job"], job["token"], draft, ff)
    finally:
        db.close()


def narrate_experiment(root, ff):
    name = "motion-notes"
    cfg = json.loads((HERE / name / "profile.json").read_text(encoding="utf-8"))
    draft = json.loads((HERE / name / "episode.json").read_text(encoding="utf-8"))
    cfg["delivery"] = "voiced"
    lines = (
        "Which dot reaches the line first?",
        "Watch the lower dot catch up.",
        "Two seconds. They arrive together.",
    )
    for scene, line in zip(draft["scenes"], lines):
        scene["voice"] = line
        scene["sound"] = "A single narrator, with a hold for the picture."
        scene.pop("audio")
        scene.pop("caption")
    db = channels.connect(root)
    try:
        channels.configure(db, cfg)
        job = channels.claim(db, name, "narrated-cut")
        if "token" not in job:
            if job["status"] == "ready":
                return job["path"]
            raise ValueError("Narrated example already in progress")
        return channels.deliver(db, root, job["job"], job["token"], draft, ff)
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--ffmpeg", default=os.getenv("CREATOR_FFMPEG", "ffmpeg"))
    parser.add_argument(
        "--narrated",
        action="store_true",
        help="Also render the experiment through CREATOR_TTS_COMMAND",
    )
    args = parser.parse_args()
    for channel in ("motion-notes", "last-light"):
        print(produce(args.directory.resolve(), args.ffmpeg, channel))

    if args.narrated:
        print(narrate_experiment(args.directory.resolve(), args.ffmpeg))
