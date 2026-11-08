"""16:9 kesitleri plan plan yuz takibiyle 9:16 Shorts'a cevirir.

Kullanim: python scripts/dikey.py <bolum_klasoru> [S3 S6 ...] [--mod takipli enbuyuk karma]
Girdi: klipler/<id>.mp4, kesitler.json, scenes.json
Cikti: shorts/<kod>-<id>-<baslangic>-<mod>.mp4 ve plan/<id>.json

Dublajda ses ile dudak ortusmedigi icin konusmaci dudaktan aranmaz. Bulanik arka plan
kullanilmaz. Modlar:
  takipli : varsayilan. Tek 9:16 kadraj; sigmayan planda buyukluk+netlik+sure ile odaktaki kisi
  karma   : takipli + iki yuz net, kameraya donuk ve yeterince buyukse alt alta panel
  enbuyuk : istege bagli (--mod enbuyuk). Sigmayan planda en buyuk kisi, genis planda yaklasir
Bir mod ayni sonucu verirse o surum uretilmez; yani karma yalnizca alt alta kullanilan kliplerde cikar.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

MODEL = Path(__file__).parent.parent / "modeller" / "yunet" / "face_detection_yunet_2023mar.onnx"
CIKIS_W, CIKIS_H = 1080, 1920
ORNEK = 5  # her 5 karede bir yuz ara
PANEL_ORAN = CIKIS_W / (CIKIS_H / 2)
MIN_VARLIK = 0.25
MIN_PANEL_YUZ = 110  # karma: panele girecek yuzun kaynak genisligi (piksel); genis planlar elenir
MAKS_YAN_BAKIS = 0.6  # karma: profilden gorunen yuzler panele alinmaz
MIN_NET_ORAN = 0.2  # karma: omuz arkasindan flu gorunen kisi panele alinmaz
YAKIN_ESIK = 130  # enbuyuk: en buyuk yuz bundan kucukse plan genistir, yaklasilir
YAKIN_MIN_H = 720  # enbuyuk: yaklasirken kaynaktan alinacak en az yukseklik


def analiz(video: Path) -> tuple[list, float, int, int, int]:
    cap = cv2.VideoCapture(str(video))
    fps, W, H = cap.get(cv2.CAP_PROP_FPS), int(cap.get(3)), int(cap.get(4))
    olcek = W / 960
    det = cv2.FaceDetectorYN.create(str(MODEL), "", (960, round(H / olcek)), 0.6, 0.3, 5000)
    ornekler, i = [], 0
    while True:
        ok, kare = cap.read()
        if not ok:
            break
        if i % ORNEK == 0:
            kucuk = cv2.resize(kare, det.getInputSize())
            _, yuzler = det.detect(kucuk)
            bulunan = []
            for y in yuzler if yuzler is not None else []:
                x, yy, w, h = (float(v) * olcek for v in y[:4])
                x0, y0 = max(int(x), 0), max(int(yy), 0)
                parca = kare[y0 : int(yy + h), x0 : int(x + w)]
                if parca.size == 0:
                    continue
                gri = cv2.cvtColor(cv2.resize(parca, (64, 64)), cv2.COLOR_BGR2GRAY)
                sag_goz, sol_goz, burun = float(y[4]), float(y[6]), float(y[8])
                on = abs(burun - (sag_goz + sol_goz) / 2) / (abs(sag_goz - sol_goz) + 1e-3)  # 0'a yakin: kameraya donuk
                bulunan.append({"x": x, "y": yy, "w": w, "h": h, "net": float(cv2.Laplacian(gri, cv2.CV_64F).var()), "on": on})
            ornekler.append({"i": i, "yuzler": bulunan})
        i += 1
    cap.release()
    return ornekler, fps, W, H, i


def izler(ornekler: list, W: int) -> list:
    """Yuzleri yatay konuma gore kisilere ayirir."""
    hepsi = sorted(
        ((f["x"] + f["w"] / 2, o["i"], f) for o in ornekler for f in o["yuzler"]), key=lambda t: t[0]
    )
    if not hepsi:
        return []
    gruplar, simdiki = [], [hepsi[0]]
    for a in hepsi[1:]:
        if a[0] - simdiki[-1][0] > 0.09 * W:
            gruplar.append(simdiki)
            simdiki = []
        simdiki.append(a)
    gruplar.append(simdiki)

    sonuc = []
    for g in gruplar:
        varlik = len({a[1] for a in g}) / max(len(ornekler), 1)
        if varlik < MIN_VARLIK:
            continue
        g.sort(key=lambda a: a[1])
        fs = [a[2] for a in g]
        sonuc.append(
            {
                "varlik": varlik,
                "cx": float(np.median([a[0] for a in g])),
                "cy": float(np.median([f["y"] + f["h"] / 2 for f in fs])),
                "w": float(np.median([f["w"] for f in fs])),
                "h": float(np.median([f["h"] for f in fs])),
                "net": float(np.median([f["net"] for f in fs])),
                "on": float(np.median([f["on"] for f in fs])),
                "kareler": [a[1] for a in g],
                "merkezler": [a[0] for a in g],
            }
        )
    return sonuc


def yol(iz: dict, bas: int, n: int, crop_w: int, W: int) -> list:
    """Takip edilen kisi icin kare basina kirpma sol kenari."""
    xler = np.interp(np.arange(bas, bas + n), iz["kareler"], iz["merkezler"])
    if xler.max() - xler.min() < 60:
        xler = np.full(n, float(np.median(xler)))
    else:
        pencere = min(31, max(n | 1, 1))
        dolgu = np.pad(xler, pencere // 2, mode="edge")
        xler = np.convolve(dolgu, np.ones(pencere) / pencere, mode="valid")[:n]
    return [float(np.clip(x - crop_w / 2, 0, W - crop_w)) for x in xler]


def panel(iz: dict, W: int, H: int, maks_w: float) -> list:
    """maks_w: yan yana oturanlarda diger kisinin yuzu panele girmesin diye genislik siniri."""
    ch = int(np.clip(iz["h"] * 2.8, 480, H))
    cw = int(min(ch * PANEL_ORAN, W, max(maks_w, 480)))
    ch = int(cw / PANEL_ORAN)
    x = int(np.clip(iz["cx"] - cw / 2, 0, W - cw))
    y = int(np.clip(iz["cy"] - ch * 0.42, 0, H - ch))
    return [x, y, cw, ch]


def plan_yap(ornekler: list, fps: float, W: int, H: int, toplam: int, kesimler: list, mod: str) -> list:
    crop_w = int(H * 9 / 16) & ~1
    sinirlar = [0] + sorted({round(t * fps) for t in kesimler if 0 < t * fps < toplam}) + [toplam]
    planlar = []
    for a, b in zip(sinirlar, sinirlar[1:]):
        n = b - a
        ilgili = [o for o in ornekler if a <= o["i"] < b]
        kisiler = izler(ilgili, W)
        p = {"bas": a, "n": n, "kisi": len(kisiler)}
        if not kisiler:
            p.update(tur="yuz_yok", sol=[(W - crop_w) / 2] * n)
        elif mod == "enbuyuk" and max(k["w"] for k in kisiler) < YAKIN_ESIK:
            en = max(kisiler, key=lambda k: k["w"])
            ch = int(np.clip(en["h"] * 5, YAKIN_MIN_H, H)) & ~1
            cw = int(ch * 9 / 16) & ~1
            x = int(np.clip(en["cx"] - cw / 2, 0, W - cw))
            y = int(np.clip(en["cy"] - ch * 0.35, 0, H - ch))
            p.update(tur="yakin", kutu=[x, y, cw, ch])
        else:
            sol_uc = min(k["cx"] - k["w"] / 2 for k in kisiler)
            sag_uc = max(k["cx"] + k["w"] / 2 for k in kisiler)
            if sag_uc - sol_uc + 80 <= crop_w:
                x = float(np.clip((sol_uc + sag_uc) / 2 - crop_w / 2, 0, W - crop_w))
                p.update(tur="hepsi_sigdi", sol=[x] * n)
            else:
                en_net = max(k["net"] for k in kisiler) or 1.0
                if mod == "enbuyuk":
                    puan = lambda k: k["w"]  # kameraya en yakin kisi
                else:
                    puan = lambda k: k["varlik"] * k["w"] * (0.4 + 0.6 * k["net"] / en_net)
                sirali = sorted(kisiler, key=puan, reverse=True)
                iki = sirali[:2]
                if (
                    mod == "karma"
                    and len(iki) == 2
                    and min(k["varlik"] for k in iki) >= 0.5
                    and min(k["w"] for k in iki) / max(k["w"] for k in iki) >= 0.45
                    and min(k["w"] for k in iki) >= MIN_PANEL_YUZ
                    and min(k["net"] for k in iki) / max(k["net"] for k in iki) >= MIN_NET_ORAN
                    and max(k["on"] for k in iki) <= MAKS_YAN_BAKIS
                ):
                    iki.sort(key=lambda k: k["cx"])
                    mesafe = iki[1]["cx"] - iki[0]["cx"]
                    p.update(tur="altalta", ust=panel(iki[0], W, H, mesafe), alt=panel(iki[1], W, H, mesafe))
                else:
                    p.update(tur="secim", sol=yol(sirali[0], a, n, crop_w, W))
        planlar.append(p)
    return planlar


def uret(video: Path, hedef: Path, planlar: list, fps: float, W: int, H: int) -> None:
    crop_w = int(H * 9 / 16) & ~1
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{CIKIS_W}x{CIKIS_H}", "-r", str(fps),
         "-i", "-", "-i", str(video), "-map", "0:v", "-map", "1:a?", "-c:v", "h264_nvenc", "-preset", "p5", "-cq", "21",
         "-pix_fmt", "yuv420p", "-c:a", "copy", "-shortest", "-movflags", "+faststart", str(hedef)],
        stdin=subprocess.PIPE,
    )
    cap = cv2.VideoCapture(str(video))
    for p in planlar:
        for k in range(p["n"]):
            ok, kare = cap.read()
            if not ok:
                break
            if p["tur"] == "altalta":
                parcalar = []
                for x, y, cw, ch in (p["ust"], p["alt"]):
                    parcalar.append(cv2.resize(kare[y : y + ch, x : x + cw], (CIKIS_W, CIKIS_H // 2), interpolation=cv2.INTER_LANCZOS4))
                cikti = np.vstack(parcalar)
                cikti[CIKIS_H // 2 - 3 : CIKIS_H // 2 + 3] = 0
            elif p["tur"] == "yakin":
                x, y, cw, ch = p["kutu"]
                cikti = cv2.resize(kare[y : y + ch, x : x + cw], (CIKIS_W, CIKIS_H), interpolation=cv2.INTER_LANCZOS4)
            else:
                x = int(p["sol"][k])
                cikti = cv2.resize(kare[:, x : x + crop_w], (CIKIS_W, CIKIS_H), interpolation=cv2.INTER_LANCZOS4)
            ff.stdin.write(cikti.tobytes())
    cap.release()
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError(f"ffmpeg hatasi: {hedef}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("bolum", type=Path)
    ap.add_argument("kesitler", nargs="*")
    ap.add_argument("--mod", nargs="+", default=["takipli", "karma"], choices=["takipli", "enbuyuk", "karma"])
    a = ap.parse_args()
    cikis = a.bolum / "shorts"
    cikis.mkdir(exist_ok=True)
    plan_klasor = a.bolum / "plan"
    plan_klasor.mkdir(exist_ok=True)
    veri = json.loads((a.bolum / "kesitler.json").read_text(encoding="utf-8"))
    tum, kod = veri["kesitler"], veri["kod"]
    sahneler = [s["start"] for s in json.loads((a.bolum / "scenes.json").read_text(encoding="utf-8"))]
    for k in tum:
        if k["tur"] != "shorts" or (a.kesitler and k["id"] not in a.kesitler):
            continue
        video = a.bolum / "klipler" / f"{k['id']}.mp4"
        ornekler, fps, W, H, toplam = analiz(video)
        kesimler = [s - k["baslangic"] for s in sahneler if k["baslangic"] < s < k["bitis"]]
        kayit, goruldu = {}, {}
        bas = f"{int(k['baslangic']) // 60:02}{int(k['baslangic']) % 60:02}"
        for mod in a.mod:
            planlar = plan_yap(ornekler, fps, W, H, toplam, kesimler, mod)
            imza = json.dumps([[p["tur"], [round(x) for x in p.get("sol", [])], p.get("ust"), p.get("alt"), p.get("kutu")] for p in planlar])
            if imza in goruldu:
                print(f"{k['id']} {mod}: {goruldu[imza]} ile ayni, uretilmedi", flush=True)
                continue
            goruldu[imza] = mod
            uret(video, cikis / f"{kod}-{k['id']}-{bas}-{mod}.mp4", planlar, fps, W, H)
            turler = {}
            for p in planlar:
                turler[p["tur"]] = turler.get(p["tur"], 0) + 1
            kayit[mod] = [{x: p[x] for x in p if x != "sol"} for p in planlar]
            print(f"{k['id']} {mod}: {len(planlar)} plan {turler}", flush=True)
        (plan_klasor / f"{k['id']}.json").write_text(json.dumps(kayit), encoding="utf-8")
    print("BITTI")


if __name__ == "__main__":
    main()
