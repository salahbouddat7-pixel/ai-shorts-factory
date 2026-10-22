import asyncio, json, math, random, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance

OUT = Path('output'); OUT.mkdir(exist_ok=True)
script = json.loads((OUT/'script.json').read_text(encoding='utf-8'))
text = script['narration'].strip()
source = Path('assets/monkey.png')
if not source.exists(): raise FileNotFoundError('Upload monkey.png to assets/monkey.png')

def run(args): subprocess.run(args, check=True)
def duration(path):
    return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=noprint_wrappers=1:nokey=1',str(path)]).decode().strip())

async def speak():
    import edge_tts
    await edge_tts.Communicate(text,'en-US-GuyNeural',rate='+15%').save(str(OUT/'voice.mp3'))
try:
    asyncio.run(speak()); voice=OUT/'voice.mp3'
except Exception as exc:
    print('Neural TTS unavailable; offline fallback:', str(exc)[:150])
    voice=OUT/'voice.wav'
    run(['espeak-ng','-v','en-us','-s','165','-w',str(voice),text])

D = duration(voice)
W,H=720,1280
font='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
large=ImageFont.truetype(font,48)
small=ImageFont.truetype(font,30)
base=Image.open(source).convert('RGB')
words=text.split()
count=max(4,min(9,math.ceil(len(words)/8)))
chunks=[' '.join(words[round(i*len(words)/count):round((i+1)*len(words)/count)]) for i in range(count)]

def wrap(draw, caption):
    lines=[]; current=''
    for word in caption.split():
        test=(current+' '+word).strip()
        if draw.textbbox((0,0),test,font=large)[2]>W-100 and current:
            lines.append(current); current=word
        else: current=test
    if current: lines.append(current)
    return lines

# Build a sequence of close-ups and wide shots with different expressions from the same reference photo.
# This is 2D editing, not genuine facial or body motion transfer.
clips=[]
fps=24
frames=math.ceil(D*fps/count)
for i,caption in enumerate(chunks):
    image=base.copy()
    bw,bh=image.size
    target_ratio=W/H
    crop_w=min(bw, int(bh*target_ratio))
    crop_h=int(crop_w/target_ratio)
    # Alternating face close-ups and full-body views
    zoom=[1.0,1.32,1.15,1.45][i%4]
    crop_w=int(crop_w/zoom); crop_h=int(crop_h/zoom)
    cx=bw*(0.50 if i%4==0 else 0.50)
    cy=bh*([0.50,0.31,0.43,0.26][i%4])
    x=max(0,min(bw-crop_w,int(cx-crop_w/2)))
    y=max(0,min(bh-crop_h,int(cy-crop_h/2)))
    image=image.crop((x,y,x+crop_w,y+crop_h)).resize((W,H),Image.Resampling.LANCZOS)
    if i%3==2: image=ImageEnhance.Contrast(image).enhance(1.18)
    draw=ImageDraw.Draw(image,'RGBA')
    draw.rounded_rectangle((25,55,W-25,155),radius=25,fill=(0,0,0,170))
    draw.text((48,84),'MONKEY MODE  /  EPISODE 01',font=small,fill=(255,255,255,255))
    lines=wrap(draw,caption)
    box_height=75*len(lines)+65
    y0=H-230-box_height
    draw.rounded_rectangle((25,y0,W-25,y0+box_height),radius=28,fill=(0,0,0,190))
    for j,line in enumerate(lines):
        bounds=draw.textbbox((0,0),line,font=large)
        draw.text(((W-(bounds[2]-bounds[0]))/2,y0+27+j*75),line,font=large,fill=(255,255,255,255),stroke_width=2,stroke_fill=(0,0,0,255))
    still=OUT/f'frame_{i:02d}.png'; image.save(still)
    clip=OUT/f'clip_{i:02d}.mp4'
    run(['ffmpeg','-hide_banner','-loglevel','error','-y','-loop','1','-framerate',str(fps),'-i',str(still),'-vf',"zoompan=z='min(zoom+0.00045,1.09)':d=1:s=720x1280:fps=24,format=yuv420p",'-frames:v',str(frames),'-c:v','libx264','-preset','veryfast','-crf','26','-an',str(clip)])
    clips.append(clip)
playlist=OUT/'concat.txt'
playlist.write_text(''.join(f"file '{clip.name}'\n" for clip in clips))
video=OUT/'silent.mp4'
run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(playlist),'-c','copy',str(video)])
# A subtle original synthetic beat, mixed quietly under narration.
final=OUT/'final_short.mp4'
run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(video),'-i',str(voice),'-f','lavfi','-i','sine=frequency=110:sample_rate=44100','-filter_complex','[2:a]volume=0.012[beat];[1:a][beat]amix=inputs=2:duration=first:dropout_transition=0[a]','-map','0:v:0','-map','[a]','-c:v','copy','-c:a','aac','-b:a','128k','-t',str(D),'-movflags','+faststart',str(final)])
print('Created:',final,'duration:',round(D,1))

])

print("Video created:", final_video)
print("Title:", title)
print("Duration:", round(audio_duration, 1), "seconds")
