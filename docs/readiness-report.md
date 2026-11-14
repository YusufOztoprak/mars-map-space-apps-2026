# Aşama 6 — geçici entegrasyon/test durum raporu

14 Kasım 2026. Bu dosya final kabul raporu değil; ekip için mevcut durum özetidir.
README, sunum veya diğer ekip üyelerinin dosyaları değiştirilmedi.

## Kanıtlanan davranış

Backend `79261e3` sürümünde gerçek Flask test client ile sentetik DEM üzerinde
başarılı rota, geçersiz istek, kapsam dışı nokta, yol yok ve preflight test edildi.
Sentetik grid üzerinde eğim hesabı, dik hücreden kaçınma, alternatif yol ve yol
yok kontrolü geçti. Sözleşme doğrulama yardımcıları da test edildi.
Son otomatik sonuç: **43 PASS, 4 FAIL, 6 SKIP**.
Tam kanıt: [test raporu](test-report.md), [pytest çıktısı](backend-test-output.txt).
Bu hazırlıkta kod değişmediği için testler tekrar çalıştırılmadı.

## Açık bulgular ve sahipleri

| Konu | Gereken işlem | Sorumlu |
| --- | --- | --- |
| Aynı hücrede tek konumlu LineString | Geçerli sonuç veya kontrollü hata; sonra yeniden test | Backend; doğrulama entegrasyon/test |
| Beklenmeyen hatada HTML 500 | Kararlı JSON hata yanıtı | Backend |
| CORS tüm origin'lere açık | Gerçek frontend portuna göre izin listesi | Backend + frontend |
| Sayısal string kabulü | Giriş türlerini ekipçe kararlaştırma; test/sözleşmeyi hizalama | Backend + frontend |
| Gerçek DEM bağlı değil | Veri ve projeksiyon bilgilerini teslim etme; yükleyiciye bağlama | Veri/içerik + backend |
| Sabit 28° eşik | Yapılandırılabilir prototip parametresini kararlaştırma | Backend |
| Frontend akışı test edilmedi | Kod/komut/port geldikten sonra Aşama 4 | Frontend; doğrulama entegrasyon/test |
| Coğrafi doğruluk kanıtlanmadı | Tile/DEM hizası, Mars metriği, NoData ve snap doğrulaması | Veri + backend; doğrulama entegrasyon/test |

## Sunum öncesi sıra

1. Frontend commit'i ve çalıştırma bilgileri alınır; [Aşama 4 listesi](frontend-checklist.md) uygulanır.
2. Backend bulguları ilgili geliştirici tarafından ele alınır; yeni kesin sürüm yeniden test edilir.
3. Gerçek DEM hazırsa [Aşama 5 planı](e2e-plan.md) çalıştırılır.
4. Demo için çalışan sürümler, kurulum komutları ve veri modu sabitlenir.
5. Test toplamları ve açık hatalar bu raporda güncellenir; ondan sonra final rapor hazırlanır.

## Sunumda kullanılabilecek mevcut ifade

“Sentetik yükseklik verisi üzerinde rota algoritması ve API için otomatik
kontroller çalıştırıldı. Frontend entegrasyonu ve gerçek Mars DEM doğrulaması
devam ediyor; dört API/sözleşme uyumsuzluğu raporlandı.”

Gerçek DEM kullanıldı, NASA güvenlik eşiği doğrulandı veya uygulama tamamen
test edildi ifadeleri şu an kanıtlanmıyor. DEM yetişmezse sentetik prototip
olarak sunma kararı ekipçe alınmalı; gerçek veri hedefi tamamlandı sayılmamalı.

## Git ve teslim durumu

Çalışma branch'i `entegrasyon-test`. Dosyalar henüz commit edilmedi.
Push, PR ve merge yapılmadı. Commit öncesi dosya listesi gösterilecek;
push için kullanıcının açık onayı beklenecek. Birleştirme ekip tarafından en son yapılacak.
