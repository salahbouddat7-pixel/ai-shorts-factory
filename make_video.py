
import asyncio
import json
import math
import os
import re
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path("output")
OUT.mkdir(exist_ok=True)

with open(OUT / "script.json", encoding="utf-8") as f:
    script = json.load(f)

narration = script["narration"].strip()
title = script["title"].strip()

def run(command):
    subprocess.run(command, check=True)

def duration(path):
    result = subprocess.check_output([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path)
    ])
    return float(result.decode().strip())

async def make_voice():
    import edge_tts

    voice = edge_tts.Communicate(
        narration,
        "en-US-AriaNeural",
        rate="+0%"
    )
    await voice.save(str(OUT / "voice.mp3"))

try:
    asyncio.run(make_voice())
    audio = OUT / "voice.mp3"
    print("Online neural narration generated")
except Exception as error:
    print("Online voice unavailable:", str(error)[:200])
    audio = OUT / "voice.wav"
    run([
        "espeak-ng", "-v", "en-us",
        "-s", "145",
        "-w", str(audio),
        narration
    ])
    print("Offline narration fallback generated")

audio_duration = duration(audio)

# Split narration into readable caption scenes.
words = narration.split()
scene_count = min(7, max(4, math.ceil(len(words) / 13)))
scene_count = min(scene_count, len(words))
scenes = []

for i in range(scene_count):
    start = round(i * len(words) / scene_count)
    end = round((i + 1) * len(words) / scene_count)
    scenes.append(" ".join(words[start:end]))

W, H = 720, 1280

font_path = (
    "/usr/share/fonts/truetype/dejavu/"
    "DejaVuSans-Bold.ttf"
)
font = ImageFont.truetype(font_path, 48)
small_font = ImageFont.truetype(font_path, 28)

def wrap_text(draw, text, font, max_width):
    lines = []
    current = ""

    for word in text.split():
        candidate = (current + " " + word).strip()
        box = draw.textbbox((0, 0), candidate, font=font)

        if box[2] - box[0] > max_width and current:
            lines.append(current)
            current = word
        else:
            current = candidate

    if current:
        lines.append(current)

    return lines

def create_scene(index, caption):
    img = Image.new("RGB", (W, H))
    pixels = img.load()

    # Dark ocean gradient.
    for y in range(H):
        depth = y / H
        for x in range(W):
            wave = math.sin(x / 85 + y / 110 + index)
            pixels[x, y] = (
                int(5 + 5 * wave),
                int(38 - 20 * depth + 5 * wave),
                int(78 - 38 * depth + 8 * wave)
            )

    draw = ImageDraw.Draw(img)

    # Decorative ocean rings.
    for ring in range(5):
        radius = 110 + ring * 90
        cx = W // 2
        cy = 430
        draw.ellipse(
            (cx-radius, cy-radius, cx+radius, cy+radius),
            outline=(25, 90, 125),
            width=3
        )

    draw.text(
        (55, 95),
        "DEEP OCEAN",
        font=small_font,
        fill=(90, 220, 235)
    )

    lines = wrap_text(draw, caption, font, W - 110)
    line_height = 67
    total_height = len(lines) * line_height
    y = (H - total_height) // 2

    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        width = bbox[2] - bbox[0]
        draw.text(
            ((W - width) / 2, y),
            line,
            font=font,
            fill="white",
            stroke_width=2,
            stroke_fill=(0, 10, 30)
        )
        y += line_height

    draw.text(
        (55, H - 110),
        f"FACTS  /  {index+1:02d}",
        font=small_font,
        fill=(90, 220, 235)
    )

    path = OUT / f"scene_{index:02d}.png"
    img.save(path)
    return path

segments = []
fps = 24

# Distribute video time across scenes.
# Add a small buffer so the last words aren't cut off.
total_duration = audio_duration + 0.5
frames_per_scene = math.ceil(total_duration * fps / scene_count)

for i, caption in enumerate(scenes):
    image = create_scene(i, caption)
    segment = OUT / f"segment_{i:02d}.mp4"

    run([
        "ffmpeg", "-y",
        "-loop", "1",
        "-framerate", str(fps),
        "-i", str(image),
        "-vf",
        (
            "zoompan="
            "z='min(zoom+0.0006,1.12)':"
            "d=1:"
            "s=720x1280:"
            "fps=24,"
            "format=yuv420p"
        ),
        "-frames:v", str(frames_per_scene),
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "25",
        "-an",
        str(segment)
    ])
    segments.append(segment)

concat_file = OUT / "segments.txt"
with open(concat_file, "w", encoding="utf-8") as f:
    for segment in segments:
        f.write(f"file '{segment.name}'\n")

silent_video = OUT / "silent.mp4"

run([
    "ffmpeg", "-y",
    "-f", "concat",
    "-safe", "0",
    "-i", str(concat_file),
    "-c", "copy",
    str(silent_video)
])

final_video = OUT / "final_short.mp4"

run([
    "ffmpeg", "-y",
    "-i", str(silent_video),
    "-i", str(audio),
    "-map", "0:v:0",
    "-map", "1:a:0",
    "-c:v", "copy",
    "-c:a", "aac",
    "-b:a", "128k",
    "-t", str(audio_duration),
    "-movflags", "+faststart",
    str(final_video)
])

print("Video created:", final_video)
print("Title:", title)
print("Duration:", round(audio_duration, 1), "seconds")
