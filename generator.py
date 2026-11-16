"""No paid APIs: original narration, animated typography, offline speech, FFmpeg.
Prototype intentionally uses slide motion, not generated cinematic footage.
"""
from pathlib import Path
import subprocess
import wave
import math
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"output"
TMP=OUT/"segments"
TMP.mkdir(parents=True,exist_ok=True)
FONT="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONTREG="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SCENES=[
("THE DEEP OCEAN","What really lies beneath the ocean surface? Today we explore the deep sea, a place that remains difficult for humans to visit."),
("A WORLD BELOW","Sunlight fades as we descend. Oceanographers divide the water into depth zones, each with different pressure, light, and temperature."),
("THE TWILIGHT ZONE","Between about two hundred and one thousand meters, only a small amount of sunlight penetrates. Many animals here create their own light."),
("LIVING LIGHTS","Bioluminescence is light produced by chemical reactions in living organisms. Some creatures use it to attract prey, communicate, or hide."),
("THE MIDNIGHT ZONE","Below one thousand meters, sunlight is essentially absent. The ocean is cold, dark, and under enormous pressure."),
("CRUSHING PRESSURE","Water pressure increases with depth. Specially adapted organisms survive conditions that would be dangerous to an unprotected human."),
("MARINE SNOW","Tiny particles of dead organisms and waste drift downward from above. This material helps feed ecosystems far below the surface."),
("STRANGE SURVIVORS","Deep sea fish can have unusually large mouths, sensitive organs, and flexible bodies. These adaptations help them find scarce food."),
("UNDERWATER MOUNTAINS","The seafloor is not flat. It contains vast mountain ranges, valleys, plains, and deep trenches."),
("THE DEEPEST TRENCH","Challenger Deep in the Mariana Trench is the deepest known point in the ocean. Its exact measured depth varies by survey."),
("HOT WATER VENTS","Hydrothermal vents release mineral rich fluids. Remarkably, some nearby ecosystems depend on chemical energy rather than sunlight."),
("LIFE WITHOUT SUN","Microbes near vents can use chemical compounds to produce energy. Larger animals may depend on these microbes directly or indirectly."),
("WHAT WE DON'T KNOW","The ocean is immense, and much of its deep environment remains challenging to observe directly. New expeditions continue to reveal species."),
("THE FINAL QUESTION","What surprising discovery might be waiting in the deep sea? Follow for more science based mysteries, and keep asking questions.")
]
def run(args):
    subprocess.run(args,check=True)
def duration_wav(path):
    with wave.open(str(path),"rb") as w:
        return w.getnframes()/w.getframerate()
def wrap(draw,text,font,max_width):
    lines=[]; line=""
    for word in text.split():
        candidate=(line+" "+word).strip()
        if draw.textbbox((0,0),candidate,font=font)[2]>max_width and line:
            lines.append(line);line=word
        else: line=candidate
    if line:lines.append(line)
    return lines
def artwork(title,number):
    img=Image.new("RGB",(540,960),(5,13,30))
    d=ImageDraw.Draw(img)
    for y in range(960):
        r=int(7+14*y/960);g=int(24+24*y/960);b=int(50+31*y/960)
        d.line((0,y,540,y),fill=(r,g,b))
    for k in range(16):
        x=(k*83+number*29)%540;y=(k*157+number*41)%960
        d.ellipse((x,y,x+3+k%5,y+3+k%5),fill=(34,115,148))
    big=ImageFont.truetype(FONT,47)
    small=ImageFont.truetype(FONTREG,24)
    d.rounded_rectangle((30,60,510,110),radius=20,fill=(14,88,109))
    d.text((52,71),"AMAZING FACTS  /  MYSTERIES",font=ImageFont.truetype(FONT,19),fill="white")
    lines=wrap(d,title,big,475)
    y=365-len(lines)*33
    for line in lines:
        d.text((35,y),line,font=big,fill=(239,247,255),stroke_width=1,stroke_fill=(2,12,30))
        y+=66
    d.rectangle((36,y+14,200,y+19),fill=(38,211,198))
    d.text((36,852),f"DEEP OCEAN  •  {number+1:02d}/{len(SCENES):02d}",font=small,fill=(178,217,226))
    path=TMP/f"slide_{number:02d}.png";img.save(path)
    return path
segments=[]
for i,(title,narration) in enumerate(SCENES):
    png=artwork(title,i)
    wav=TMP/f"voice_{i:02d}.wav"
    run(["espeak-ng","-v","en-us","-s","137","-w",str(wav),narration])
    seconds=max(10.1,duration_wav(wav)+1.2)
    mp4=TMP/f"scene_{i:02d}.mp4"
    run(["ffmpeg","-hide_banner","-loglevel","error","-y",
         "-loop","1","-framerate","12","-i",str(png),"-i",str(wav),
         "-filter_complex","[0:v]zoompan=z='min(zoom+0.00025,1.10)':d=1:s=540x960:fps=12,format=yuv420p[v];[1:a]apad[a]",
         "-map","[v]","-map","[a]","-t",f"{seconds:.2f}",
         "-c:v","libx264","-preset","ultrafast","-crf","29","-r","12",
         "-c:a","aac","-b:a","96k",str(mp4)])
    segments.append(mp4)
manifest=TMP/"concat.txt"
manifest.write_text("".join("file '"+str(p.resolve()).replace("'","'\\''")+"'\n" for p in segments))
run(["ffmpeg","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(manifest),"-c","copy",str(OUT/"mystery.mp4")])
print("Created:",OUT/"mystery.mp4")
