# Actions logunda ilerleme

`.github/workflows/backup.yml` dosyasını değiştirin ve `scripts/run-with-progress.py` dosyasını repoya ekleyin. Diğer betikleri koruyun. Yeni bir workflow çalıştırın; mevcut çalışan job güncellenmez.

Özet bilgisi Summary yerine stdout/Actions adım loguna yazılır. Her 30 saniyede geçen süre, dosya sayısı, toplam boyut, son ham log yazımının yaşı ve gözlenen değişimsizlik süresi gösterilir. On dakika değişim gözlenmezse uyarı verilir; bu otomatik iptal veya kesin takılma teşhisi değildir. Dört saatlik yedekleme sınırı korunur. Ham log veya dosya isimleri yazılmaz.

Dosya sayısı ve boyut çalışma/çıktı dizinlerini kapsar; eksiksizlik ya da kurtarılabilirlik kanıtı değildir.
