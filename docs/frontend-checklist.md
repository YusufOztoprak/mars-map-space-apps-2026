# Aşama 4 — frontend entegrasyon kontrol listesi

14 Kasım 2026: `git fetch origin` sonrası origin/main ve origin/backend-rota
ağaçları kontrol edildi. Frontend dosyası veya frontend branch'i bulunamadı.
Durum: BEKLİYOR; tarayıcı testi yapılmadı. Frontend kodu oluşturulmadı veya değiştirilmedi.

## Frontend sorumlusundan gereken bilgiler

- Push edilmiş branch/commit ve frontend giriş dosyası.
- Kurulum/çalıştırma komutu, port, backend URL ayarının yeri.
- Leaflet ve tile yapılandırması; harita ile DEM koordinat eşleşmesi.

## Uygulama geldiğinde çalıştırılacak senaryolar

Her senaryoda beklenen ve gözlenen davranış, test edilen frontend/backend commit'leri
ve PASS/FAIL/SKIP kaydedilecek. Şimdilik aşağıdaki her satır SKIP (frontend yok).

| Senaryo | Beklenen davranış | Durum |
| --- | --- | --- |
| Başlangıç seçimi | İlk tıklama başlangıcı seçer; erken istek gönderilmez | SKIP |
| Bitiş seçimi | İkinci tıklama bitişi seçer ve istek gönderir | SKIP |
| İstek biçimi | POST /route, application/json; start/end içinde sayısal lat/lon; Leaflet lng → lon | SKIP |
| Başarılı yanıt | Feature/LineString doğrulanır, [lon,lat] sırası korunarak rota çizilir | SKIP |
| Yeni rota | Önceki çizim uygun biçimde temizlenir; eski istek yeni rotanın üstüne yazmaz | SKIP |
| Rota bilgisi | distance_km ve estimated_time_hours doğru birimlerle gösterilir | SKIP |
| Bağlantı yok | Anlaşılır hata gösterilir; tekrar deneme mümkün olur | SKIP |
| 400/422 | Geçersiz nokta, kapsam dışı veya rota yok açıklaması gösterilir | SKIP |
| 500/503 | Uygulama kilitlenmez; JSON veya HTML hata güvenle ele alınır | SKIP |
| Bozuk başarı yanıtı | Geçersiz geometri, NaN, eksik properties veya tek nokta çizilmez | SKIP |
| CORS/preflight | Gerçek frontend origin'i ile OPTIONS ve POST tarayıcıda başarılıdır | SKIP |
| Harita koordinatları | EPSG4326, tile grid ve tıklama konumu ayrı ayrı doğrulanır | SKIP |
| Tile URL | Verilen çift slash ve {z}/{y}/{x} sırası korunur | SKIP |
| Sentetik veri bildirimi | DEM gerçek değilse kullanıcıya/sunuma gerçek Mars hesabı olarak aktarılmaz | SKIP |

## Mevcut backend ile dikkat edilecekler

İncelenen sürüm: `79261e3`, geliştirme portu 5000, POST /route.
Hata gövdesi `{"error":"açıklama"}`; iç içe code/message kullanılmıyor.
Aynı hücredeki noktalar tek koordinatlı LineString üretiyor; frontend bunu çizmemeli.
Beklenmeyen hesaplama hatası HTML 500 döndürüyor. CORS tüm origin'lere açık;
gerçek frontend portu öğrenilince backend sorumlusu izin listesini daraltmalı.
Başlangıç/bitiş hücreye snap ediliyor; işaretçi ve rota uçları için tolerans
kararlaştırılmalı. Gerçek DEM ve coğrafi doğruluk Aşama 5'in ayrıca doğrulanacak konularıdır.

Frontend sorumlusunun kodu yeniden yazılmayacak. Uyumsuzluklar raporlanacak;
backend/frontend üzerinde değişiklik gerekirse önce nedeni açıklanacak.
