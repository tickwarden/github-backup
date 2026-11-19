# GitHub Actions: parolalı 7z + isteğe bağlı şifresiz ZIP

Paketin tüm dosyalarını, gizli `.github` dizini dahil, güvendiğiniz özel repoya ekleyin. Eski `scripts/plaintext-zip.py` artık kullanılmıyor.

## Secrets
- TICKWARDEN_BACKUP_TOKEN
- IRONCREST_BACKUP_TOKEN
- TICKWARDEN_BACKUP_PASSPHRASE
- IRONCREST_BACKUP_PASSPHRASE

Mevcut parola secret'ları aynen kullanılır. En az 20 karakter; rastgele ASCII parola tercih edin. Token doğru hesaba ve gereken okuma erişimlerine sahip olmalı. GITHUB_TOKEN hesapların tüm özel verilerinin yerine geçmez. Parolaları ayrıca güvenli saklayın.

Actions → GitHub hesap yedekleri → Run workflow. Şifresiz ZIP de isterseniz `plaintext_zip` kutusunu açın. Yeni çalıştırma gerekir.

Şifreli çıktı artık `.7z`; 7z arşiv başlık şifreleme (`-mhe=on`) kullanılır. GPG üretim/doğrulaması kullanılmaz; eski GPG arşivleri dönüştürülmez.

Şifreli artifact 7 gün, isteğe bağlı şifresiz ZIP artifact'i 1 gün saklanır. ZIP özel kodları parolasız içerir. Drive yüklemesi dahil değildir.

Her hesap ayrı job; stdout/Actions loguna 30 saniyede bir güvenli sayaçlar yazılır. Ham günlükler yayımlanmaz. 10 dakika değişim yoksa uyarı; yedekleme üst sınırı 4 saat. Başarısız çalışma ya da kontrol artifact yayınını engeller.

7z bütünlük testi, şifreyle okuma ve temel token/parola/anahtar kalıbı taraması yapılır. Bu, sıkıştırılmış Git nesnelerindeki tüm geçmişi inceleyen tam gizli bilgi taraması DEĞİLDİR. Restore veya tam kapsam doğrulaması yoktur. Yalnız kullanıcı hedefleri; erişilebilir tüm kuruluşların ayrı tam yedeği değildir.

Doğrulama geçici yerel şifresiz dosyalar açar. Symlink/özel dosya desteklenmez; güvenli ZIP dönüşümü için reddedilir. ZIP tüm Unix metadata özelliklerini korumaz. Geçici dosyalar iş bitiminde temizlenir; güvenli fiziksel silme garantisi yoktur.

7z CLI parolayı alt sürecin argümanında kullanır; ham komutları/logları yayımlamayın. Yalnız GitHub-hosted geçici runner ve güvenilir özel repo kullanın; paylaşılan self-hosted runner için uygun değildir.

GitHub üzerinde henüz çalıştırılmadı. Gömülü backup-org.sh v4.0 değiştirilmemiştir. İşlemler GitHub verisini silmez/geri yazmaz, OAuth grant iptali yapmaz.
