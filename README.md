# GitHub Actions ile hesap yedekleme

Bu paket hazırlanmıştır; GitHub'a gönderilmemiş ve Actions üzerinde çalıştırılmamıştır.

## Kurulum
1. Güvendiğiniz **özel** bir repoya bu paketteki `.github/` ve `scripts/` dizinlerini ekleyin. Gizli `.github` dizinini atlamayın.
2. Repo → Settings → Secrets and variables → Actions altında şu secrets değerlerini oluşturun:
   - `TICKWARDEN_BACKUP_TOKEN`
   - `IRONCREST_BACKUP_TOKEN`
   - `TICKWARDEN_BACKUP_PASSPHRASE`
   - `IRONCREST_BACKUP_PASSPHRASE`
3. Token'ları hesapların kendisi üzerinden oluşturun; kapsamı yedeklenecek verilere göre sınırlayın. Özel depolar, Gist ve kuruluş verileri için gerekli okuma erişimi bulunmalı; gerekiyorsa SSO onayını verin. Fine-grained token'ların tüm Gist/kuruluş uç noktalarını kapsadığı varsayılmamalıdır. `GITHUB_TOKEN` iki hesabın tüm özel verileri için yeterli değildir. Token ve parolaları sohbete ya da repoya yazmayın. Parolalar en az 20 karakter, tercihen parola yöneticisinden üretilmiş olsun. Parolaları ayrıca güvenli yerde saklayın.
4. Actions → GitHub hesap yedekleri → Run workflow.
5. Başarılı job'un şifreli çıktısını workflow run sayfasının Artifacts bölümünden indirin. Saklama süresi 7 gündür; kalıcı saklama için ayrıca indirin.

## Davranış ve sınırlar
- İki hesap ayrı job'larda çalışır; biri hata verirse diğeri iptal edilmez. Aynı workflow'un eşzamanlı çalışmaları sıraya alınır.
- Hesap kimliği önceden doğrulanır. Yedekleme komutu 4 saatte sonlandırılır; job üst sınırı 330 dakikadır. Bu, kök ağ sorununu çözmez; süresiz beklemeyi engeller.
- Ekli `backup-org.sh` yüklediğiniz v4.0'ın değiştirilmemiş kopyasıdır. Kaynak SHA-256: `99423f34b0ac06874532637bc6640914399f595a05b2f62db5bba6d8e9e8b7ce`.
- `--strict` açık: uyarı/erişim hataları çalışmayı başarısız yapabilir; başarısız job'un kısmi arşivi yayımlanmaz. Kontrolü atlayarak yükleme yapılmaz.
- Ham loglar token içeren URL barındırabilir; konsola veya artifact'e gönderilmez ve job sonunda temizlenir. Tam runner yönetimi/kalıcı disk silme garantisi verilmez.
- Artifact yalnız şifreli `.gpg`, SHA-256 ve kapsam manifestini içerir. Şifresiz dosya yüklenmez.
- Şifre çözme ve tar okuma sınanır. Temel sızıntı kontrolü bilinen token/parola ve bazı anahtar kalıplarını tarar; **sıkıştırılmış Git nesneleri içindeki tüm geçmişi inceleyen kapsamlı güvenlik taraması değildir**. Tam güvenlik incelemesi veya geri yükleme testi yapıldığı iddia edilmez.
- Bu sürüm **kullanıcı hedeflerini** yedekler. Tüm erişilebilir kuruluşları ayrıca keşfedip her birini bağımsız yedekleyen bir orchestration değildir. Kuruluş üyelik kaydı, kuruluşların tamamının yedeği demek değildir.
- **Drive yüklemesi bu pakete eklenmedi.** Çıktı GitHub Actions artifact'i olarak tutulur. Arena'daki Drive bağlantısı GitHub runner'a aktarılmaz; Drive otomasyonu için ayrıca yetkilendirilmiş, güvenli bir kimlik akışı gerekir. Şimdilik artifact'i indirip güvenlik incelemesinden sonra Drive'a aktarın.
- Repo/gist silme, GitHub'a veri geri yazma veya OAuth grant iptali yoktur. Actions kendi run/artifact kayıtlarını oluşturur.
- Workflow action sürümleri commit SHA'larına, github-backup paketi sürüme sabitlenmiştir; apt ve transitif Python bağımlılıkları hash kilitli değildir. Sadece güvendiğiniz özel repo ve runner'da çalıştırın.

PHP/JS canlı ekran bu paketin parçası değildir; Actions durumunu Actions arayüzünden izleyin.
