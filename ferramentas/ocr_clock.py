"""Lê o cronômetro do placar da transmissão (1 quadro/s) -> CSV video_s,clock_s,txt,score"""
import subprocess, sys, re, csv, time
import numpy as np
from rapidocr_onnxruntime import RapidOCR
video, out = sys.argv[1], sys.argv[2]
W, H, S = 50, 16, 4
cmd = ["ffmpeg", "-loglevel", "error", "-i", video, "-vf",
       f"fps=1,crop={W}:{H}:298:287,scale={W*S}:{H*S}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"]
p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
rec = RapidOCR().text_recognizer
n = W * S * H * S * 3
t0, t, ok, batch = time.time(), 0, 0, []
def flush(w, batch):
    global ok
    res = rec([b[1] for b in batch])[0]
    for (ts, _), (txt, sc) in zip(batch, res):
        c = re.fullmatch(r"\s*(\d{1,2})\s*[:.]\s*(\d{2})\s*", txt)
        if c and int(c.group(2)) < 60 and int(c.group(1)) * 60 + int(c.group(2)) <= 600:
            w.writerow((ts, int(c.group(1)) * 60 + int(c.group(2)), txt, round(float(sc), 3))); ok += 1
with open(out, "w", newline="") as f:
    w = csv.writer(f); w.writerow(["video_s", "clock_s", "txt", "score"])
    while True:
        buf = p.stdout.read(n)
        if len(buf) < n: break
        batch.append((t, np.frombuffer(buf, np.uint8).reshape(H * S, W * S, 3).copy())); t += 1
        if len(batch) == 64:
            flush(w, batch); batch = []
        if t % 1200 == 0: print(f"{t}s | lidos {ok} | {time.time()-t0:.0f}s", flush=True)
    if batch: flush(w, batch)
print(f"FIM frames={t} lidos={ok} tempo={time.time()-t0:.0f}s", flush=True)
