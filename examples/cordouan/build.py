"""Build the Cordouan masters from the stills and the consistency document.

Picture is reconstructed. Every word is set with a font. Joins are the ones
named in consistency.md. Run from this directory after FFmpeg is on PATH,
or set CREATOR_FFMPEG.
"""

import math
import struct
import subprocess
import wave
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
STILLS = HERE / "stills"
OUT = HERE / "masters"
FPS_LONG, FPS_SHORT = 24, 30
LONG_S, SHORT_S = 60.0, 20.0
GROUND = (12, 14, 18)
IVORY = (243, 237, 226)
QUIET = (196, 180, 154)
SOURCE = (154, 145, 134)
FLAME = (231, 161, 90)

FFMPEG = Path(
    __import__("os").environ.get(
        "CREATOR_FFMPEG",
        r"C:\Users\pc\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.1-full_build\bin\ffmpeg.exe",
    )
)


def face(path, size, index=0):
    return ImageFont.truetype(str(path), size, index=index)


FONTS = {
    "en-title": face(r"C:\Windows\Fonts\constan.ttf", 64),
    "en-title-s": face(r"C:\Windows\Fonts\constan.ttf", 52),
    "en-end": face(r"C:\Windows\Fonts\constan.ttf", 72),
    "en-end-s": face(r"C:\Windows\Fonts\constan.ttf", 46),
    "en-line": face(r"C:\Windows\Fonts\constan.ttf", 32),
    "en-line-s": face(r"C:\Windows\Fonts\constan.ttf", 28),
    "en-kick": face(r"C:\Windows\Fonts\bahnschrift.ttf", 22),
    "en-kick-s": face(r"C:\Windows\Fonts\bahnschrift.ttf", 20),
    "en-mark": face(r"C:\Windows\Fonts\bahnschrift.ttf", 16),
    "en-src": face(r"C:\Windows\Fonts\bahnschrift.ttf", 18),
    "zh-title": face(r"C:\Windows\Fonts\simsun.ttc", 60),
    "zh-title-s": face(r"C:\Windows\Fonts\simsun.ttc", 48),
    "zh-end": face(r"C:\Windows\Fonts\simsun.ttc", 64),
    "zh-end-s": face(r"C:\Windows\Fonts\simsun.ttc", 42),
    "zh-line": face(r"C:\Windows\Fonts\simsun.ttc", 32),
    "zh-line-s": face(r"C:\Windows\Fonts\simsun.ttc", 30),
    "zh-kick": face(r"C:\Windows\Fonts\msyhl.ttc", 26),
    "zh-kick-s": face(r"C:\Windows\Fonts\msyhl.ttc", 24),
    "zh-mark": face(r"C:\Windows\Fonts\msyhl.ttc", 20),
    "zh-src": face(r"C:\Windows\Fonts\msyhl.ttc", 20),
}


def ease(p):
    p = max(0.0, min(1.0, p))
    return p * p * (3 - 2 * p)


def cover(im, size, fx, fy, zoom):
    tw, th = size
    sw, sh = im.size
    scale = max(tw / sw, th / sh) * zoom
    cw, ch = tw / scale, th / scale
    left = min(max(fx * sw - cw / 2, 0), sw - cw)
    top = min(max(fy * sh - ch / 2, 0), sh - ch)
    return im.resize(size, Image.Resampling.LANCZOS, box=(left, top, left + cw, top + ch))


def load_stills():
    glass = Image.open(STILLS / "glass.jpg").convert("RGB")
    glass = glass.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return {
        "flame": Image.open(STILLS / "flame.jpg").convert("RGB"),
        "glass": glass,
        "beam": Image.open(STILLS / "beam.jpg").convert("RGB"),
        "coast": Image.open(STILLS / "coast.jpg").convert("RGB"),
    }


STILLS_IMG = None


def plate(name, local, dur, size, kind):
    zoom = 1.0 + 0.04 * ease(local / dur)
    if kind == "short":
        focus = {
            "flame": (0.40, 0.48, 1.35),
            "glass": (0.62, 0.50, 1.45),
            "coast": (0.60, 0.42, 1.22),
        }
        fx, fy, z0 = focus[name]
        return cover(STILLS_IMG[name], size, fx, fy, z0 * zoom)
    focus = {"flame": (0.38, 0.52), "glass": (0.62, 0.50), "beam": (0.58, 0.46), "coast": (0.70, 0.40)}
    fx, fy = focus[name]
    return cover(STILLS_IMG[name], size, fx, fy, zoom)


