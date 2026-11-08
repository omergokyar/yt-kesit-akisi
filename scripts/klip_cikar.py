"""kesitler.json'daki kesitleri kaynak videodan tek parca (montajsiz) MP4 olarak cikarir.

Kullanim: python scripts/klip_cikar.py <video> <bolum_klasoru> [kesit_id ...]
Cikti: <bolum_klasoru>/klipler/<id>.mp4 (kaynak cozunurluk, 16:9)
"""
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")


def main() -> None:
    video, d = Path(sys.argv[1]), Path(sys.argv[2])
    out = d / "klipler"
    out.mkdir(exist_ok=True)
    kesitler = json.loads((d / "kesitler.json").read_text(encoding="utf-8"))["kesitler"]
    secim = set(sys.argv[3:])  # bos ise hepsi
    for k in kesitler:
        if secim and k["id"] not in secim:
            continue
        hedef = out / f"{k['id']}.mp4"
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", str(k["baslangic"]), "-i", str(video), "-t", str(k["sure"]),
             "-c:v", "h264_nvenc", "-preset", "p5", "-cq", "21", "-c:a", "aac", "-b:a", "160k",
             "-movflags", "+faststart", str(hedef)],
            check=True,
        )
        print(f"{k['id']} tamam", flush=True)
    print("BITTI")


if __name__ == "__main__":
    main()
