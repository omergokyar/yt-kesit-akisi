---
name: bolum-isle
description: Bir dizi bölümünden uzun kesit ve dikey Shorts üretir, Drive'a hazır teslim klasörünü ve Excel listesini çıkarır. Yeni bölüm işlenmek istendiğinde kullan.
argument-hint: "<video yolu> <bölüm no> [dizi kodu, varsayılan YC]"
---

Argümanlar: $ARGUMENTS

`CLAUDE.md` kurallarına uy. Kod: `<dizi>-E<bölüm>` (ör. `YC-E197`), klasör: `calisma/ep<bölüm>`.

## 1. Hazırlık
Video yolunu ve süresini `ffprobe` ile doğrula. `calisma/kesit_kaydi.csv` içinde bu kodun satırları varsa durumlarını oku; "yayında" olan aralıkları tekrar seçme.

## 2. Döküm ve sahne (arka planda, birlikte)
```powershell
$env:PYTHONUTF8='1'; .venv\Scripts\python.exe scripts\transcribe.py "<video>" calisma\ep<no>
$env:PYTHONUTF8='1'; .venv\Scripts\python.exe scripts\scenes.py "<video>" calisma\ep<no>
```

## 3. Seçim
1. `transcript.compact.txt` dosyasını tamamen oku. Konuşmasız uzun boşlukların içeriğine kareden bak.
2. `diziler/<dizi>.md` yazımlarını kullan.
3. Uzun kesitleri ve Shorts'ları `calisma\ep<no>\kesitler.taslak.json` dosyasına yaz:
```json
{"bolum": "Dizi - 197. Bölüm", "kod": "YC-E197", "kesitler": [
 {"id": "U1", "tur": "uzun", "ilk_satir": 1, "son_satir": 137,
  "ozet": "", "ozet_fa": "", "neden": "", "neden_fa": "", "baglam": "", "baglam_fa": "",
  "basliklar": [{"tr": "", "fa": ""}, {"tr": "", "fa": ""}]},
 {"id": "S1", "tur": "shorts", "ilk_satir": 303, "son_satir": 323, "devam": "U2",
  "isim_tr": "", "isim_fa": "", "ozet": "", "ozet_fa": "", "neden": "", "neden_fa": "", "baglam": "", "baglam_fa": "",
  "basliklar": [{"tr": "", "fa": ""}, {"tr": "", "fa": ""}],
  "ceviri": ["Türkçe diyalog satırları"]}
]}
```
`ilk_satir` ve `son_satir`, `transcript.compact.txt` satır numaralarıdır. Konuşmasız açılış veya bitiş için isteğe bağlı `baslangic_hedef` ve `bitis_hedef` (saniye) kullanılır.

## 4. Sınırlar ve onay
```powershell
$env:PYTHONUTF8='1'; .venv\Scripts\python.exe scripts\kesit_sinirla.py calisma\ep<no>
```
Süre uyarılarını gider. **Üretime geçmeden önce kesit listesini (dakika, süre, isim, neden) kullanıcıya göster ve onay al.**

## 5. Üretim (arka planda)
```powershell
$env:PYTHONUTF8='1'; .venv\Scripts\python.exe scripts\klip_cikar.py "<video>" calisma\ep<no>
$env:PYTHONUTF8='1'; .venv\Scripts\python.exe scripts\dikey.py calisma\ep<no>
```
Her klibin başından, ortasından ve sonundan kareye bak; yanlış sahne, logo, dizi jeneriği veya bozuk kadraj varsa düzelt.

## 6. Teslim
```powershell
$env:PYTHONUTF8='1'; .venv\Scripts\python.exe scripts\kayit_guncelle.py calisma\ep<no>
$env:PYTHONUTF8='1'; .venv\Scripts\python.exe scripts\teslim_hazirla.py calisma\ep<no>
```

## 7. Rapor
Teslim klasörünü, kesit tablosunu, ekibin kontrol etmesi gereken belirsiz yerleri ve doğrulayamadıklarını (ses, hareket) yaz. Drive'a yükleme adımını kullanıcıya hatırlat.
