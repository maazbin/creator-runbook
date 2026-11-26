"""Original animated short. Run with Python, Pillow and FFmpeg on PATH."""

import argparse
from array import array
from functools import lru_cache
import math
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import wave

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skills/creator-runbook/scripts"))
from motion import camera, ease, flight, progress, track
from fold import surface

SIZE = (1080, 1920)
FPS = 30
SECONDS = 15
INK = "#182632"
TRAIN = "#284e56"
CREAM = "#fff1c7"


@lru_cache
def font(size, mono=False):
    for filename in (
        ("DejaVuSansMono.ttf", "consola.ttf") if mono else ("DejaVuSans-Bold.ttf", "arialbd.ttf")
    ):
        try:
            return ImageFont.truetype(filename, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


class Canvas:
    """Author in a 720-unit composition, rasterize geometry at the master resolution."""

    def __init__(self, image):
        self.draw = ImageDraw.Draw(image)

    def __getattr__(self, name):
        fn = getattr(self.draw, name)

        def scaled(points, *args, **kw):
            def coord(pt):
                return tuple(v * 1.5 for v in pt) if isinstance(pt, (list, tuple)) else pt * 1.5

            pts = [coord(pt) for pt in points]
            for key in ("width", "radius"):
                if key in kw:
                    kw[key] = round(kw[key] * 1.5)
            if "font" in kw:
                kw["font"] = kw["font"].font_variant(size=round(kw["font"].size * 1.5))
            return fn(pts, *args, **kw)

        return scaled


@lru_cache
def sky():
    im = Image.new("RGB", (720, 1280))
    d = ImageDraw.Draw(im)
    stops = [
        (0, (51, 75, 91)),
        (300, (131, 137, 144)),
        (620, (234, 165, 137)),
        (800, (255, 197, 142)),
        (1279, (92, 101, 98)),
    ]
    for (a, c), (b, e) in zip(stops, stops[1:]):
        for y in range(a, b + 1):
            u = (y - a) / (b - a)
            d.line((0, y, 720, y), fill=tuple(round(v + (w - v) * u) for v, w in zip(c, e)))
    rng = random.Random(301)
    # Dry-brush cloud banks and fine, static printed grain.
    for _ in range(160):
        x = rng.randrange(-60, 720)
        y = rng.choice([305, 425, 520]) + rng.randrange(-22, 23)
        d.line(
            (x, y, x + rng.randrange(18, 112), y),
            fill=im.getpixel((0, max(0, y - 12))),
            width=rng.randint(1, 3),
        )
    d.ellipse((451, 342, 568, 459), fill="#ffe4b3")
    for y in [427, 437, 448]:
        d.line((445, y, 577, y), fill="#d6a795", width=2)
    return im.resize(SIZE, Image.Resampling.BICUBIC)


@lru_cache
def grain():
    rng = random.Random(704)
    return Image.frombytes("L", SIZE, rng.randbytes(SIZE[0] * SIZE[1])).convert("RGB")


@lru_cache
def city(layer):
    rng = random.Random(47 + layer)
    buildings = []
    x = -120
    while x < 1240:
        width = rng.randint(26, 79) if layer else rng.randint(14, 42)
        top = rng.randint(528, 666) if layer else rng.randint(438, 597)
        rim = rng.randint(3, 14)
        windows = [
            (a, b)
            for a in range(7, width - 4, 10)
            for b in range(10, 105, 17)
            if rng.random() < 0.36
        ]
        buildings.append((x, width, top, rim, windows))
        x += width + rng.randint(1, 7)
    return buildings


def skyline(d, pan):
    for layer, color in enumerate(["#aa8e91", "#767b83"]):
        shift = pan * (0.055 if layer == 0 else 0.14)
        for x, w, top, rim, windows in city(layer):
            x -= shift
            if x > 730 or x + w < 0:
                continue
            d.rectangle((x, top, x + w, 727), fill=color)
            d.rectangle((x + w * 0.27, top - rim, x + w * 0.68, top), fill=color)
            if w > 43:
                d.line((x + w * 0.57, top - rim, x + w * 0.57, top - 32), fill=color, width=2)
            for a, b in windows:
                d.rectangle(
                    (x + a, top + b, x + a + 3, top + b + 4),
                    fill="#c1a29a" if not layer else "#939197",
                )


def railings(d, pan):
    for i in range(-2, 9):
        x = i * 194 - pan * 0.32
        d.line((x, 708, x, 585), fill="#53616a", width=4)
        d.line((x - 4, 584, x + 4, 584), fill="#45515e", width=3)
    for y in (614, 621):
        d.line((0, y, 720, y), fill="#636a70", width=2)


def car(d, x, shut, last):
    if x > 740 or x + 704 < -20:
        return
    y = 694
    d.rounded_rectangle((x + 6, y + 20, x + 700, 957), radius=22, fill=INK)
    d.rounded_rectangle((x, y + 7, x + 697, 921), radius=19, fill=TRAIN, outline="#1c343e", width=3)
    d.polygon([(x + 8, y + 10), (x + 32, y), (x + 667, y), (x + 690, y + 10)], fill="#90a3a0")
    d.line((x + 18, y + 15, x + 682, y + 15), fill="#d0c2a4", width=3)
    d.rectangle((x + 1, 843, x + 695, 888), fill="#d5b997")
    d.rectangle((x + 1, 885, x + 695, 895), fill="#c05d40")
    d.line((x + 6, 911, x + 691, 911), fill="#162e37", width=4)
    for n in (45, 136, 366, 457, 548, 624):
        w = 57 if n != 624 else 42
        d.rounded_rectangle((x + n, 744, x + n + w, 817), radius=7, fill="#182e36")
        d.rounded_rectangle((x + n + 4, 748, x + n + w - 4, 813), radius=4, fill="#e3b67c")
        d.polygon(
            [(x + n + 6, 808), (x + n + w - 8, 756), (x + n + w - 7, 777), (x + n + 25, 812)],
            fill="#edcb96",
        )
        cx = x + n + w * 0.59
        d.ellipse((cx - 6, 778, cx + 6, 792), fill="#5d5d57")
        d.polygon([(cx - 11, 811), (cx - 8, 793), (cx + 6, 791), (cx + 16, 811)], fill="#565752")
        d.line((x + n + 3, 759, x + n + w - 3, 759), fill="#927f65", width=2)
    left = x + 220
    d.rectangle((left, 737, left + 120, 918), fill="#f5cd8c")
    for i in (15, 102):
        d.line((left + i, 741, left + i, 908), fill="#a8805d", width=3)
    for side in (0, 1):
        amount = 12 + 48 * shut
        a, b = (left, left + amount) if side == 0 else (left + 120 - amount, left + 120)
        d.rectangle((a, 735, b, 916), fill="#547476", outline="#253e47", width=2)
        if amount > 22:
            d.rounded_rectangle((a + 5, 749, b - 5, 807), radius=4, fill="#d1a67a")
            d.line((a + 3, 866, b - 3, 866), fill="#edcd9f", width=3)
    d.rounded_rectangle((left + 13, 709, left + 106, 730), radius=3, fill="#202d2e")
    d.text((left + 59, 720), "NIGHT LINE", font=font(12, True), fill="#f4cf85", anchor="mm")
    d.text((x + 43, 860), "N  /  07", font=font(17, True), fill="#435050")
    if last:
        d.ellipse((x + 9, 830, x + 18, 842), fill="#ff805a")
    for cx in (x + 91, x + 605):
        d.ellipse((cx - 21, 922, cx + 21, 964), fill="#252d35")
        d.ellipse((cx - 9, 934, cx + 9, 952), fill="#697177")


def paths(t):
    move = 46 * max(0, t - 6.0) ** 1.62
    pan = max(0, move - 660) * 0.90
    roof = move - 519 - pan
    if t < 4.75:
        x, y, a = flight(
            [(-130, 574), (110, 539), (254, 691), (301, 802)], ease(progress(t, 0, 4.75))
        )
        scale = 0.90
    elif t < 7.5:
        u = progress(t, 4.75, 7.5)
        x, y, a = flight([(301, 802), (280, 806), (228, 844), (196, 868)], ease(u))
        a = track(t, [(4.75, 66), (5.15, 14), (6.1, -7), (7.5, 24)])
        scale = 0.9
    elif t < 11.55:
        landing = paths(11.55)[:2]
        x, y, a = flight(
            [(196, 868), (150, 1005), (15, 438), landing], ease(progress(t, 7.5, 11.55))
        )
        # Level out the wing for contact with the train roof.
        u = progress(t, 10.7, 11.55)
        a = a * (1 - ease(u)) - 6 * ease(u)
        scale = 0.9
    else:
        x, y, a = roof, 678, -6
        scale = 0.90
    return x, y, a, scale, move, pan


def frame(t):
    im = sky().copy()
    d = Canvas(im)
    x, y, angle, scale, move, pan = paths(t)
    skyline(d, pan)
    railings(d, pan)
    # A flock crosses above the roof on a different vector from the commuter train.
    for j in range(5):
        bx = 190 + 35 * j + 11 * t - pan * 0.10
        by = 374 + 17 * math.sin(j * 2.4) - t * 1.3
        wing = 2 + 3 * math.sin(t * 4.1 + j)
        d.line([(bx - 8, by - wing), (bx, by), (bx + 8, by - wing)], fill="#6b727a", width=2)
    # Overhead catenary sags between fixed supports.
    for i in range(-2, 8):
        px = i * 487 - pan * 0.47
        d.line((px, 660, px, 271), fill="#54636b", width=5)
        d.line((px - 31, 309, px + 72, 283), fill="#465663", width=3)
        d.line(
            [(px + z * 487 / 16, 285 + 32 * math.sin(math.pi * z / 16)) for z in range(17)],
            fill="#495965",
            width=2,
        )
    d.rectangle((0, 929, 720, 1030), fill="#3c4447")
    for start in range(-1, 3):
        car(d, 72 + start * 720 + move - pan, ease(progress(t, 4.07, 4.74)), start == -1)
    # Three depths of platform movement carry the tracking shot.
    d.polygon([(0, 961), (720, 945), (720, 1280), (0, 1280)], fill="#475459")
    d.polygon([(0, 963), (720, 947), (720, 964), (0, 983)], fill="#e5ac77")
    for i in range(-8, 32):
        px = i * 64 - (pan * 1.05) % 64
        d.line((px, 971 - px * 0.022, px + 28, 970 - px * 0.022), fill="#594b45", width=3)
    for i in range(-1, 10):
        px = (i * 162 - pan * 1.08) % 1460 - 360
        d.line((px, 992, px - 60, 1280), fill="#394950", width=2)
    d.line((0, 1128, 720, 1110), fill="#626966", width=2)
    if 7.35 < t < 10.7:
        for j in range(3):
            u = progress(t, 7.35, 10.7)
            xx = x - 18 - j * 18
            d.arc(
                (xx - 85, y - 13 + j * 9, xx + 22, y + 32 + j * 9),
                70,
                160 + int(32 * math.sin(math.pi * u)),
                fill="#b8cac2",
                width=2,
            )
    # Open-door spill disappears at contact. Shallow puddles catch the sunset.
    width = 61 * (1 - ease(progress(t, 4.07, 4.74)))
    if width > 1:
        dx = 352 + move - pan
        d.polygon(
            [
                (dx - width, 965),
                (dx + width, 962),
                (dx + width + 48, 1037),
                (dx - width - 44, 1044),
            ],
            fill="#a59880",
        )
    for row in range(33):
        yy = 1007 + row * 7
        xx = ((row * 229 - pan * (1.02 + 0.002 * row)) % 1070) - 180
        length = 15 + (19 * row) % 84
        d.line(
            (xx, yy, xx + length, yy - 1),
            fill="#667271" if row % 3 else "#9a9383",
            width=1 + (row % 4 == 0),
        )
    for k in range(-2, 6):
        px = k * 660 + 60 - pan * 1.38
        if -110 < px < 740:
            d.line((px, 1125, px + 10, 1071), fill="#253540", width=5)
            d.line((px + 82, 1123, px + 72, 1070), fill="#253540", width=5)
            d.rounded_rectangle(
                (px - 4, 1062, px + 92, 1072), radius=2, fill="#b09075", outline="#443e3d"
            )
            for n in (0, 11):
                d.line((px, 1027 + n, px + 84, 1027 + n), fill="#967864", width=6)
            for n in (9, 73):
                d.line((px + n, 1023, px + n, 1062), fill="#38454a", width=3)
    bank = track(
        t,
        [(0, 18), (3.75, -12), (4.75, 5), (7.5, 12), (8.7, -49), (10.7, 32), (11.55, 5), (12.4, 0)],
    )
    roof_shadow = (695, max(0, 695 - y), "#486064") if t >= 11.0 else None
    surface(d, (x, y), scale * 1.51, angle, bank, roof_shadow)
    # Signal green-to-amber and near post pass at a larger parallax factor.
    px = 637 - pan * 1.34
    if -65 < px < 760:
        d.rectangle((px, 598, px + 9, 1000), fill="#31434c")
        d.rounded_rectangle((px - 17, 572, px + 27, 651), radius=14, fill="#243841")
        d.ellipse((px - 5, 585, px + 15, 605), fill="#efa75d" if t > 4 else "#426068")
        d.ellipse((px - 5, 615, px + 15, 635), fill="#98c0a0" if t <= 4 else "#43545a")
    # A motivated push on the shut doors. Recover geography before the ascent.
    if t < 3.75:
        zoom = track(t, [(0, 1.01), (3.75, 1.10)])
        centre = (354, 680)
    elif t < 6.35:
        zoom = track(t, [(3.75, 1.86), (4.65, 2.10), (6.35, 2.13)])
        centre = (330, 790)
    elif t < 10.60:
        zoom = track(t, [(6.35, 1.51), (7.8, 1.65), (10.60, 1.28)])
        centre = (max(252, x + 53), y - 90)
    else:
        zoom = track(t, [(10.6, 1.52), (11.55, 1.60), (13, 1.77), (15, 1.77)])
        centre = (max(252, x + 64), 636)
    im = camera(im, SIZE, (1.5 * centre[0], 1.5 * centre[1]), zoom)
    return Image.blend(im, grain(), 0.033)


def soundtrack(path):
    sr = 24000
    samples = array("h")
    rng = random.Random(7)
    air = 0.0
    for n in range(SECONDS * sr):
        t = n / sr
        air = 0.95 * air + 0.05 * rng.uniform(-1, 1)
        r = progress(t, 5.7, 11)
        v = 0.065 * air + 0.011 * math.sin(2 * math.pi * 73 * t)
        v += 0.047 * r * math.sin(2 * math.pi * (39 * t + 1.2 * max(0, t - 6) ** 2))
        v += 0.058 * r * math.exp(-19 * ((t * 2.3) % 1)) * math.sin(2 * math.pi * 73 * t)
        for start, freq, l, amp in [
            (1.1, 622, 1.2, 0.17),
            (1.62, 466, 1.3, 0.13),
            (4.69, 107, 0.22, 0.38),
            (4.78, 170, 0.12, 0.16),
            (11.58, 932, 0.9, 0.08),
            (12, 466, 2, 0.12),
        ]:
            u = t - start
            if 0 <= u < l:
                v += (
                    amp
                    * min(1, u / 0.008)
                    * math.exp(-4 * u / l)
                    * math.sin(2 * math.pi * freq * u)
                )
        v += air * 0.63 * math.exp(-(((t - 8.35) / 1.1) ** 2))
        samples.append(round(32767 * v * min(1, t / 0.3, (SECONDS - t) / 0.7)))
    if sys.byteorder != "little":
        samples.byteswap()
    with wave.open(str(path), "wb") as out:
        out.setparams((1, 2, sr, 0, "NONE", "not compressed"))
        out.writeframes(samples.tobytes())


def render(target, ff):
    with tempfile.TemporaryDirectory() as temp:
        audio = Path(temp) / "score.wav"
        soundtrack(audio)
        cmd = [
            ff,
            "-loglevel",
            "error",
            "-y",
            "-f",
            "rawvideo",
            "-s",
            "1080x1920",
            "-pix_fmt",
            "rgb24",
            "-framerate",
            str(FPS),
            "-i",
            "pipe:0",
            "-i",
            str(audio),
            "-c:v",
            "libx264",
            "-crf",
            "18",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-movflags",
            "+faststart",
            str(target),
        ]
        with subprocess.Popen(cmd, stdin=subprocess.PIPE) as p:
            try:
                for i in range(SECONDS * FPS):
                    p.stdin.write(frame(i / FPS).tobytes())
            finally:
                p.stdin.close()
            if p.wait():
                raise RuntimeError("Movie encoding failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--ffmpeg", default=os.environ.get("CREATOR_FFMPEG", "ffmpeg"))
    args = parser.parse_args()
    render(args.output, args.ffmpeg)
