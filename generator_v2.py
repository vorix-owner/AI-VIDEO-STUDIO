"""Version 2: Wikimedia Commons licensed video + neural English TTS.
Fail clearly rather than silently generating a slide-only video.
"""
import asyncio, json, random, re, subprocess, urllib.parse, urllib.request, time, urllib.error
from pathlib import Path
import edge_tts

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"output"; WORK=OUT/"v2"; WORK.mkdir(parents=True,exist_ok=True)
SCENES=[
("The ocean looks peaceful from above. But below its surface lies a world of darkness, pressure, and astonishing life. Come with us on a journey into the deep.", "ocean underwater"),
("Sunlight quickly weakens as we descend. In the twilight zone, many animals are adapted to survive with barely any light. Their eyes and senses work differently from ours.", "underwater fish"),
("Some animals produce their own light through bioluminescence. These flashes may help attract prey, communicate, or confuse predators in the darkness.", "jellyfish underwater"),
("Deeper still, the ocean becomes almost completely dark. Water pressure rises dramatically. Creatures living here have remarkable biological adaptations.", "deep sea"),
("Food can be scarce. Small pieces of organic matter drift down from the surface, a phenomenon scientists call marine snow. This slow rain supports deep ecosystems.", "underwater plankton"),
("The seafloor itself contains mountains, valleys, and trenches. Some landscapes are so remote that scientists can only study them using specialized underwater vehicles.", "ocean floor"),
("At hydrothermal vents, mineral-rich water flows out of the seafloor. Communities of organisms can thrive here using chemical energy instead of sunlight.", "hydrothermal vent"),
("The Mariana Trench contains Challenger Deep, the deepest known part of Earth's ocean. Reaching such depths requires specially engineered submersibles.", "submersible ocean"),
("Scientists continue to discover new deep-sea species and behaviors. Each expedition adds another piece to our understanding of the planet.", "marine life underwater"),
("The ocean is not an empty abyss. It is a connected system of habitats that influence life on Earth. Protecting it requires research and careful decisions.", "coral reef underwater"),
("What else remains to be discovered? The next scientific expedition might reveal something no one has ever seen. Keep your curiosity alive.", "ocean waves")
]
UA="AI-VIDEO-STUDIO/0.2 (educational video prototype; contact via GitHub)"
def request_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req,timeout=35) as r:return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 2: raise
            time.sleep(12*(attempt+1))
def fetch(url,dest):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    with urllib.request.urlopen(req,timeout=75) as r,open(dest,"wb") as f:
        total=0
        while True:
            b=r.read(1024*512)
            if not b:break
            total+=len(b)
            if total>25*1024*1024:raise ValueError('clip exceeds 25 MB download cap')
            f.write(b)
def run(args):subprocess.run(args,check=True)
def commons_candidates(term):
    params={"action":"query","generator":"search","gsrsearch":'filetype:video '+term,"gsrnamespace":"6","gsrlimit":"8","prop":"imageinfo","iiprop":"url|mime|size|extmetadata","format":"json"}
    data=request_json("https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode(params))
    found=[]
    for p in data.get("query",{}).get("pages",{}).values():
        for info in p.get("imageinfo",[]):
            mime=info.get("mime","")
            url=info.get("url","")
            meta=info.get("extmetadata",{})
            lic=meta.get("LicenseShortName",{}).get("value","")
            if mime.startswith("video/") and url and info.get("size",0) < 25*1024*1024 and ("CC" in lic or "Public domain" in lic or "PD" == lic):
                found.append({"url":url,"source":p.get("title"),"license":lic,"artist":re.sub("<[^>]*>","",meta.get("Artist",{}).get("value",""))[:150]})
    return found
async def speak(text,path):
    tts=edge_tts.Communicate(text,voice="en-US-JennyNeural",rate="-5%")
    await tts.save(str(path))
def probe_duration(path):
    r=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(path)],capture_output=True,text=True,check=True)
    return float(r.stdout.strip())
def subtitle_filter(text):
    # Draw caption in 2-4 short lines; escape ffmpeg text metacharacters.
    words=text.split(); lines=[]; cur=[]
    for w in words:
        if len(" ".join(cur+[w]))>32 and cur:lines.append(" ".join(cur));cur=[w]
        else:cur.append(w)
    if cur:lines.append(" ".join(cur))
    return "\\n".join(lines[:5]).replace("\\","\\\\").replace(":","\\:").replace("'","\\'").replace("%","\\%")
async def main():
    random.seed(11)
    manifest=[]; credits=[]; downloaded=[]
    for i,(speech,search) in enumerate(SCENES):
        voice=WORK/f"voice_{i}.mp3"
        await speak(speech,voice)
        dur=max(12.0,probe_duration(voice)+1)
        # Reuse a small set of licensed real video clips to reduce Wikimedia requests.
        options=commons_candidates(search) if len(downloaded)<3 else []
        if not options and not downloaded:raise RuntimeError(f"No verified CC/PD video available for {search}; refusing slide-only fallback")
        video=None
        for j,item in enumerate(options[:3]):
            try:
                candidate=WORK/f"clip_{i}.{j}.webm"
                fetch(item["url"],candidate)
                if candidate.stat().st_size>50*1024*1024:raise ValueError("clip too large")
                if probe_duration(candidate)<2:raise ValueError("clip too short")
                video=candidate;credits.append(item);downloaded.append(candidate);break
            except Exception as e:print("Skipping media",str(e)[:140])
        if video is None and downloaded:
            video=downloaded[i%len(downloaded)]
            print("Reusing previously downloaded licensed real footage for",search)
        if video is None:raise RuntimeError(f"Unable to download usable licensed footage for {search}")
        output=WORK/f"scene_{i:02}.mp4"
        # loop footage; audio is spoken neural voice; text stays visible.
        vf="scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,setsar=1,fps=24,format=yuv420p"
        run(["ffmpeg","-y","-hide_banner","-loglevel","error","-stream_loop","-1","-i",str(video),"-i",str(voice),
             "-filter_complex",f"[0:v]{vf}[v];[1:a]apad[a]",
             "-map","[v]","-map","[a]","-t",str(dur),"-c:v","libx264","-preset","veryfast","-crf","27",
             "-c:a","aac","-b:a","128k",str(output)])
        manifest.append(output)
        time.sleep(2)
    listfile=WORK/"concat.txt"
    listfile.write_text("".join("file '"+str(p.resolve())+"'\n" for p in manifest))
    final=OUT/"mystery_v2.mp4"
    run(["ffmpeg","-y","-hide_banner","-loglevel","error","-f","concat","-safe","0","-i",str(listfile),"-c","copy",str(final)])
    (OUT/"CREDITS.json").write_text(json.dumps(credits,indent=2))
    print("FINISHED",final,"duration",probe_duration(final))
    if probe_duration(final)<120:raise RuntimeError("Video shorter than required 2 minutes")
if __name__=="__main__":asyncio.run(main())
