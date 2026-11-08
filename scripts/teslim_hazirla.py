"""Bir bolumu Drive'a yuklemeye hazir hale getirir: kontrol listesi + adlandirilmis videolar.

Kullanim: python scripts/teslim_hazirla.py <bolum_klasoru>
Cikti: teslim/<kod>/<kod>-liste.xlsx, uzun/<kod>-<id>-<baslangic>.mp4, shorts/<dosyalar>
Videolar kopyalanmaz, hard link olusturulur (diskte ek yer kaplamaz). Shorts'ta takipli ve
varsa karma surum gider. Liste Google Sheets'te acilir: ustte durum satiri, her klip Farsca ve
Turkce satirlardan olusur, Shorts'un altinda diyalog satirlari vardir.
"""
import json
import math
import os
import shutil
import sys
from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

sys.stdout.reconfigure(encoding="utf-8")

ONAY, DUZELT, RET = "Onay / تأیید", "Düzeltme / اصلاح", "Ret / رد"
KOLON = [
    ("Kesit", "کلیپ", 7), ("Tür", "نوع", 9), ("Dosya adı", "نام فایل", 25), ("Dakika", "زمان", 12), ("Süre", "مدت", 7),
    ("Başlık", "عنوان", 34), ("Özet", "خلاصه", 44), ("Neden seçildi", "چرا انتخاب شد", 32), ("Karar", "تصمیم", 13), ("Not", "یادداشت", 22),
]
ICERIK, SABIT_SAG = (6, 8), (9, 10)
RENK = {"uzun": "D9E7F5", "shorts": "FBE3D0"}
RENK_KOYU = {"uzun": "2F6F9F", "shorts": "C8682A"}
ZEMIN_TR, ZEMIN_DIYALOG = "F6F4EF", "FBFAF6"
INCE = Side(style="thin", color="DDD9D0")
KALIN = Side(style="medium", color="8A867C")
YAZI = "Tahoma"


def mmss(t: float) -> str:
    return f"{int(t) // 60:02}:{int(t) % 60:02}"


def bagla(kaynak: Path, hedef: Path) -> None:
    hedef.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.link(kaynak, hedef)
    except OSError:
        shutil.copy2(kaynak, hedef)


def satir_yuksekligi(metinler: list, genislikler: list) -> float:
    satirlar = max(sum(max(1, math.ceil(len(p) / (g * 0.95))) for p in m.split("\n")) for m, g in zip(metinler, genislikler))
    return max(34, satirlar * 16 + 8)


def basliklar(k: dict, dil: str) -> str:
    """Klip ismi (varsa) ve numarali iki baslik onerisi; ikincisi alternatif."""
    no = ("۱.", "۲.") if dil == "fa" else ("1.", "2.")
    satirlar = [k.get(f"isim_{dil}", "")] + [f"{n} {b[dil]}" for n, b in zip(no, k["basliklar"])]
    return "\n".join(s for s in satirlar if s)


def bant(ws, r: int, metin: str, zemin: str, yazi: str, boy: float) -> None:
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=len(KOLON))
    h = ws.cell(row=r, column=1, value=metin)
    h.fill = PatternFill("solid", fgColor=zemin)
    h.font = Font(name=YAZI, bold=True, color=yazi, size=11)
    h.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[r].height = boy


