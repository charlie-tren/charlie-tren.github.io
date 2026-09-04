"""Contact sheet of the structural design directions in tools/proto/."""
import io, subprocess, time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
HUB = HERE.parent.parent
PORT = 8814
W, H = 900, 700
NAMES = [("A. Jacket","a-jacket.html"),("B. Card catalogue","b-catalogue.html"),
         ("C. Sentence","c-sentence.html"),("D. Shelf","d-shelf.html")]

def main():
    srv = subprocess.Popen(["python","-m","http.server",str(PORT),"--directory",str(HUB)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    shots=[]
    try:
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            for label, f in NAMES:
                pg = b.new_page(viewport={"width":W,"height":H}, device_scale_factor=2)
                pg.goto(f"http://localhost:{PORT}/bookmark/tools/proto/{f}", wait_until="networkidle")
                pg.wait_for_timeout(400)
                shots.append((label, Image.open(io.BytesIO(pg.screenshot())).convert("RGB")))
                pg.close()
            b.close()
    finally:
        srv.terminate()
    w,h = shots[0][1].size
    pad, lab = 26, 42
    sheet = Image.new("RGB",(2*w+3*pad, 2*(h+lab)+3*pad), "#3a3a3a")
    d = ImageDraw.Draw(sheet)
    try: font = ImageFont.truetype("segoeuib.ttf", 28)
    except OSError: font = ImageFont.load_default()
    for i,(label,im) in enumerate(shots):
        x = pad + (i%2)*(w+pad); y = pad + (i//2)*(h+lab+pad)
        d.text((x,y+4), label, fill="#fff", font=font)
        sheet.paste(im,(x,y+lab))
    out = HERE/"design_options_2.png"; sheet.save(out); print(out, sheet.size)

main()
