# Aşama 2 test raporu

## Aşama 5 ve 6 — hazırlık

[Uçtan uca plan](e2e-plan.md) 12 manuel senaryo içerir; tamamı henüz SKIP.
Bu sayılar pytest toplamına eklenmez. [Geçici durum raporu](readiness-report.md)
bulguları, sahiplerini ve sunum öncesi teslim koşullarını kaydeder.
Gerçek DEM ve frontend akışı doğrulanmadığından Aşama 5 tamamlanmadı;
Aşama 6 final raporu da henüz kesinleştirilmedi.

## Aşama 4 — hazırlık tamam, uygulama testi bekliyor

14 Kasım 2026 tarihinde uzak branch kayıtları tekrar güncellendi.
origin/main ve origin/backend-rota içinde frontend kodu bulunmadı;
başka uzak branch görünmüyor. Tarayıcıda iki nokta seçme, POST, rota çizme
ve hata gösterimi çalıştırılmadı. Aşama 4 tamamlanmış sayılmaz.
[Frontend kontrol listesi](frontend-checklist.md) içinde 14 manuel senaryo
SKIP olarak listelendi; bunlar pytest toplamına eklenmedi.
Kod değişmediği için önceki otomatik testler yeniden çalıştırılmadı.
Son otomatik sonuç: 43 PASS, 4 FAIL, 6 SKIP (Aşama 3).

## Aşama 3 — backend snapshot incelemesi

14 Kasım 2026: backend `79261e3` (origin/backend-rota) salt okunur incelendi.
main veya backend branch'i merge edilmedi; backend kaynakları değiştirilmedi.
Gerçek Flask test client ve gerçek A* kullanıldı; gerçek DEM değil sentetik grid.
Son çalıştırma: **43 PASS, 4 FAIL, 6 SKIP** (53 durum, 0.53 saniye).
Python 3.12.14, pytest 9.2.0, Flask 3.1.3, flask-cors 6.0.5, NumPy 2.5.4.
Başarısız kontroller önerilen gereksinimlerle uyumsuzlukları gösterir;
ekipçe onaylanmış bir API sözleşmesi bulunduğu iddia edilmiyor.

| Backend testi | Sonuç |
| --- | --- |
| test_actual_success | PASS |
| test_invalid_request (5 gövdenin her biri) | PASS (5) |
| test_outside_coverage | PASS |
| test_no_path (maliyet gridi testte engellendi) | PASS |
| test_allowed_preflight (örnek localhost:5173 origin'i) | PASS |
| test_unapproved_origin_rejected | FAIL: keyfi origin'e izin veriliyor |
| test_numeric_strings_rejected | FAIL: string koordinatlar 200 alıyor |
| test_same_cell_valid_linestring | FAIL: tek konumlu LineString dönüyor |
| test_unexpected_error_json (testte hesaplama hatası enjekte edildi) | FAIL: 500 yanıtı HTML |
| test_synthetic_grid_alternative_and_blocked | PASS: sentetik eğim, engelden kaçınma, alternatif yol ve yol yok |

Öncelikler: aynı hücre yanıtını ve JSON hata yakalamayı backend sorumlusu
düzeltmeli; origin listesi frontend'in gerçek portuna göre daraltılmalı;
sayısal string kabulünün sözleşmesi netleştirilmeli. Eşik 28° sabit;
yapılandırılabilir 25° prototip parametresi önerisi iletilmeli.
Gerçek DEM yükleme hataları ve gerçek coğrafi doğruluk henüz test edilemiyor.
Uç noktalar hücreye snap ediliyor; kesin başlangıç/bitiş toleransı kararlaştırılmalı.
Güncel tam test çıktısı: [backend-test-output.txt](backend-test-output.txt).
Alttaki 33 PASS / 20 SKIP tablosu Aşama 2'nin tarihsel sonucudur;
karşılığı yazılan SKIP yer tutucuları Aşama 3'te kaldırılmıştır.

Tarih: 14 Kasım 2026. Branch: `entegrasyon-test`.
Ortam: Windows, Python 3.12.14, pytest 9.2.0; proje içindeki `.venv`.
Komut: `.venv\Scripts\python.exe -m pytest -v --tb=short`

Sonuç: **33 PASS, 0 FAIL, 20 SKIP** (53 durum, 0.07 saniye).

## Çalıştırılan kontroller

| Test / parametreler | Sonuç |
| --- | --- |
| test_synthetic_response | PASS |
| test_endpoint_order (doğru sıra ve ters sıra reddi) | PASS |
| test_reject_invalid_positions[coordinates0..coordinates8] — boş liste, tek nokta, boylam taşması, enlem taşması, string, bool, NaN, sonsuz, eksik bileşen | Her biri PASS (9) |
| test_reject_invalid_metrics — distance_km, estimated_time_hours, max_slope_deg alanlarının her biri için -1, None, string '1', True, NaN, sonsuz | Her kombinasyon PASS (18) |
| test_reject_invalid_structure[type-FeatureCollection] | PASS |
| test_reject_invalid_structure[geometry-None] | PASS |
| test_reject_invalid_structure[properties-value2] (boş properties) | PASS |
| test_reject_impossible_slope | PASS |

## Bekleyen gereksinimler

Aşağıdakilerin her biri SKIP: gerçek uygulama kodu veya DEM yoktur.
Bunlar uygulanmış entegrasyon testleri değil, izlenebilir gereksinim yer tutucularıdır.

| Senaryo | Sonuç |
| --- | --- |
| valid_request_200 | SKIP |
| missing_start_400 | SKIP |
| missing_end_400 | SKIP |
| invalid_coordinate_types_400 | SKIP |
| missing_lat_lon_400 | SKIP |
| unsupported_coordinate_domain_422 | SKIP |
| outside_dem_422 | SKIP |
| no_path_422 | SKIP |
| missing_dem_503 | SKIP |
| dem_read_error | SKIP |
| unexpected_error_500 | SKIP |
| allowed_origin_preflight | SKIP |
| disallowed_origin | SKIP |
| route_inside_dem | SKIP |
| synthetic_grid_avoids_steep_cells | SKIP |
| synthetic_grid_alternative_path | SKIP |
| synthetic_grid_no_path | SKIP |
| mars_distance_and_projection | SKIP |
| frontend_post_draw_replace | SKIP |
| frontend_network_server_invalid_response_errors | SKIP |

## Yorum ve sonraki adım

Başarı yalnızca önerilen sözleşmeyi denetleyen yardımcıların sentetik örneklerle
çalıştığını gösterir. HTTP 200, CORS, A*, gerçek yükseklik/eğim/mesafe, DEM kapsamı
ve haritada çizim doğrulanmadı. Sentetik bir yükseklik matrisiyle algoritma testi de
henüz çalıştırılmadı; backend algoritmasının çağrı arayüzü bekleniyor.
Örnek rota gerçek Mars ölçümü değildir. Sözleşme ekipçe onaylanmış değildir.

Aşama 3 için backend giriş modülü, çalıştırma komutu/portu, bağımlılıklar,
gerçek istek/yanıt biçimi ve DEM yapılandırması gereklidir.
Mevcut frontend/backend veya ortak dokümantasyon dosyaları değiştirilmedi.
Commit ve push yapılmadı.