def schematic(size, p):
    """A principle, not a measured section: a solid lens, then the curve as separate prisms."""
    w, h = size
    im = Image.new("RGB", size, GROUND)
    draw = ImageDraw.Draw(im)
    cy = h * 0.54
    hh = h * 0.18

    def column(cx, left_edge, right_edge):
        for dy in (-hh * 0.62, 0, hh * 0.62):
            y = cy + dy
            draw.line((cx - w * 0.12, y, left_edge, y), fill=IVORY, width=2)
            draw.line((right_edge, y, cx + w * 0.13, cy + dy * 0.28), fill=IVORY, width=2)
        r = max(5, int(w / 220))
        fx = cx - w * 0.145
        draw.ellipse((fx - r, cy - r, fx + r, cy + r), fill=FLAME)

    left = w * 0.32
    hw = w * 0.04
    draw.ellipse((left - hw, cy - hh, left + hw, cy + hh), outline=IVORY, width=2)
    column(left, left - hw, left + hw)

    right = w * 0.68
    tooth = w * 0.05
    slots = (-hh * 0.62, 0, hh * 0.62)
    shown = max(1, int(round(ease(min(1.0, p * 1.2)) * len(slots))))
    order = (1, 0, 2)
    for rank, i in enumerate(order):
        if rank >= shown:
            continue
        y = cy + slots[i]
        half = hh * 0.18
        draw.line([(right, y - half), (right + tooth, y), (right, y + half)], fill=IVORY, width=2)
    column(right, right, right + tooth)
    return im


def picture(t, size, kind):
    w, h = size
    blank = Image.new("RGB", size, GROUND)
    if kind == "long":
        if t < 1:
            return blank
        if t < 9:
            return plate("flame", t - 1, 8, size, kind)
        if t < 16.5:
            return plate("glass", t - 9, 7.5, size, kind)
        if t < 17:
            a = ease((t - 16.5) / 0.5)
            g = plate("glass", 7.5, 7.5, size, kind)
            b = plate("beam", 0, 10, size, kind)
            return Image.blend(g, b, a)
        if t < 27:
            return plate("beam", t - 17, 10, size, kind)
        if t < 35:
            return schematic(size, (t - 27) / 8)
        if t < 47:
            return plate("coast", t - 35, 12, size, kind)
        if t < 47.5:
            a = ease((t - 47) / 0.5)
            return Image.blend(plate("coast", 12, 12, size, kind), blank, a)
        return blank
    if t < 6:
        return plate("flame", t, 6, size, kind)
    if t < 12:
        return plate("glass", t - 6, 6, size, kind)
    if t < 16.5:
        return plate("coast", t - 12, 4.5, size, kind)
    if t < 17:
        a = ease((t - 16.5) / 0.5)
        return Image.blend(plate("coast", 4.5, 4.5, size, kind), blank, a)
    return blank


def fade(t, a, b, inn=0.35, out=0.45):
    if t < a or t >= b:
        return 0.0
    alpha = 1.0
    if t < a + inn:
        alpha = ease((t - a) / inn)
    if t > b - out:
        alpha = min(alpha, ease((b - t) / out))
    return alpha


def tracked(draw, text, x, y, font, fill, gap, center=False):
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + gap * max(0, len(text) - 1)
    if center:
        x -= total / 2
    for ch, width in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=fill)
        x += width + gap
    return total


def draw_block(base, lines, alpha, shadow=False):
    if alpha <= 0:
        return base
    over = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(over)
    shade = None
    if shadow:
        shade = Image.new("RGBA", base.size, (0, 0, 0, 0))
        ink = ImageDraw.Draw(shade)
    for text, font, fill, x, y, gap, center in lines:
        if shade is not None:
            tracked(ink, text, x, y + 1, font, (0, 0, 0, 200), gap, center)
        tracked(draw, text, x, y, font, fill, gap, center)
    if shade is not None:
        from PIL import ImageFilter

        shade = shade.filter(ImageFilter.GaussianBlur(10))
        base = Image.alpha_composite(base.convert("RGBA"), shade).convert("RGB")
    if alpha < 0.999:
        over.putalpha(over.getchannel("A").point(lambda p, a=alpha: int(p * a)))
    return Image.alpha_composite(base.convert("RGBA"), over).convert("RGB")


