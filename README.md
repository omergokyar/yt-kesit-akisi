# YT Kesit Akışı

Farsça dublajlı dizi bölümlerinden 8–12 dakikalık uzun kesitler ve dikey Shorts üretir; ekip için iki dilli Excel listesi ve Drive'a hazır klasör çıkarır.

## Gereksinimler
Windows, NVIDIA ekran kartı, git, [Claude Code](https://claude.com/claude-code). uv ve ffmpeg yoksa kurulum betiği kurar.

## Kurulum
```powershell
git clone https://github.com/omergokyar/yt-kesit-akisi.git
cd yt-kesit-akisi
.\kurulum.ps1
```
İlk kurulumda birkaç GB indirilir. Betik çalışmazsa önce `Set-ExecutionPolicy -Scope Process Bypass` çalıştırın.

## Kullanım
Klasörde `claude` komutuyla Claude Code'u açın ve yazın:
```
/bolum-isle "\\NAS\diziler\bolum-197.mp4" 197
```
Akış: döküm ve sahne tespiti → kesit seçimi → **sizin onayınız** → video üretimi → teslim klasörü.

Takılırsanız Claude'a "bu proje nasıl kullanılır?" diye sorun; kurallar `CLAUDE.md` içinde.

## Teslim
`teslim/<kod>/` klasörünü Drive'a yükleyin. `<kod>-liste.xlsx` dosyasını **Birlikte aç → Google E-Tablolar** ile açıp E-Tablolar olarak kaydedin ve klasörü ekiple paylaşın.

## Notlar
- Videolar, çıktılar ve modeller depoya girmez.
- Kullanılan aralıkların kaydı `calisma/kesit_kaydi.csv` dosyasındadır ve bilgisayara özeldir. Birden çok bilgisayar kullanıyorsanız bu dosyayı Drive'da yedekleyin.
- Karakter yazımları için `diziler/YC.md` dosyasını güncel tutun; yeni dizi için aynı biçimde dosya ekleyin.
