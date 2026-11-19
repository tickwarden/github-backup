# İsteğe bağlı şifresiz ZIP

Run workflow ekranında `plaintext_zip` kutusunu işaretleyin. Varsayılan kapalıdır. Şifreli GPG her zaman korunur. Şifresiz ZIP ayrı UNENCRYPTED artifact olarak 1 gün saklanır; indirdikten sonra güvenli bir yerde tutun. Parolasız açılır ve özel kaynak kodunu açığa çıkarabilir. Drive yüklemesi eklenmemiştir.

Önce var olan doğrulama ve temel gizli bilgi taraması geçmelidir. Tam Git geçmişi gizli bilgi taraması veya geri yükleme testi değildir. Bulgu nedeniyle engellenen veri kontrol atlanarak yayımlanmaz.

ZIP güvenli yol/çakışma denetimi ve CRC kontrolüyle oluşturulur; symlink, hardlink veya özel dosya varsa eksik bir ZIP üretmek yerine işlem başarısız olur. Böyle bir veri setinde şifreli tar tercih edilmelidir. ZIP tüm Unix metadata özelliklerini korumaz.

Güncel paketin tüm dosyalarını, gizli .github dizini dahil repoya ekleyin. Yeni çalıştırma gerekir; mevcut run değişmez. Paket hazırlandı; GitHub üzerinde denenmedi.
