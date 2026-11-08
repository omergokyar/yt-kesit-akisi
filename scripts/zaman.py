"""Whisper kelime zamanlarindaki kopuk bas/son kelimeleri duzeltir.

Whisper bazen cumlenin ilk (veya son) kelimesini oncesindeki sessizligin kenarina yazar:
gercekte 16:07'de soylenen cumle 15:52'de basliyormus gibi gorunur. Bir segmentin basinda ya da
sonunda en fazla PARCA kelime, geri kalanindan BOSLUK saniyeden fazla ayriliyorsa o kelimeler
cumleye yapistirilir. Islem idempotenttir; ayni metne tekrar uygulanabilir.
"""
BOSLUK = 3.0
PARCA = 2
ARA = 0.05
MAKS_KELIME = 0.45


def _kaydir(kelimeler: list, fark: float) -> None:
    for k in kelimeler:
        k["start"] = round(k["start"] + fark, 2)
        k["end"] = round(k["end"] + fark, 2)


def duzelt(segmentler: list) -> int:
    """Segmentleri yerinde duzeltir, degisen segment sayisini dondurur."""
    degisen = 0
    for s in segmentler:
        w = s.get("words") or []
        if len(w) < 2:
            continue
        degisti = False
        for k in range(1, min(PARCA, len(w) - 1) + 1):
            bosluk = w[k]["start"] - w[k - 1]["end"]
            if bosluk >= BOSLUK:
                _kaydir(w[:k], bosluk - ARA)
                # Kopuk kelimenin suresi de sisirilmis olur; cumleye fazla erken baslatmasin.
                for x in w[:k]:
                    x["start"] = round(max(x["start"], x["end"] - MAKS_KELIME), 2)
                degisti = True
                break
        for k in range(len(w) - 1, max(len(w) - 1 - PARCA, 0), -1):
            bosluk = w[k]["start"] - w[k - 1]["end"]
            if bosluk >= BOSLUK:
                _kaydir(w[k:], -(bosluk - ARA))
                for x in w[k:]:
                    x["end"] = round(min(x["end"], x["start"] + MAKS_KELIME), 2)
                degisti = True
                break
        if degisti:
            s["start"], s["end"] = w[0]["start"], w[-1]["end"]
            degisen += 1
    return degisen