def main() -> None:
    d = Path(sys.argv[1])
    v = json.loads((d / "kesitler.json").read_text(encoding="utf-8"))
    kod = v["kod"]
    teslim = Path(__file__).parent.parent / "teslim" / kod
    for alt in ("uzun", "shorts"):
        if (teslim / alt).exists():
            shutil.rmtree(teslim / alt)  # yalnizca teslim baglantilari; asil dosyalar calisma/ altinda

    wb = Workbook()
    ws = wb.active
    ws.title = kod
    for c, (tr, fa, g) in enumerate(KOLON, 1):
        h = ws.cell(row=2, column=c, value=f"{tr}\n{fa}")
        h.font = Font(name=YAZI, bold=True, color="FFFFFF")
        h.fill = PatternFill("solid", fgColor="2B2B2B")
        h.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        ws.column_dimensions[get_column_letter(c)].width = g
    ws.row_dimensions[2].height = 40
    ws.freeze_panes = "A3"

    r = 3
    karar_hucreler, onceki = [], None
    icerik_gen = [KOLON[i][2] for i in range(ICERIK[0] - 1, ICERIK[1])]
    diyalog_gen = sum(icerik_gen)
    for k in v["kesitler"]:
        if k["tur"] != onceki:
            etiket = "UZUN KESİTLER · کلیپ‌های بلند" if k["tur"] == "uzun" else "SHORTS · شورتز"
            bant(ws, r, etiket, RENK_KOYU[k["tur"]], "FFFFFF", 24)
            r += 1
            onceki = k["tur"]
        tur = "Uzun\nبلند" if k["tur"] == "uzun" else "Shorts\nشورتز"
        if k["tur"] == "uzun":
            ad = f"{kod}-{k['id']}-{mmss(k['baslangic']).replace(':', '')}.mp4"
            bagla(d / "klipler" / f"{k['id']}.mp4", teslim / "uzun" / ad)
            dosyalar = [ad]
        else:
            yollar = sorted(
                [p for p in (d / "shorts").glob(f"{kod}-{k['id']}-*.mp4") if p.stem.endswith(("-takipli", "-karma"))],
                key=lambda p: p.stem.endswith("-karma"),
            )
            for y in yollar:
                bagla(y, teslim / "shorts" / y.name)
            dosyalar = [y.name for y in yollar]
        sol = [k["id"], tur, "\n".join(dosyalar), f"{mmss(k['baslangic'])} – {mmss(k['bitis'])}", mmss(k["sure"])]
        fa = [basliklar(k, "fa"), k["ozet_fa"], k["neden_fa"]]
        tr = [basliklar(k, "tr"), k["ozet"], k["neden"]]
        diyalog = bool(k.get("ceviri"))
        boy = 4 if diyalog else 2

        renk = PatternFill("solid", fgColor=RENK[k["tur"]])
        for c, deger in enumerate(sol, 1):
            ws.merge_cells(start_row=r, start_column=c, end_row=r + boy - 1, end_column=c)
            h = ws.cell(row=r, column=c, value=deger)
            h.fill = renk
            h.font = Font(name=YAZI, bold=c == 1, size=10)
            h.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        for c in range(SABIT_SAG[0], SABIT_SAG[1] + 1):
            ws.merge_cells(start_row=r, start_column=c, end_row=r + boy - 1, end_column=c)
            ws.cell(row=r, column=c).alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
        karar_hucreler.append(f"{get_column_letter(SABIT_SAG[0])}{r}")

        for i, (a, b) in enumerate(zip(fa, tr)):
            c = ICERIK[0] + i
            ust = ws.cell(row=r, column=c, value=a)
            ust.font = Font(name=YAZI, size=11, bold=i == 0)
            ust.alignment = Alignment(wrap_text=True, vertical="top", horizontal="right", readingOrder=2)
            alt = ws.cell(row=r + 1, column=c, value=b)
            alt.font = Font(name=YAZI, size=10, bold=i == 0, color="444444")
            alt.fill = PatternFill("solid", fgColor=ZEMIN_TR)
            alt.alignment = Alignment(wrap_text=True, vertical="top", horizontal="left")
        ws.row_dimensions[r].height = satir_yuksekligi(fa, icerik_gen)
        ws.row_dimensions[r + 1].height = satir_yuksekligi(tr, icerik_gen)

        if diyalog:
            metinler = ("دیالوگ: " + " · ".join(k["fa_satirlar"]), "Diyalog: " + " · ".join(k["ceviri"]))
            for j, metin in enumerate(metinler):
                rr = r + 2 + j
                ws.merge_cells(start_row=rr, start_column=ICERIK[0], end_row=rr, end_column=ICERIK[1])
                h = ws.cell(row=rr, column=ICERIK[0], value=metin)
                h.font = Font(name=YAZI, size=9.5, color="333333" if j == 0 else "555555")
                h.fill = PatternFill("solid", fgColor=ZEMIN_DIYALOG)
                h.alignment = Alignment(
                    wrap_text=True, vertical="top", horizontal="right" if j == 0 else "left", readingOrder=2 if j == 0 else 1
                )
                ws.row_dimensions[rr].height = satir_yuksekligi([metin], [diyalog_gen])

        for c in range(1, len(KOLON) + 1):
            for rr in range(r, r + boy):
                ws.cell(row=rr, column=c).border = Border(
                    top=KALIN if rr == r else INCE, bottom=KALIN if rr == r + boy - 1 else INCE, left=INCE, right=INCE
                )
        r += boy

    son = r - 1
    harf = get_column_letter(SABIT_SAG[0])
    alan = f"{harf}3:{harf}{son}"
    menu = DataValidation(type="list", formula1=f'"{ONAY},{DUZELT},{RET}"', allow_blank=True)
    ws.add_data_validation(menu)
    for hucre in karar_hucreler:
        menu.add(hucre)
    for metin, zemin in ((ONAY, "C9EBC9"), (DUZELT, "FCE8B2"), (RET, "F4C7C3")):
        ws.conditional_formatting.add(alan, CellIsRule(operator="equal", formula=[f'"{metin}"'], fill=PatternFill("solid", bgColor=zemin)))

    toplam = len(karar_hucreler)
    say = lambda x: f'COUNTIF({alan},"{x}")'
    durum = (
        f'="Toplam / مجموع: {toplam}   |   Onay / تأیید: "&{say(ONAY)}&"   |   Düzeltme / اصلاح: "&{say(DUZELT)}'
        f'&"   |   Ret / رد: "&{say(RET)}&"   |   Bekleyen / در انتظار: "&({toplam}-{say(ONAY)}-{say(DUZELT)}-{say(RET)})'
    )
    bant(ws, 1, durum, "EFECE4", "1D1D1B", 28)

    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True

    teslim.mkdir(parents=True, exist_ok=True)
    wb.save(teslim / f"{kod}-liste.xlsx")
    print(f"BITTI: {len(v['kesitler'])} kesit -> {teslim}")


if __name__ == "__main__":
    main()
