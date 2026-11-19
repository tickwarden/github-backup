# Bölünmüş yedekleme ve tekrar toplama olmadan teşhis

## Gereklilik — önce okuyun
Bu sürüm GitHub-hosted ubuntu runner DEĞİL; size ait kalıcı diskli, yalnız bu özel/güvenilir repo tarafından kullanılan Linux x64 self-hosted runner gerektirir. GitHub Settings → Actions → Runners üzerinden kurun. **Yalnız bir runner'a `private-backup` etiketi verin.** Bütün job'lar aynı makine ve aynı kullanıcı HOME dizininde çalışmalıdır. Bu runner'ı güvenilmeyen PR kodları veya başka kullanıcılarla paylaşmayın. Boş disk kapasitesini takip edin.

Runner PATH üzerinde python3, github-backup==0.67.0, py7zr==1.0.0, git, git-lfs, 7z, gh, curl, jq, rsync bulunmalı. Python paketlerini bir sanal ortama kurup runner servisinin PATH'ine bu ortamın bin dizinini ekleyin. Mevcut dört hesap token/parola secret'ı korunur. Parolalar en az 20 karakter olmalı.

## Kurulum
Tüm `.github/` ve `scripts/` dosyalarını repoda güncelleyin. Yeni workflow başlatın; ilk çalıştırmada capture_id boş olmalı. `plaintext_zip` isteğe bağlıdır.

## Ayrı job'lar
Her hesap için capture → verify → publish olmak üzere toplam 6 job vardır. Bir hesabın başarısızlığı diğer hesabın yayınını engellemez. Capture bir kez başarılıysa yerel CAPTURE_OK işareti yazılır. Verify hatası capture verisini silmez. Kontrolü geçmeyen arşiv, raw log veya repository verisi artifact olarak yüklenmez.

Veriler `$HOME/.private-github-backups/OWNER_REPO/CAPTURE_ID/ACCOUNT` altında kalır. Yerel SCAN-FINDING.json kalıbın kategorisini ve göreli dosya yolunu içerir; eşleşen içerik/parola/token yoktur. Bu rapor özel disk üzerinde elle incelenmelidir. Konsola sadece kategori yazılır. Bu rapor tüm bulguların listesi değildir; ilk kalıp eşleşmesini gösterir. İçeriklerin tamamını sohbet/loga taşımayın.

## Hata sonrası tekrar
- Kod değişmediyse Re-run failed jobs: capture job'u yeniden çalışmadan verify tekrar çalışır.
- Teşhis kodunu güncellediyseniz **Run workflow** ile yeni run başlatın ve `capture_id` alanına eski capture'ın sayısal run ID'sini yazın. Başarılı capture aynı makinede bulunursa yeniden toplama yapılmaz.
- Önceki GitHub-hosted run'ın temizlenmiş dosyalarını bu yöntem geri getiremez. İlk kalıcı capture bir defaya mahsus tekrar alınmalıdır.
- Bilinen token/parola ve kalıp taraması engelleri kaldırılmaz. CREDENTIAL_PATTERN_FOUND gerçek anahtar veya örnek metin olabilir; inceleme olmadan otomatik istisna verilmez. Bu paket iş akışını düzeltir; gerçek veri bulgusunun çözüldüğünü iddia etmez.

## Gizlilik ve sınırlar
Raw loglar ve doğrulanmamış yedekler yerelde saklanır, otomatik silinmez. Yetkili kullanıcı disk temizliği ve saklama politikasından sorumludur. Diskte bu veriler şifresiz çalışma kopyaları da içerebilir; disk şifrelemesi ve özel kullanıcı hesabı kullanın. GitHub artifact'leri yalnız verify başarılıysa yayımlanır; şifreli 7z 7 gün, isteğe bağlı şifresiz ZIP 1 gün saklanır. Drive otomasyonu yoktur. Tam Git geçmişi secret taraması, tam erişilebilir kuruluş kapsamı veya restore doğrulaması iddiası yoktur. Links/özel dosyalar reddedilir.

Sözdizimi kontrolleri yapıldı; bu yeni workflow gerçek self-hosted runner üzerinde test edilmedi. İlk çalıştırmayı izleyin. Repo/GitHub verisi silme veya OAuth grant iptali yoktur.
