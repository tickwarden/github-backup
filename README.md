# GitHub hesap yedekleri — hosted runner sürümü

Bu sürüm GitHub-hosted Ubuntu 24.04 üzerinde çalışır; self-hosted runner gerekmez.

## İş akışı
1. Sentetik verilerle regresyon testleri.
2. Her hesap için bağımsız yedekleme + güvenlik taraması.
3. Yalnız kontrolden geçen çıktı için güvenli artifact checkpoint.
4. Ayrı teslim job'unda checkpoint indirme ve SHA-256 kontrolü.

**Yedekleme yalnız özel repoda başlar.** Public repoda özel kod, depo isimleri veya şifresiz ZIP yayımlanmaması için capture engellenir. Testler public repoda çalışabilir. Repo görünürlüğü workflow tarafından değiştirilmez.

Secrets: TICKWARDEN_BACKUP_TOKEN, IRONCREST_BACKUP_TOKEN, TICKWARDEN_BACKUP_PASSPHRASE, IRONCREST_BACKUP_PASSPHRASE. Parolalar en az 20 karakter. Mevcut secret'lar korunur.

Actions → GitHub hesap yedekleri → Run workflow. `plaintext_zip` varsayılan kapalıdır; açılırsa özel kod içeren şifresiz ZIP ayrıca bir gün saklanır. Şifreli 7z checkpoint yedi gün saklanır. Drive yüklemesi dahil değildir.

## Bulgular ve kısmi kapsam
Dosyalar ve tespit edilen bare Git depolarındaki çözülmüş Git nesneleri, mevcut token/parolayla tam eşleşme ve bazı gizli bilgi kalıpları için taranır. Bu bütün olası sırları/nested arşivleri tespit eden kapsamlı güvenlik garantisi değildir.

Bir repository biriminde bulgu varsa o deponun **tamamı** teslimden çıkarılır; bulgu bastırılmaz, Git geçmişi değiştirilmez. Diğer temiz birimler `PARTIAL` adıyla teslim edilir. SCAN-REPORT.json / COVERAGE.json bulgu kategorisini, repository birimini ve eşleşen yolun hash'ini içerir; eşleşen içerik/token/parola yer almaz. Örnek metin bile olsa manuel inceleme olmadan istisna tanınmaz.

Hesap metadata'sında veya eşlenemeyen bir alanda bulgu varsa tüm hesabın yayını engellenir. Hesaplar bağımsızdır; biri engellenince diğeri iptal edilmez. Tam yedek/restore garantisi verilmez. Kullanıcı hedefi kapsamı, tüm erişilebilir kuruluşların bağımsız tam yedeği anlamına gelmez. Eski inventory dosyaları dışlanan depoları anabilir; teslimin gerçek kapsamı DELIVERY-COVERAGE.json dosyasıdır.

## Yeniden deneme
Teslim kontrolü başarısızsa Re-run failed jobs mevcut güvenli checkpoint'i kullanır; yeniden capture gerekmez. Capture+scan başarısızsa GitHub-hosted disk kalıcı olmadığından yeniden veri toplamak gerekebilir. Kontrolden geçmemiş/withheld veri sadece yeniden deneme kolaylığı için artifact'e yüklenmez. Her aşamanın koşulsuz kalıcı tutulduğu iddia edilmez.

Ham loglar yayımlanmaz. İlerleme her 30 saniyede Actions loguna sayaç olarak yazılır; on dakika değişim yoksa uyarı verilir. Yedekleme komutu dört saatte durdurulur. 7z parolayı alt süreç argümanında kullandığından yalnız güvenilir, tek kiracılı hosted runner kullanılmalıdır. Symlink/özel dosyalar reddedilir. Şifresiz ZIP tüm Unix metadata'sını korumaz.

Eski self-hosted kullanım belgeleri ve yardımcı dosyalar bu sürüm için geçerli değildir; etkin workflow `.github/workflows/backup.yml` ve bu README'dir. Workflow çıkış yapmaz veya OAuth grant iptal etmez.
