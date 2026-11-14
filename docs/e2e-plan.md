# Aşama 5 — uçtan uca doğrulama planı

Durum: HAZIRLIK TAMAM, ÇALIŞTIRMA BEKLİYOR. 14 Kasım 2026.
Frontend ve gerçek DEM mevcut yerel çalışma ağacında yok. Aşağıdaki senaryolar
çalıştırılmadı; örnek koordinatlardan gerçek DEM kapsamı varsayılmadı.

## Başlama koşulları

- Frontend ve backend için test edilecek kesin commit'ler, komutlar ve portlar kayıtlı.
- Aşama 4 temel tarayıcı akışı doğrulanmış; backend bulguları yeniden değerlendirilmiş.
- Veri sorumlusundan DEM yolu, kaynak bilgisi, CRS, affine dönüşüm, kapsam,
  yükseklik birimi, piksel çözünürlüğü ve NoData bilgisi alınmış.
- Backend'in sentetik veri yerine bu dosyayı gerçekten yüklediği doğrulanmış.
- Boylam konvansiyonu, Mars koordinat sistemi, metrik dönüşüm ve rota ucu
  snap toleransı kararlaştırılmış. EPSG4326 tek başına Mars uyumunun kanıtı değil.
- Eğim eşiği ve toleranslar kaydedilmiş; 25° yalnızca önerilen prototip
  parametresi, NASA güvenlik standardı değil. Mevcut kod eşiği 28°.

## Senaryolar ve kabul kriterleri

Noktalar gerçek DEM incelendikten sonra seçilecek; keyfi örnek koordinatlar kullanılmayacak.

| ID | Senaryo | Kabul kriteri | Durum |
| --- | --- | --- | --- |
| E01 | Kapsam içi kısa rota | Gerçek POST 200; geçerli LineString ve haritada eşleşen çizim; sonlu metrikler | SKIP |
| E02 | Kapsam içi uzun rota | Başlangıç/bitiş snap toleransında; tüm hücreler kapsam içinde; süre kaydedilmiş | SKIP |
| E03 | Dik alan çevresinde rota | Bağımsız DEM örneklemesinde eşik üstü/NoData hücre geçilmez; alternatif varsa bulunur | SKIP |
| E04 | Geçilebilir yol yok | Uygun hata durumu ve anlaşılır mesaj; yanıltıcı düz çizgi çizilmez | SKIP |
| E05 | DEM dışı nokta | 422 ve açıklayıcı hata; harita çalışmaya devam eder | SKIP |
| E06 | Aynı nokta veya hücre | Kararlaştırılmış davranış; tek konumlu LineString başarı olarak çizilmez | SKIP |
| E07 | DEM sınırı ve NoData | İndeks taşması yok; NoData engel kabul edilir; sessizce sahte yükseklik üretilmez | SKIP |
| E08 | Backend kapalı / hesaplama hatası | Bağlantı veya 500 hatası kullanıcıya gösterilir; tekrar denenebilir | SKIP |
| E09 | DEM yok / bozuk | Kontrollü hata; gerçek veri varmış gibi başarı dönmez | SKIP |
| E10 | Art arda rota istekleri | Son seçime ait rota görünür; eski rota ve gecikmiş yanıt karışmaz | SKIP |
| E11 | Tile ve DEM hizası | Bilinen referans noktaları doğru hücrelerle eşleşir; CRS/grid ayrı doğrulanır | SKIP |
| E12 | Mesafe, süre ve eğim | Mesafe Mars metriği/DEM çözünürlüğüyle bağımsız kontrol edilir; zaman modeli ve varsayımlar açıklanır | SKIP |

Gerçek arazide E03/E04 için uygun nokta bulunamazsa sonuç SKIP ve neden olarak
veri kısıtı yazılır; sentetik algoritma testleri ayrıca raporlanır.
Performans için önceden kararlaştırılmış hedef yok: süre ölçülecek, keyfi bir
eşik kullanılarak PASS iddia edilmeyecek. Snap ve mesafe toleransları çözünürlükten
türetilip test öncesinde kaydedilecek. Backend'in kendi path_stats fonksiyonunu
tekrar çağırmak bağımsız metrik doğrulama sayılmayacak.

## Her çalıştırmada kaydedilecek kanıt

- Senaryo ID, tarih, frontend/backend commit, DEM dosya adı ve SHA-256.
- Gerçek başlangıç/bitiş koordinatları, boylam konvansiyonu ve eşik.
- İstek, HTTP kodu, yanıt, geçen süre, ekran görüntüsü.
- Beklenen/gözlenen davranış, PASS/FAIL/SKIP, hata için yeniden üretme adımları.
- Kanıt dosyaları küçük tutulacak; DEM veya büyük ekran kayıtları Git'e eklenmeyecek.

## Bitirme koşulu

Kritik akışta açık hata kalmamalı; çalıştırılmayan her senaryo ve sınırlama
açıklanmalı. Sentetik modda demo yapılırsa bu açıkça belirtilmeli ve gerçek
DEM ile uçtan uca doğrulama tamamlandı denmemeli.