COPY = {
    "en": {
        "date": "25 JULY 1823",
        "date_title": "25 July 1823",
        "curve": "The curve stays.",
        "thick": "The thickness goes.",
        "mark": "RECONSTRUCTION",
        "schematic": "SCHEMATIC",
        "place": "CORDOUAN",
        "end": "A lens, not a thicker one.",
        "line": "The first lighthouse Fresnel lens was lit that night.",
        "src": "RECONSTRUCTION  ·  GIRONDE ESTUARY",
        "solid": "SOLID",
        "rings": "RINGS",
    },
    "zh": {
        "date": "1823年7月25日",
        "date_title": "1823年7月25日",
        "curve": "曲线留下。",
        "thick": "厚度省去。",
        "mark": "复原",
        "schematic": "示意",
        "place": "科尔杜昂",
        "end": "透镜，而不是更厚的一块。",
        "line": "当晚，灯塔上的第一块菲涅尔透镜在此点亮。",
        "src": "复原画面  ·  吉伦特河口",
        "solid": "整块",
        "rings": "环",
    },
}


def legend(im, lang, kind):
    """Labels under the two drawings. Code-set, not painted by the image model."""
    if kind != "long":
        return im
    w, h = im.size
    text = COPY[lang]
    font = FONTS["en-kick" if lang == "en" else "zh-kick"]
    gap = 4 if lang == "en" else 1
    over = Image.new("RGBA", im.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(over)
    y = int(h * 0.76)
    tracked(draw, text["solid"], int(w * 0.30), y, font, QUIET, gap, True)
    tracked(draw, text["rings"], int(w * 0.70), y, font, QUIET, gap, True)
    return Image.alpha_composite(im.convert("RGBA"), over).convert("RGB")


def compose(base, t, lang, kind):
    c = COPY[lang]
    w, h = base.size
    en = lang == "en"
    if kind == "long" and 27 <= t < 35:
        base = legend(base, lang, kind)
    frame = base

    def put(alpha, specs):
        nonlocal frame
        if alpha > 0:
            frame = draw_block(frame, specs, alpha, shadow=(kind == "short"))

    if kind == "long":
        kick = FONTS["en-kick" if en else "zh-kick"]
        title = FONTS["en-title" if en else "zh-title"]
        mark = FONTS["en-mark" if en else "zh-mark"]
        x = int(w * 0.075)
        put(fade(t, 1.4, 5.2), [(c["mark"], mark, QUIET, x, int(h * 0.10), 3, False)])
        put(fade(t, 2.0, 7.4), [(c["date"], kick, QUIET, x, int(h * 0.74), 5 if en else 1, False)])
        put(fade(t, 10.0, 15.6), [(c["curve"], title, IVORY, x, int(h * 0.74), 0, False)])
        put(fade(t, 18.2, 25.4), [(c["thick"], title, IVORY, x, int(h * 0.74), 0, False)])
        put(
            fade(t, 27.4, 34.4),
            [(c["schematic"], kick, QUIET, x, int(h * 0.16), 5 if en else 1, False)],
        )
        put(fade(t, 48.3, 59.2, 0.6, 0.7), end_lines(c, lang, w, h, "long"))
        return frame
    title = FONTS["en-title-s" if en else "zh-title-s"]
    y = int(h * 0.72)
    put(
        fade(t, 0.1, 5.4, 0.25, 0.35),
        [(c["date_title"], title, IVORY, w // 2, y, 1 if en else 0, True)],
    )
    put(fade(t, 6.3, 11.4), [(c["curve"], title, IVORY, w // 2, y, 0, True)])
    put(fade(t, 12.2, 16.1), [(c["thick"], title, IVORY, int(w * 0.36), int(h * 0.58), 0, True)])
    put(fade(t, 17.15, 19.7, 0.3, 0.35), end_lines(c, lang, w, h, "short"))
    return frame


def end_lines(c, lang, w, h, kind):
    en = lang == "en"
    if kind == "long":
        kick = FONTS["en-kick" if en else "zh-kick"]
        title = FONTS["en-end" if en else "zh-end"]
        line = FONTS["en-line" if en else "zh-line"]
        src = FONTS["en-src" if en else "zh-src"]
        cy = int(h * 0.40)
        return [
            (c["place"], kick, QUIET, w // 2, cy, 6 if en else 2, True),
            (c["end"], title, IVORY, w // 2, cy + 54, 0, True),
            (c["line"], line, QUIET, w // 2, cy + 150, 0, True),
            (c["src"], src, SOURCE, w // 2, cy + 214, 3 if en else 1, True),
        ]
    kick = FONTS["en-kick-s" if en else "zh-kick-s"]
    title = FONTS["en-end-s" if en else "zh-end-s"]
    line = FONTS["en-line-s" if en else "zh-line-s"]
    src = FONTS["en-src" if en else "zh-src"]
    cy = int(h * 0.40)
    return [
        (c["place"], kick, QUIET, w // 2, cy, 4 if en else 1, True),
        (c["end"], title, IVORY, w // 2, cy + 48, 0, True),
        (c["line"], line, QUIET, w // 2, cy + 120, 0, True),
        (c["src"], src, SOURCE, w // 2, cy + 180, 2 if en else 1, True),
    ]


def _mix(base, lines, alpha):
    typed = draw_block(base, lines, 1)
    if alpha >= 0.999:
        return typed
    return Image.blend(base, typed, alpha)


def tone(path, seconds, rate=48000):
    n = int(seconds * rate)
    buf = bytearray()
    for i in range(n):
        t = i / rate
        env = 1.0
        if t < 1.4:
            env = ease(t / 1.4)
        if t > seconds - 4.0:
            env *= ease((seconds - t) / 4.0)
        drone = 0.07 * math.sin(2 * math.pi * 65.41 * t)
        drone += 0.028 * math.sin(2 * math.pi * 98.0 * t)
        drone += 0.012 * math.sin(2 * math.pi * 130.81 * t + 0.4)
        drone *= 0.82 + 0.18 * math.sin(2 * math.pi * t / 18.0)
        noise = (((i * 1103515245 + 12345) & 0x7FFFFFFF) / 0x7FFFFFFF - 0.5) * 0.01
        sample = max(-1.0, min(1.0, (drone + noise) * env))
        v = int(sample * 28000)
        buf += struct.pack("<hh", v, v)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(buf)


def encode(path, size, fps, audio, frames):
    w, h = size
    cmd = [
        str(FFMPEG),
        "-y",
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
        "-i",
        str(audio),
        "-c:v",
        "libx264",
        "-profile:v",
        "high",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        "17",
        "-preset",
        "medium",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-ar",
        "48000",
        "-ac",
        "2",
        "-movflags",
        "+faststart",
        "-shortest",
        str(path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for frame in frames:
            proc.stdin.write(frame.tobytes())
    finally:
        proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError(f"ffmpeg failed for {path}")


def srt_time(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02}:{(ms // 60000) % 60:02}:{(ms // 1000) % 60:02},{ms % 1000:03}"


def write_srt(path, cues):
    blocks = []
    for i, (a, b, text) in enumerate(cues, 1):
        blocks.append(f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{text}")
    path.write_text("\n\n".join(blocks) + "\n", encoding="utf-8")


def captions():
    write_srt(
        OUT / "long-en.srt",
        [
            (0.0, 1.4, "[Low tone]"),
            (1.4, 5.2, "Reconstruction"),
            (2.0, 7.4, "25 July 1823"),
            (10.0, 15.6, "The curve stays."),
            (16.5, 17.0, "[The beam continues]"),
            (18.2, 25.4, "The thickness goes."),
            (27.4, 34.4, "Schematic. A solid lens, then the same curve as rings."),
            (48.3, 59.2, "Cordouan. A lens, not a thicker one. The first lighthouse Fresnel lens was lit that night. Reconstruction. Gironde estuary."),
        ],
    )
    write_srt(
        OUT / "long-zh.srt",
        [
            (0.0, 1.4, "[低音]"),
            (1.4, 5.2, "复原"),
            (2.0, 7.4, "1823年7月25日"),
            (10.0, 15.6, "曲线留下。"),
            (16.5, 17.0, "[光束延续]"),
            (18.2, 25.4, "厚度省去。"),
            (27.4, 34.4, "示意。整块透镜，然后同一条曲线分成环。"),
            (48.3, 59.2, "科尔杜昂。透镜，而不是更厚的一块。当晚，灯塔上的第一块菲涅尔透镜在此点亮。复原画面。吉伦特河口。"),
        ],
    )
    write_srt(
        OUT / "short-en.srt",
        [
            (0.0, 0.4, "[Low tone]"),
            (0.1, 5.4, "25 July 1823"),
            (6.3, 11.4, "The curve stays."),
            (12.2, 16.1, "The thickness goes."),
            (17.15, 19.7, "Cordouan. A lens, not a thicker one. Reconstruction."),
        ],
    )
    write_srt(
        OUT / "short-zh.srt",
        [
            (0.0, 0.4, "[低音]"),
            (0.1, 5.4, "1823年7月25日"),
            (6.3, 11.4, "曲线留下。"),
            (12.2, 16.1, "厚度省去。"),
            (17.15, 19.7, "科尔杜昂。透镜，而不是更厚的一块。复原画面。"),
        ],
    )


def render_pair(kind, size, fps, seconds):
    n = int(round(seconds * fps))
    audio = OUT / f"{kind}-tone.wav"
    tone(audio, seconds)
    encoders = {}
    for lang in ("en", "zh"):
        path = OUT / f"{kind}-{lang}.mp4"
        w, h = size
        cmd = [
            str(FFMPEG), "-y", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(fps),
            "-i", "pipe:0", "-i", str(audio),
            "-c:v", "libx264", "-profile:v", "high", "-pix_fmt", "yuv420p",
            "-crf", "17", "-preset", "medium",
            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
            "-movflags", "+faststart", "-shortest", str(path),
        ]
        encoders[lang] = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    covers = {}
    try:
        for i in range(n):
            t = i / fps
            base = picture(t, size, kind)
            for lang, proc in encoders.items():
                frame = compose(base, t, lang, kind)
                proc.stdin.write(frame.tobytes())
                if kind == "long" and lang == "en" and abs(t - 40.0) < 0.5 / fps:
                    covers["16x9"] = frame
                if kind == "short" and lang == "en" and abs(t - 3.0) < 0.5 / fps:
                    covers["9x16"] = frame
                if kind == "long" and lang == "zh" and abs(t - 54.0) < 0.5 / fps:
                    covers["end-zh"] = frame
                if kind == "long" and lang == "en" and abs(t - 54.0) < 0.5 / fps:
                    covers["end-en"] = frame
    finally:
        for proc in encoders.values():
            proc.stdin.close()
        for lang, proc in encoders.items():
            if proc.wait() != 0:
                raise RuntimeError(f"ffmpeg failed for {kind}-{lang}")
    return covers


def cover_3x4(coast):
    im = cover(coast, (1080, 1440), 0.72, 0.40, 1.35)
    return im


def preview():
    global STILLS_IMG
    STILLS_IMG = load_stills()
    dest = HERE / "previews"
    dest.mkdir(exist_ok=True)
    samples = {
        "long": (1920, 1080, [3.0, 12.0, 22.0, 31.0, 40.0, 54.0]),
        "short": (1080, 1920, [0.8, 8.0, 14.0, 18.4]),
    }
    for kind, (w, h, times) in samples.items():
        for t in times:
            base = picture(t, (w, h), kind)
            for lang in ("en", "zh"):
                compose(base, t, lang, kind).save(dest / f"{kind}-{lang}-{t:.1f}.jpg", quality=90)
    print(dest)


def main():
    global STILLS_IMG
    if "--preview" in __import__("sys").argv:
        preview()
        return
    if not FFMPEG.is_file():
        raise SystemExit(f"FFmpeg not found: {FFMPEG}")
    OUT.mkdir(parents=True, exist_ok=True)
    STILLS_IMG = load_stills()
    print("long")
    covers = render_pair("long", (1920, 1080), FPS_LONG, LONG_S)
    print("short")
    covers.update(render_pair("short", (1080, 1920), FPS_SHORT, SHORT_S))
    if "16x9" in covers:
        covers["16x9"].save(OUT / "cover-16x9.jpg", quality=92)
    if "9x16" in covers:
        covers["9x16"].save(OUT / "cover-9x16.jpg", quality=92)
    if "end-en" in covers:
        covers["end-en"].save(OUT / "cover-end-en.jpg", quality=92)
    cover_3x4(STILLS_IMG["coast"]).save(OUT / "cover-3x4.jpg", quality=92)
    captions()
    print("done", OUT)


if __name__ == "__main__":
    main()
