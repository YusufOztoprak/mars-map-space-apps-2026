# Entegrasyon notları — öneri, henüz uygulanmış sözleşme değil

Aşama 4 güncel durumu: uzak kayıtlar tekrar güncellendi; frontend henüz yok.
[Frontend kontrol listesi](frontend-checklist.md) hazır; gerçek tarayıcı
entegrasyonu frontend branch'i ve çalıştırma bilgileri geldiğinde yapılacak.

## Aşama 3 güncellemesi

`origin/backend-rota` üzerinde `79261e3` sürümü bulundu. `git fetch origin`
yalnızca uzak kayıtları güncelledi; branch değiştirilmedi veya merge yapılmadı.
`tests/test_backend_snapshot.py` bu sabit sürümün üç Python dosyasını geçici
klasöre okuyup gerçek Flask test client ile çalıştırır. Git geçmişi ve test
bağımlılıkları gereklidir; sürüm bulunamazsa test hata verir. Başka sürüm
test edilecekse REVISION açıkça güncellenmelidir.

Uygulanmış API: POST /route, GET /health, geliştirme portu 5000.
Başarı biçimi önerilen Feature/LineString ile uyumlu. Hata biçimi
`{"error":"açıklama"}`; önerilen iç içe code/message biçimi henüz uygulanmamış.
Mevcut biçim frontend ile netleştirilmeli; tek taraflı değiştirilmedi.
Backend sentetik 200x200, 25m/hücre grid kullanıyor. Coğrafi sınırlarla
bu metrik ölçeğin uyumu doğrulanmış değil. Gerçek DEM yüklenmiyor.
28° sabit eşik mevcut; 25° yapılandırılabilir prototip talebi henüz karşılanmıyor.
Astronot güvenlik standardı olarak sunulmamalı.

Aşağıdaki başlangıç notları Aşama 2 durumunu anlatır; güncel sonuçlar test raporundadır.

Ekip beş kişidir: backend/algoritma, frontend/harita, veri/içerik,
entegrasyon/test ve dokümantasyon/sunum. Bu çalışma yalnızca entegrasyon/test kapsamındadır.

## Mevcut durum

Backend, frontend ve DEM yerel repository'de yoktur. Endpoint veya CORS eklenmedi.
API sözleşmesi backend ve frontend sorumlularıyla netleştirilecektir.

## Önerilen API

`POST /route`, `Content-Type: application/json`

```json
{"start":{"lat":18.4,"lon":77.5},"end":{"lat":18.41,"lon":77.51}}
```

200: GeoJSON Feature, LineString ve en az iki `[longitude, latitude]` konumu.
properties: sonlu, negatif olmayan `distance_km`, `estimated_time_hours`,
`max_slope_deg` (0–90). Örnekler ve fixture değerleri hesaplanmış Mars rotası değildir.
Leaflet `latlng.lng` değeri istekte `lon` olur; GeoJSON sırası `[lon, lat]` olur.
Test yardımcısındaki -180..180 boylam kuralı bir öneridir; DEM 0..360 kullanıyorsa
dönüşüm ekipçe belirlenmelidir. Sayısal sınır kontrolü tek başına ters koordinatı yakalayamaz.

Önerilen hata biçimi: `{"error":{"code":"NO_PATH","message":"Rota bulunamadı"}}`.
400: eksik/bozuk giriş; 422: desteklenmeyen alan, DEM dışı veya rota yok;
503: DEM kullanılamıyor; 500: beklenmeyen hata. DEM okuma hatasının kodu,
hata nedenine göre backend sorumlusuyla netleştirilecektir.

## Backend geldiğinde

- Giriş modülü/app factory, bağımlılıklar, komut, port ve hata biçimini öğren.
- Gerçek Flask test client kullan; bu aşamada sahte Flask uygulaması oluşturma.
- Gerçek frontend origin'lerini belirle; yalnızca gereken origin'lere CORS izni ve OPTIONS kontrolü.
- Başlangıç/bitişin hücre merkezine taşınma kuralını ve toleransını belirle.
- DEM kapsamı, NoData, projeksiyon, piksel dönüşümü ve Mars yarıçapıyla mesafeyi doğrula.
- Küçük sentetik DEM ile dik hücreden kaçınma, alternatif yol ve yol yok testlerini yaz.
  Hücre aralığı/metre ve yükseklik/metre açık olmalı; 25° yapılandırılabilir prototip
  parametresidir, NASA güvenlik standardı değildir. Şimdilik algoritma testleri bekliyor.

## Frontend geldiğinde

İki nokta seçimi → POST → yanıt doğrulama → rota çizimi → eski rotayı temizleme;
mesafe/süre ve bağlantı, sunucu, rota yok, bozuk yanıt mesajlarını kontrol et.
CRS, tile grid ve DEM eşleşmesini ayrı doğrula. Tile görüntüsü yükseklik verisi değildir.
Verilen tile URL'si değiştirilmeden korunmalıdır; bu aşamada ağdan doğrulanmadı:

```text
https://trek.nasa.gov/tiles/Mars/EQ/JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0_lon0_first_dd/1.0.0//default/default028mm/{z}/{y}/{x}.png
```

## Çalıştırma ve sınırlar

`python -m pip install -r requirements-test.txt`

`python -m pytest -v`

PASS yalnızca test yardımcıları ve sentetik sözleşme örneği için geçerlidir.
SKIP gerçek uygulama davranışının doğrulanmadığını gösterir. Bekleyen testlerin skip
işareti kaldırılmadan önce gerçek uygulamaya bağlı assertion'lar yazılmalıdır.
DEM dosyalarını Git'e ekleme; mevcut .gitignore TIFF dosyalarını dışlamıyor.
