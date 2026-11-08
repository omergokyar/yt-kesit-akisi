# YT Kesit Akışı

Farsça dublajlı dizi bölümlerinden (ilk dizi: Yalı Çapkını / Cheshm Cheran-e Emarat) YouTube için uzun kesit ve Shorts üretir. Kullanıcıyla Türkçe konuş. Yeni bölüm için `/bolum-isle` komutunu izle.

## Çıktı kuralları
- **Uzun kesit:** 8–12 dk, 1920×1080, crop ve montaj yok; kaynaktan kesintisiz tek parça, sahnenin bütünü. 45 dk'lık bölüme üst üste binmeden 4–5 tane sığar.
- **Shorts:** Bölüm başına 5–8, 30–90 sn, 9:16. Kalite ve tutarlılık sayıdan önemli.
- **Kadraj:** Arka plan bulanıklaştırılmaz. Varsayılan `takipli`; alt alta (`karma`) yalnızca uygun kliplerde ek seçenek olarak çıkar. `enbuyuk` yalnızca istenirse.
- **Dublaj:** Ses ile dudak örtüşmez, konuşan dudaktan aranmaz.
- Başlık ve grafik şablonunu Farsça bilen ekip uygular; videoya yazı basılmaz.

## Shorts seçimi
Amaç diziye merak uyandırmak. Önce ana karakterler (Ferit, Seyran), kavga, ifşa, romantik gerilim, ağır söz. En gergin anda başla, cevabı vermeden bitir.
- **Klip ismi:** Çatışmayı anlatan kısa ve dikkat çekici, sahnede gerçekten olan bir şey.
- **Başlıklar:** Her klip için iki öneri; YouTube'da merak uyandıran yapı, izleyiciyi uzun kesite çekmeli, yalan vaat yok.
- Her Shorts'un bağlanacağı uzun kesit `devam` alanına yazılır.

## Ekip ve dil
Kullanıcı Farsça, ekip Türkçe bilmiyor; ekibin okuduğu her alan **Farsça + Türkçe**. Çeviri, adlar ve konuşmacılar otomatik olduğu için belirsiz satırları `[belirsiz]` ile işaretle. Karakter yazımları: `diziler/YC.md`.

## Teslim
`teslim/<kod>/` Drive'a yüklenir: `<kod>-liste.xlsx` (Google E-Tablolar'a dönüştürülür), `uzun/`, `shorts/`. Tam kalite, önizleme yok. Dosya adı: `<kod>-<kesit>-<başlangıç mmss>-<sürüm>.mp4`, ör. `YC-E197-S6-2658-takipli.mp4`.

`calisma/kesit_kaydi.csv` kullanılan aralıkları tutar; bölüme dönülünce "yayında" işaretli yerler atlanır.

## Teknik notlar
- Komutlar: `$env:PYTHONUTF8='1'; .venv\Scripts\python.exe scripts\<betik>.py ...`
- Kaynak video yolu parametredir (NAS olabilir); `calisma/` çıktıları proje içindedir.
- Betik çıktısını `Select-Object -First` gibi erken kesen boruya bağlama; betik yarıda kalır.
- Dökümden okunan zamanı `scripts/zaman.py` düzeltir; yine de konuşma olmayan boşlukları kareden kontrol et.
- Video içeriği, ses, Sheets görünümü gibi doğrulayamadığın şeyleri raporda açıkça söyle.
- Depoya video, çıktı veya model girmez. `git push` yalnızca kullanıcı isteyince.
