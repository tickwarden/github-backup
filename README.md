# GitHub hesap yedekleri

Actions → **GitHub hesap yedekleri → Run workflow** yeterlidir. Self-hosted runner veya private repo zorunlu değildir. Daha önce tanımlanan dört hesap token/parola secret'ı kullanılır.

`scripts/` altında yalnız iki dosya vardır:
- `backup-org.sh`: hesap verilerini toplar, parolalı 7z oluşturur.
- `verify.py`: arşivi açıp doğrular, dosyaları ve Git nesnelerini tarar; güvenli çıktıyı hazırlar.

İlerleme ve olay logları workflow içindedir; yardımcı betik gerekmez. Her 30 saniyede aşama, geçen süre, dosya sayısı, boyut, son log yazım yaşı gösterilir. Tanınan HTTP hata kodları ve retry/rate-limit olayları ayrıca yazılır. Bu olay sınıflandırması sezgiseldir; tüm API hatalarını tanıdığı iddia edilmez. Ham loglar, token/parola, içerik ve public loglarda özel depo isimleri gösterilmez.

Her hesabın yedekleme+tarama ve teslim kontrolü ayrı job'lardadır (toplam dört job). Bir hesabın hatası diğerini durdurmaz. Otomatik test job'u yoktur; `tests/` yalnız yerel regresyon testleri içindir.

Uyarı nedeniyle hemen durdurma modu kapalıdır. Toplama hata verirse bağımsız doğrulama, kullanılabilir bir 7z adayı olup olmadığına bakar. Güvenli çıktı yoksa o hesap başarısız raporlanır; bozuk/güvensiz veri başarılıymış gibi teslim edilmez.

Gizli bilgi kalıbı bulunan repository birimi bütünüyle dışarıda tutulur. Bulgu bastırılmaz, Git geçmişi değiştirilmez; kalan veri PARTIAL adıyla teslim edilir. Hesap metadata'sındaki bulgular tüm hesabın yayınını engeller. Bu tarama bütün olası sırları veya iç içe sıkıştırılmış formatları tespit eden bir garanti değildir. Tam kapsam ve restore doğrulaması yapılmış sayılmaz. Kullanıcı hedefi, erişilebilir tüm kuruluşların bağımsız tam yedeği demek değildir.

Şifreli 7z checkpoint yedi gün saklanır. Şifresiz ZIP isteğe bağlıdır; private repoda bir gün saklanır, public repoda uyarıyla atlanır. Public tarama raporunda özel repository birim adları hash olarak gösterilir. Drive yüklemesi dahil değildir.

Teslim job'undaki hata sonrası Re-run failed jobs güvenli checkpoint'i kullanabilir. Toplama+tarama aşamasında arşiv teslim edilememişse hosted runner diski kalıcı olmadığından yeniden toplamak gerekebilir. Ham/withheld veri sırf checkpoint için artifact'e yüklenmez.

Workflow çıkış yapmaz, OAuth grant iptal etmez ve repo görünürlüğünü değiştirmez. 7z parola argümanı kullandığından güvenilir, tek kiracılı hosted runner kullanılmalıdır. Symlink/özel dosyalar reddedilir. ZIP tüm Unix metadata'sını korumaz.
