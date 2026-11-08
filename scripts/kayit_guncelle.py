"""Tum bolumlerin kesitlerini tek kayitta (calisma/kesit_kaydi.csv) toplar.

Kullanim: python scripts/kayit_guncelle.py <bolum_klasoru>
Amac: Hangi bolumun hangi araliginin kullanildigini takip etmek; ileride ayni bolume
donuldugunde kullanilan yerler atlanir. Excel'de duzenlenebilir ("durum" sutunu korunur).
"""
import csv
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ALANLAR = ["kod", "kesit", "isim", "tur", "baslangic", "bitis", "sure_sn", "dosyalar", "durum", "ozet"]


def mmss(t: float) -> str:
    return f"{int(t) // 60:02}:{int(t) % 60:02}"


def main() -> None:
    d = Path(sys.argv[1])
    kayit = Path(__file__).parent.parent / "calisma" / "kesit_kaydi.csv"  # tum diziler icin tek kayit
    kayit.parent.mkdir(exist_ok=True)
    v = json.loads((d / "kesitler.json").read_text(encoding="utf-8"))
    eski = {}
    if kayit.exists():
        with kayit.open(encoding="utf-8-sig", newline="") as f:
            eski = {(r["kod"], r["kesit"]): r for r in csv.DictReader(f, delimiter=";")}
    for k in v["kesitler"]:
        anahtar = (v["kod"], k["id"])
        dosyalar = sorted(p.name for p in (d / "shorts").glob(f"{v['kod']}-{k['id']}-*.mp4")) if k["tur"] == "shorts" else [f"{k['id']}.mp4"]
        eski[anahtar] = {
            "kod": v["kod"], "kesit": k["id"], "isim": k.get("isim_tr", ""), "tur": k["tur"], "baslangic": mmss(k["baslangic"]), "bitis": mmss(k["bitis"]),
            "sure_sn": k["sure"], "dosyalar": " ".join(dosyalar),
            "durum": eski.get(anahtar, {}).get("durum", "aday"), "ozet": k["ozet"],
        }
    with kayit.open("w", encoding="utf-8-sig", newline="") as f:
        y = csv.DictWriter(f, ALANLAR, delimiter=";")
        y.writeheader()
        y.writerows(eski[a] for a in sorted(eski))
    print(f"BITTI: {len(eski)} satir -> {kayit}")


if __name__ == "__main__":
    main()
