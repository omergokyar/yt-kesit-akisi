"""Secilen kesitlerin sinirlarini sahne gecislerine ve konusma aralarina oturtur.

Kullanim: python scripts/kesit_sinirla.py <bolum_klasoru>
Girdi: kesitler.taslak.json, transcript.json, scenes.json
Cikti: kesitler.json (baslangic/bitis/sure eklenmis)

Kural: Kesit hicbir zaman bir cumlenin icinden baslamaz veya bitmez. Yakin bir sahne
gecisi varsa ona oturur, yoksa konusmanin hemen oncesinde/sonrasinda kisa pay birakilir.
"""
import json
import sys
from pathlib import Path

from zaman import duzelt

sys.stdout.reconfigure(encoding="utf-8")

SINIRLAR = {"uzun": (480, 720), "shorts": (30, 90)}
ARAMA = {"uzun": 15.0, "shorts": 4.0}
BITIS_ARAMA = {"uzun": 5.0, "shorts": 3.0}
BITIS_PAY = {"uzun": 1.5, "shorts": 0.35}
PAY = 0.35
BAS_TOLERANS = 0.3
IC_SESSIZLIK = 8.0  # shorts icinde bundan uzun konusmasiz ara varsa uyarilir


def mmss(t: float) -> str:
    return f"{int(t) // 60:02}:{int(t) % 60:02}"


def main() -> None:
    d = Path(sys.argv[1])
    taslak = json.loads((d / "kesitler.taslak.json").read_text(encoding="utf-8"))
    seg = json.loads((d / "transcript.json").read_text(encoding="utf-8"))
    sure_toplam = seg["meta"]["duration"]
    seg = seg["segments"]
    print(f"zaman duzeltmesi: {duzelt(seg)} segment", flush=True)
    gecisler = sorted({s["start"] for s in json.loads((d / "scenes.json").read_text(encoding="utf-8"))})

    for k in taslak["kesitler"]:
        i, j = k["ilk_satir"] - 1, k["son_satir"] - 1
        ilk, son = seg[i]["start"], seg[j]["end"]
        once = seg[i - 1]["end"] if i else 0.0
        sonra = seg[j + 1]["start"] if j + 1 < len(seg) else sure_toplam
        menzil = ARAMA[k["tur"]]

        # En yakin gecis: daha geriye gitmek onceki sahneyi kesite sokar.
        # Tolerans: kelime zamani tahminidir; cumleyle ayni anda gelen gecis onceki plana dusurmesin.
        adaylar = [g for g in gecisler if max(once, ilk - menzil) <= g <= ilk + BAS_TOLERANS]
        bas = max(adaylar) if adaylar else max(once, ilk - PAY)

        # Bitis aramasi kisa tutulur: uzak bir gecis jenerik/logoya tasir (U3).
        adaylar = [g for g in gecisler if son <= g <= min(sonra, son + BITIS_ARAMA[k["tur"]])]
        bit = min(adaylar) if adaylar else min(sonra, son + BITIS_PAY[k["tur"]])

        # Konusmasiz acilis gerekiyorsa (or. yuzugun cikarilisi) elle hedef baslangic.
        if k.get("baslangic_hedef"):
            hedef = k["baslangic_hedef"]
            bas = max((g for g in gecisler if hedef - 5 <= g <= hedef), default=hedef)  # yakin gecis yoksa tam hedef

        # Konusmasiz (muzikli) devam eden bolumler icin elle hedef bitis: hedeften onceki son gecis.
        if k.get("bitis_hedef"):
            bit = max((g for g in gecisler if son < g <= k["bitis_hedef"]), default=k["bitis_hedef"])

        k["fa_satirlar"] = [s["text"] for s in seg[i : j + 1]]
        k.update(baslangic=round(bas, 2), bitis=round(bit, 2), sure=round(bit - bas, 1))
        k["sahneye_oturdu"] = bas in gecisler and bit in gecisler
        alt, ust = SINIRLAR[k["tur"]]
        uyari = "" if alt <= k["sure"] <= ust else "  <-- SURE SINIR DISI"
        if k["tur"] == "shorts":
            kelimeler = [w for s in seg[i : j + 1] for w in s["words"]]
            ara = max((b["start"] - a["end"] for a, b in zip(kelimeler, kelimeler[1:])), default=0)
            if ara > IC_SESSIZLIK:
                uyari += f"  <-- {ara:.0f} sn konusmasiz ara, kontrol et"
        print(f"{k['id']}: {mmss(bas)}-{mmss(bit)}  {k['sure']:7.1f} sn  sahne={k['sahneye_oturdu']}{uyari}")

    if "--kuru" not in sys.argv:
        (d / "kesitler.json").write_text(json.dumps(taslak, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
