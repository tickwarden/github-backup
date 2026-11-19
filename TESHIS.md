# Güvenli hata teşhisi

Repoda yalnız `scripts/verify.py` dosyasını değiştirin ve değişikliğin bulunduğu commit için YENİ workflow çalıştırın. Eski run üzerinde Re-run jobs, eski commit'i kullandığından değişikliği almaz.

VERIFY_STAGE satırları kontrol aşamasını, hata satırı sabit kodu gösterir. Ham dosya adı, token, parola, exception metni yazılmaz.

KNOWN_CREDENTIAL_FOUND: token/parola ile tam eşleşme bulundu. CREDENTIAL_PATTERN_FOUND: token veya özel anahtar kalıbı bulundu; gerçek sızıntı mı örnek metin mi ayrıca incelenmeli. LINK_NOT_SUPPORTED: symlink/bağlantı bulundu. LIBRARY_OR_IO_FAILURE: şifre çözme/kütüphane/disk gibi bir hata; aşama ve tür sonraki teşhisi yönlendirir.

Hiçbir güvenlik kontrolü kaldırılmadı. Hatalı veriler yüklenmez. Bu paket önceki hatanın kök nedenini giderdiği iddiasında değildir.
