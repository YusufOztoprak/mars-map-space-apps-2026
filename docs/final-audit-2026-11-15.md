# Mars Explorer — son bilimsel ve teknik denetim

Tarih: 15 Kasım 2026, Europe/Istanbul. Çalışma kopyası: `C:/Projects/mars-map-space-apps-2026-explorer`; yerel branch: `veri-icerik`. Kullanıcının ZIP'indeki mimari korundu. Önceki repo, `main`, dış başvuru formu ve ekip üyelerinin branch'leri değiştirilmedi. Bu build henüz upstream'e gönderilmedi.

## A. Yapılan düzeltmeler

| Bulgu | Düzeltme | Dosyalar |
|---|---|---|
| MOLA için 1200 km ve ±87° kısıtı; çok büyük arama penceresinin reddedilmesi | Explorer mesafe sınırı kaldırıldı. Küresel arama en fazla 80.000 düğüme uyarlanıyor; dönen adayın aradaki yerel MOLA hücreleri ve çapraz komşuları denetleniyor. Dik/eksik hücreye rastlayan kaba kenarlar yeniden aranıyor. | `backend/explorer.py`, `backend/tests/test_explorer.py` |
| Uzun rotalarda tüm harita için tek ortalama enlem katsayısı kullanılması | MOLA kenar maliyetleri ve A* kestirimi Mars küresindeki büyük çember mesafesine bağlandı. Bağımsız Dijkstra referansı ile maliyet doğrulandı. Yerel API davranışı korundu. | `backend/routing.py`, `backend/explorer.py`, `backend/tests/test_final_audit.py` |
| Rota uçlarının yalnızca grid merkezlerine ulaşması | Dönüş geometrisi tam seçilen koordinatlara bağlanıyor. Bağlantılar da aynı DEM'den örnekleniyor; eğimi geçersiz bağlantı kabul edilmiyor. Arayüzdeki sapma artık “Search grid offset” olarak adlandırılıyor. | `backend/explorer.py`, `frontend/explorer.js` |
| Yakın görünümde gri detayların arasından renkli kaba görüntü çıkması; çok sayıda bölgesel dikdörtgenin üst üste binmesi | Uzak Viking görünümü renkli kalıyor. Yakında kaba arka plan da griye geçiyor. Bölgesel görüntü, görünümün tamamını kapsadığında ve gerçekten daha ayrıntılı olduğunda seçiliyor. Seyrek küresel HiRISE yalnızca çok yakın zoom'da etkinleşiyor. | `frontend/explorer.js`, `tests/explorer-policy.cjs` |
| NASA'nın küresel HiRISE WMTS tanımında z12–17 için z11 matris boyutlarının tekrarlanması | NASA'nın yönlendirdiği yayıncı MapServer LOD kaydı, Mars koordinat sistemi ve tile başlangıcı doğrulanarak kullanılıyor. En ince sunulan piksel yaklaşık 0,16 m; bu, her yerde aynı doğal görüntü çözünürlüğü olduğu anlamına gelmiyor. Dört başka tutarsız mozaik devre dışı bırakıldı. | `scripts/verify_explorer_sources.py`, `data/explorer/imagery.json` |
| Yükseklik legend uçlarının yüklenen DEM'in gerçek uçları olmaması | Yüklenen MOLA rasterinden **−8177 m / +21171 m** hesaplandı ve renk skalasının uçlarına bağlandı. Çok renkli geçişler ve ayrı hillshade korundu; jeoloji birim renkleriyle karıştırılmıyor. | `backend/explorer.py`, sayısal raster/legend testleri |
| Hatalı düz liste biçimindeki yükseklik sorgusunun sunucu hatası üretebilmesi | Sonlu, sayısal, iki bileşenli koordinat çiftleri zorunlu; bozuk gövdeler 400 alıyor. | `backend/explorer.py`, `backend/tests/test_final_audit.py` |
| Eski belgelerde 1200 km sınırı, eski kaynak sayısı ve kesin “safest” ifadesi | Güncel yöntem, sınırlar, kaynaklar, yapay zekâ kullanımı ve gönderim taslağı düzeltildi. | `README.md`, `data_sources.md`, `ai_usage.md`, `docs/explorer-data.md`, `docs/submission.md` |

## B. Katmanlar ve veri kapsamı

Buradaki “sayısal/servis doğrulandı”, dosyanın/API'nin gerçekten çalıştırıldığını belirtir; son sürümün tarayıcıda görsel olarak kabul edildiği anlamına gelmez. Son görsel kabul durumu G bölümündedir.

| Katman | Doğrulanan davranış | Eksik veya sınırlı kısım |
|---|---|---|
| Yüzey görüntüsü | 77 etkin mozaik tanımı, dört reddedilen matris kaydı. Sekiz temsili canlı tile isteği: HTTP 200, açılabilir görüntü, CORS `*`. Uzak/orta/yakın seçim politikası altı otomatik testle kontrol edildi. | Bütün mozaiklerin her pikseli taranmadı. Gerçek kaynakta dikiş, pozlama farkı veya veri boşluğu kalabilir. |
| Yükseklik | Gerçek MOLA/CTX/HiRISE sayısal DEM. Nokta, raster pikseli ve legend ilişkisi; ayrıca CTX projeksiyonu bağımsız GDAL dönüşümüyle doğrulandı. Birim metre; referans Mars areoidi. | Küresel aktif MOLA yaklaşık 3,7 km/cell; global 463 m sayısal DEM kullanılmıyor. |
| Fiziki rölyef | Aynı yükseklik renkleri ve DEM'den türetilen hillshade. Tile sınırında türev için halo örneklemesi kullanılıyor. | Gölgelendirmenin parlaklığı yükselti değeri değildir. |
| Eğim | Derece; aynı analiz DEM'inin gradyanı. 15–20° uyarı; >20° prototip dışlama kuralı. | 20° bilimsel olarak doğrulanmış astronot emniyet sınırı değildir. Gerçek küçük engeller çözülemeyebilir. |
| Pürüzlülük | Metre; merkez yüksekliğin dört komşu ortalamasından mutlak farkı. Rota tercihinde kullanılabiliyor. | Çözünürlüğe bağımlı bir vekil ölçüt; kaya boyutu veya zemin taşıma gücü değil. |
| Jeoloji | USGS yerel/küresel poligonları, birim adları ve ölçekler. Nokta sorgusunda jeoloji metin birimi, yükselti sayısal metre olarak ayrı dönüyor. | Web için basitleştirilmiş sınırlar; uygulama renkleri resmi basılı haritanın paleti değil. |
| Radyasyon | Gerçek RAD RDR bayt konumu, birim, UTC, entegrasyon süresi, kaynak özeti checksum'ı ve aynı-sol rover konumu test edildi. | Tek yerel arşiv gözlemi. Kesin ölçüm anı konumu yok; bütün Mars'a veya bugünkü rotaya yayılmıyor. |
| Sıcaklık | MEDA ATS1: 253,31 K → −19,84 °C; Sol 1, LTST 15:27:28. Gerçek PDS satırı yeniden kontrol edildi. | Yaklaşık Jezero iniş konumu; tek eski örnek, güncel sıcaklık alanı değil. |
| Termal atalet | Gerçek TES kaynak-renkli görüntüsünün temsili tile'ı canlı açıldı. Fiziksel birim açıklanıyor. | Sayısal renk kalibrasyonu kurulmadı; renklerden sayısal atalet veya sıcaklık okunmuyor, rota maliyetine katılmıyor. |
| THEMIS gece IR | Gerçek tarihsel IR mozaiği; temsili tile ve kapsama doğrulandı. | Göreli IR parlaklığı; Kelvin veya hava sıcaklığı değil. |
| Toz/atmosfer | MY34 Sol 400, 3° tarihsel gözlemlerden enterpole edilmiş model. Kaynak paleti/JSON/PNG ilişkisi test edildi; 9,3 µm optik derinlik, 610 Pa referansı. | Güncel hava, rüzgâr veya basınç tahmini yok. Bu bir doğrudan yeni ölçüm ya da tam atmosfer simülasyonu değil. |
| Veri kapsamı | Sayısal cell maskesi; nokta/rota için veri mevcudiyeti. Eksik radyasyon/sıcaklık/güncel toz, sıfır risk olarak ele alınmıyor. | Optik footprint tek başına her pikselde veri garantisi değil. Çevresel ölçümlerin eşleşeceği rota zamanı verilmediği için güncel kapsam eksik kalıyor. |
| Rover geçmişi | Dört gerçek GeoJSON dosyası HTTP ile alındı; geometri ve koordinat sınırları kontrol edildi. | Curiosity arşiv çizgilerinde eksik sol bilgisi uydurulmadı. Rakamlar arşiv kesitinin uzunluğu; güncel görev kilometre sayacı değil. |

Sayısal yükseklik/eğim/pürüzlülük görünümü seçilen rotanın DEM'ine kilitlenir. O modelin kapsamadığı yerde değer null/şeffaf kalır. “Clear” ile en ayrıntılı mevcut DEM seçimine dönülür. Haritanın ayrı 3B geometri kaynağı ayrıca etiketlenir.

## C. Rota algoritması ve bağımsız referanslar

- A* gerçek sayısal DEM gridi üzerinde çalışır. Eksik yükseklik/eğim ve >20° hücreler dışlanır; çapraz köşe kesilmez. Yükseklik, eğim ve tırmanış/iniş hesabına temel olur; mesafe kenar maliyetine, isteğe bağlı eğim/pürüzlülük ağırlıkları tercihlere girer. Mutlak yükseltiye uydurma sağlık puanı eklenmedi.
- Mesafe referansı Mars 2000 yarıçapı **3.396.190 m** ve 3B birim vektörlerin `atan2(cross, dot)` hesabıdır. Bu yöntem API'nin haversine formülünden bağımsızdır. Test toleransı toplam 0,003 km'dir. A* özel küresel kenar maliyeti ayrıca küçük grid üzerinde bağımsız Dijkstra ile karşılaştırıldı.
- Rota başı/sonu tam seçilen koordinatlarla eşleşiyor. Grid merkezine sapma, kullanıcıya iç arama özelliği olarak raporlanıyor. Aynı kaynak üzerinden başlangıç/bitiş bağlantıları da kontrol ediliyor.
- Ekran katmanını açmak görüntüleme işlemidir. Maliyet tercihlerindeki eğim/pürüzlülük seçimi hesaplamayı etkiler. Geçmiş radyasyon/atmosfer görüntüsünü açmak, bu verilerin gelecekteki rota boyunca bilindiği anlamına gelmez.
- Rota adayları birden çok ölçütü dengeler. “Dengeli” adayın her tekil ölçütü mutlaka daha küçük değildir. Eksik çevresel veri, fiziksel eğim uyarısından ayrı gösterilir. Arama penceresi ve uyarlamalı grid nedeniyle tüm gezegen üzerinde mutlak optimum veya operasyonel emniyet garantisi verilmez.

### Gerçek HTTP rota örnekleri

| Bölge / başlangıç–bitiş [lon, lat] | Doğrulanan model ve sonuç |
|---|---|
| Jezero `[77.42,18.44] → [77.40,18.46]` | CTX 20 m. Mesafe öncelikli 1,656 km / en dik 16,1°; dengeli 1,656 km / 11,7°; arazi öncelikli 1,691 km / 10,3°. Son adayın ortalama pürüzlülüğü de 0,12 m'den 0,10 m'ye indi. |
| HiRISE `[77.41,18.45] → [77.4104,18.4504]` | Küçük 1,02 m DTM penceresi gerçekten seçildi. |
| Gale `[137.35,-4.7] → [137.8,-4.8]` | MOLA; detaylı görüntü olması detaylı yürüyüş DEM'i olduğu şeklinde yorumlanmadı. |
| Olympus `[-134,18] → [-133,19]` | Engebeli/volkanik bölge, MOLA. |
| Valles Marineris `[-70,-12] → [-68,-13]` | Krater/yarıntı duvarlarına benzer engebeli bölge; >20° mevcut grid hücreleri dışlama kuralına tabi. |
| Seyrek veri `[165,40] → [168,42]` | Yerel ince DEM ve güncel çevre ölçümleri bulunmadığında MOLA ve açık veri eksikliği bildirimi. |
| Kullanıcının uzun rotası `[67.149373,27.259329] → [82.878283,10.875713]` | 1308 km kuş uçuşu mesafe artık reddedilmiyor. Tam uç bağlantılarıyla ilk aday 1322,378 km; yaklaşık 7,4 km arama adımı, aradaki yerel MOLA hücreleri denetlendi. |
| Gezegen ölçeği `[-140,-35] → [30,45]` | Yaklaşık 9924 km kuş uçuşu; ilk aday 10237,917 km. 75.050 arama düğümü; yaklaşık 25,9 km arama adımı. Bu bir tek EVA planı değil, kaba bölgesel hesaplama örneğidir. |
| Kutup `[10,89] → [120,88.5]` | Eski ±87° reddi kaldırıldı; gerçek MOLA'da hesaplama tamamlandı. Kutup bölgesi çözünürlük/geometri sınırlamaları devam eder. |

Her adayın mesafesi, eğimi, pürüzlülüğü, zamanı ve gerçek kaynak metadatası [canlı HTTP kaydında](final-live-api-checks.json) bulunur. Yürüme süresi uyarlanmış Tobler modeli ve 2,2 km/h varsayımıdır; günler süren uzun sonuçlar gerçek görevin yaşam desteği, mola veya kaynak planlaması değildir.

## D. Görüntü kalitesi ve koordinatlar

Projeksiyon Web Mercator değildir. Küre Mars yarıçapını, planetosentrik enlem ve doğu-pozitif boylamı kullanır. Sayısal CTX dönüşümü GeoTIFF CRS'siyle bağımsız kontrol edildi. Görüntü servisi grid başlangıcı `[-180,90]`, 2:1 coğrafi matris ve yayıncı çözünürlükleri doğrulanıyor; bunlara uymayan dört ürün kullanılmıyor.

Uzakta Viking renkleri korunur. 1,6 milyon–600 bin metre kamera yüksekliği aralığında geçiş yumuşatılır; yakında gri CTX/HiRISE ve gri kaba arka plan kullanılır. Gri arka plan, görüntü boşluklarında renkli şerit çıkmasını engellemeyi amaçlar; eksik yüksek çözünürlüğü üretmez. Bölgesel görüntü görünümün tamamını örtmeden bindirilmez. Seyrek küresel HiRISE yakın zoom'la sınırlandırılır. Bunun gerçek son-frame görünümü son tarayıcı kabulünde doğrulanmalıdır; politika testinin geçmesi ekranın kusursuz olduğunu kanıtlamaz.

Yüksek çözünürlüklü görüntü ile yüksek çözünürlüklü sayısal DEM farklı ürünlerdir. HiRISE/CTX kaynaklarının kendi kayıt hataları, görüntü dikişleri ve boşlukları tamamen giderilmiş sayılmıyor. Yapay keskinleştirme veya uydurulmuş yüzey ayrıntısı eklenmedi. Altı renkli yükselti geçişi, sıfır areoid referansı ve hillshade korunuyor; gerçek yüklenen MOLA min/max uçları legend'e bağlanıyor.

## E. NASA Space Apps uygunluğu

NASA'nın [resmî Space Apps organizasyon ekibi yanıtı](https://github.com/nasa/spaceapps/discussions/1827), Global Awards için ilgili görevin Resources bölümündeki en az bir NASA veri kaynağının kullanılmasını; tüm veri, kod, metin, görsel ve araçların atıflarının verilmesini istiyor. Üçüncü taraf kaynaklar, koşullarına uyulduğunda kullanılabiliyor. [Gönderim/atıf alanlarına ilişkin resmî yanıt](https://github.com/nasa/spaceapps/discussions/1858) yapay zekâ kullanımının da açıklanmasını istiyor.

Bu uygulama birden fazla NASA görevinden gerçek veri kullanıyor. LMD/Montabone ürünü ve Caltech tarafından işlenen CTX mozaiği, NASA'nın kendi yayımladığı her yerde güncel bir ölçüm olarak sunulmuyor. NASA/USGS/PDS kaynağı ve bilimsel kapsamı ayrı ayrı kaydedildi. NASA'nın projeyi desteklediği veya emniyetini onayladığı ileri sürülmüyor.

**Açık inceleme:** [Martian Map görev sayfası](https://www.spaceappschallenge.org/2026/challenges/interplanetary-survival-guide-martian-map/?tab=resources) ve güncel web gönderim kılavuzu bu denetimde 502/403/sertifika erişim hataları verdi. Bu nedenle ilgili Resources listesindeki üyelik ve göreve özgü bütün son koşulların sağlandığı kesin olarak onaylanmadı. Başka takımların README'leri resmî şartname yerine kullanılmadı. Kullanıcının önceki resmî form ekran görüntülerindeki alanlar korunuyor; form gönderilmedi. Ayrıca bu yerel build'in herkese açık demo/repo sürümüne entegrasyonu yapılmış sayılmaz.

Kullanım koşulları: [NASA medya yönergesi](https://www.nasa.gov/nasa-brand-center/images-and-media/), [USGS haklar/atıflar](https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits), [HiRISE görüntü politikası](https://www.uahirise.org/media/usage.php). HiRISE kamuya açık görüntüleri için NASA/JPL/University of Arizona atfı korunur. USGS üretimi içerik genel olarak ABD kamu malıdır; üçüncü taraf istisnaları ayrıca geçerlidir. Caltech işlenmiş mozaiğinin ayrı yeniden dağıtım lisansı bağımsız olarak kesinleştirilmedi; uygulama ilan edilen servisten akış yapıyor, görüntü mozaiğini yeniden paketlemiyor. Toz türevi CC BY-SA 3.0 atıf/paylaşım koşullarını korur. Yazılım lisansları bilimsel veri koşullarından ayrıdır.

## F. Gerçekten entegre edilen bilimsel kaynaklar

| Veri / görev–cihaz | Yayıncı ve resmî bağlantı | Uygulamadaki kullanım, kapsama/çözünürlük/zaman |
|---|---|---|
| Viking MDIM 2.1 / Viking kameraları | NASA/JPL Mars Trek: [katalog](https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars) | Küresel renkli bağlam, nominal 232 m; tarihsel mozaik. |
| Küresel CTX / MRO Context Camera | Caltech/MSSS/JPL görev görüntülerinden işlenmiş; NASA'nın [ilan ettiği WMTS](https://trek.nasa.gov/tiles/Mars/EQ/CTX_beta01_uncontrolled_5m_Caltech/1.0.0/WMTSCapabilities.xml) ve [yayıncı servis](https://astro.arcgis.com/arcgis/rest/services/OnMars/CTX/MapServer?f=pjson) | Gri küresel yakın görünüm. Kaynak nominal 5 m; kullanılan WMTS seviyesinde yaklaşık 10,18 m sunulan piksel. Boşluklar mevcut olabilir. |
| HiRISE görüntüleri / MRO HiRISE | NASA/JPL/UArizona: [küresel capabilities](https://trek.nasa.gov/tiles/Mars/EQ/HiRISE_Global/1.0.0/WMTSCapabilities.xml), [geçerli yayıncı LOD](https://astro.arcgis.com/arcgis/rest/services/OnMars/HiRISE/MapServer?f=pjson), [Jezero capabilities](https://trek.nasa.gov/tiles/Mars/EQ/JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0_lon0_first_dd/1.0.0/WMTSCapabilities.xml) | Seyrek yakın görüntüler; 0,16 m sunulan en ince global piksel, yerel Jezero kaynak nominal 25 cm. Sunulan piksel doğal edinim çözünürlüğünü ve tam kapsamı garanti etmez. |
| Bölgesel CTX/HiRISE optik mozaikler / MRO | NASA Mars Trek [tek tek kaynak URL'lerini içeren manifest](../data/explorer/imagery.json) | Görünüme göre isteğe bağlı seçim. 77 etkin tanımın hepsinin görüntüsü bu denetimde tek tek indirilmedi; dört reddedilen matris ve nedenleri aynı dosyada. |
| Sayısal MOLA MEGDR / MGS Mars Orbiter Laser Altimeter | NASA PDS Geosciences/GSFC: [ürün arşivi](https://pds-geosciences.wustl.edu/missions/mgs/megdr.html) | Aktif küresel grid 16 px/° ≈3,7 km; 1997–2001 görev verilerinden topoğrafik model; Mars areoidi/GMM3 referansı. Ölçümden türetilmiş grid, her cell'de bağımsız yeni ölçüm değil. |
| Jezero CTX DEM / MRO CTX | USGS/JPL: [ürün sayfası](https://astrogeology.usgs.gov/search/map/mars_2020_science_investigation_ctx_dem_mosaic), [GeoTIFF](https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/ScienceInvestigationMaps_JPL/M20_JezeroCrater_CTXDEM_20m.tif) | Jezero 20 m DEM; eğim, pürüzlülük, yükselti ve rota. Fred Calef/USGS/PDS ürün atfı. |
| HiRISE stereo DTM / MRO HiRISE | NASA/UArizona/USGS: [PSP_002387_1985 DTM](https://hirise.lpl.arizona.edu/dtm/PSP_002387_1985), [USGS koleksiyonu](https://doi.org/10.5066/P9VQTS7V) | Yaklaşık 1 km² yerel pencere; yaklaşık 1,02 m gerçek örnekler. Küresel ince DEM gibi sunulmaz. |
| Küresel jeoloji / görev verilerinin kartografik sentezi | USGS [SIM 3292](https://pubs.usgs.gov/sim/3292/) | Küresel jeolojik birim, 1:20.000.000; bir cihazın anlık ölçümü değil. |
| Jezero jeolojisi / MRO ve ilgili görev verileri sentezi | USGS [SIM 3464](https://pubs.usgs.gov/publication/sim3464) | Yerel birimler, 1:75.000; basitleştirilmiş web poligonları. |
| Termal atalet / MGS TES | NASA Mars Trek [TES WMTS](https://trek.nasa.gov/tiles/Mars/EQ/TES_Thermal_Inertia/1.0.0/WMTSCapabilities.xml) | Tarihsel renkli atalet görüntüsü; kaynak örnekleme yaklaşık 3 km, servis z0–1. Nicel renk anahtarı bu uygulamada doğrulanmadı. |
| Gece IR / Mars Odyssey THEMIS | NASA Mars Trek [gece WMTS](https://trek.nasa.gov/tiles/Mars/EQ/THEMIS_NightIR_ControlledMosaics_100m_v2_oct2018/1.0.0/WMTSCapabilities.xml) | Nominal 100 m, yaklaşık ±65°; tarihsel 2018 kontrollü mozaik, göreli parlaklık. |
| Radyasyon / MSL Curiosity RAD E | NASA PDS PPI/SwRI: [RDR arşivi](https://pds-ppi.igpp.ucla.edu/data/MSL-M-RAD-3-RDR-V1.0/), [tam gözlem dosyası](https://pds-ppi.igpp.ucla.edu/data/MSL-M-RAD-3-RDR-V1.0/DATA/SOL_01418_01514/RAD_RDR_2016_298_19_33_1500_V00.TXT), [etiket](https://pds-ppi.igpp.ucla.edu/data/MSL-M-RAD-3-RDR-V1.0/DATA/SOL_01418_01514/RAD_RDR_2016_298_19_33_1500_V00.LBL) | OBS000, Sol 1500, **10,92457 µGy/h**, **2016-10-24 19:33:55 UTC**, **961 s**. Yerel arşiv kaydı; biyolojik doz eşdeğeri veya küresel alan değil. |
| RAD konum ilişkisi / Curiosity görev navigasyonu | NASA/JPL [Sol 1500 waypoint kaynağı](https://mars.nasa.gov/mmgis-maps/MSL/Layers/json/MSL_waypoints.json) | `[137.3550896,-4.70014911]`, aynı-sol son rover konumu. RAD dosyasındaki sıfır geometri alanları gerçek ölçüm konumu sayılmadı; kesin zaman eşleşmesi yok. |
| Hava sıcaklığı / Mars 2020 Perseverance MEDA ATS1 | NASA PDS Atmospheres [kalibre CSV](https://atmos.nmsu.edu/PDS/data/PDS4/Mars2020/mars2020_meda/data_calibrated_env/sol_0000_0089/sol_0001/WE__0001___________CAL_ATS_________________P01.CSV) | Sol 1, LTST 15:27:28, yaklaşık iniş noktası; 253,31 K → −19,84 °C. Güncel sıcaklık grid'i değil. |
| Tarihsel toz / Montabone ekibi, MRO/MCS tabanlı klimatoloji | LMD [ürün sitesi](https://www-mars.lmd.jussieu.fr/mars/dust_climatology/), [çalışma](https://doi.org/10.1029/2019JE006111) | MY34 Sol 400/Ls 196,39°, 3° grid; 9,3 µm optik derinlik ve 610 Pa normalizasyonu. Gözlemlerden enterpole edilmiş model; yayıncı NASA değil, görev verisi kökeni ve CC BY-SA 3.0 koşulu açık. |
| Rover arşiv rotaları / görev navigasyonu | NASA/JPL [Perseverance](https://mars.nasa.gov/mmgis-maps/M20/Layers/json/M20_traverse.json), [Curiosity](https://mars.nasa.gov/mmgis-maps/MSL/Layers/json/MSL_traverse.json); NASA PDS [Spirit/Opportunity](https://an.rsl.wustl.edu/mera/AN/pages/mer/mer_traverse.htm) | Dört görevin tarihsel çizgileri; bazı MER ara konumları arşivce enterpole edilmiş, eksik sol alanı korunuyor. |
| Bilim durakları ve fotoğraflar / Perseverance, Mastcam-Z ve diğer görüntüleyiciler | NASA/JPL [waypoint verisi](https://mars.nasa.gov/mmgis-maps/M20/Layers/json/M20_waypoints.json), [Brac](https://science.nasa.gov/resource/mastcam-zs-view-of-the-area-around-brac-in-mars-jezero-crater/), [Hogwallow Flats](https://science.nasa.gov/resource/perseverances-mastcam-z-views-hogwallow-flats/), [Wildcat Ridge bağlamı](https://science.nasa.gov/mission/mars-2020-perseverance/mars-rock-samples/), [Yori Pass](https://science.nasa.gov/blog/a-picture-is-worth-a-thousand-words/), [Three Forks](https://science.nasa.gov/resource/perseverances-three-forks-sample-depot-map/) | Beş bağlam işareti; tam örnek alma yerleriyle eşitlenmez. Her fotoğrafın gerçek galeri URL'si/cihaz kredisi [GeoJSON'da](../data/science_points.json). |
| Yer adları / IAU nomenklatürü | USGS/IAU [Gazetteer](https://planetarynames.wr.usgs.gov/Page/MARS/target) | Arama/yer bulma; coğrafi özellik merkezi, noktasal fiziksel ölçüm değil. |
| Lake Salda / bilimsel sunum bağlamı | NASA Science [Salda–Mars karşılaştırması](https://science.nasa.gov/blogs/earth-matters/2021/02/17/what-a-lake-in-turkey-can-tell-us-about-mars/) | Belge/sunum metni; rota maliyeti veya çevresel ölçüm kaynağı değil. |

### İncelenen veya mevcut olup bu 3B analizde kullanılmayanlar

- [USGS 463 m MOLA DEM](https://astrogeology.usgs.gov/search/map/mars_mgs_mola_dem_463m): bu 3B hesaplamada indirilmiş/etkin sayısal grid değil. 463 m renkli hillshade legacy 2B görsel bağlamından ayrı tutulur. 4 px/° dosyası da mevcut 16 px/° rasterin yerine etkin kaynak olarak gösterilmez.
- Üçüncü taraf eski RAD/Zenodo satırı resmî PDS kaydıyla değiştirildi; mevcut ölçüm kaynağı diye listelenmez.
- THEMIS gündüz mozaiğinin temsili servisi kontrol edildi, ancak mevcut arayüzün ayrı aktif gündüz katmanı olarak eklenmedi.
- Güncel küresel radyasyon, hava sıcaklığı, rüzgâr/basınç tahmini, sayısal TES renk kalibrasyonu ve küresel ince HiRISE DEM'i entegre edilmiş gibi sunulmaz.

## G. Test sonuçları, kanıtlar ve açık işler

| Kontrol | Sonuç / kanıt |
|---|---|
| Tüm pytest | **78 başarılı, 27 atlandı** — [tam kayıt](final-pytest.txt) |
| Güncel backend + gerçek veri + bağımsız sayısal referanslar | **45 başarılı** — [backend kaydı](final-backend-tests.txt) |
| Frontend görüntü seçim politikası | **6 başarılı** — [kayıt](final-frontend-policy-tests.txt). Bu testler tarayıcı/GPU görüntülemesi değil. |
| Çalışan Flask üzerinden gerçek HTTP/API | **25 başarılı, 0 başarısız** — [ayrıntılı kayıt](final-live-api-checks.json): başlangıç/assets, metadata, beş raster türü, dört rover, dokuz rota, hatalı istekler ve gerçek CORS yanıtı. |
| Canlı dış görüntü servisleri | **8 temsili tile başarılı** — [HTTP/format/CORS kaydı](explorer-source-checks.json). Tüm dünya görüntülerinin tamamı test edilmiş sayılmaz. |
| Atlas metadata yenilemesi | 77 etkin / 4 tutarsız matris dışlandı — [manifest ve ret nedenleri](../data/explorer/imagery.json) |
| Python sözdizimi / JavaScript sözdizimi / Git diff boşluk kontrolü | **Geçti.** Bilimsel veya görsel kabul yerine geçmez. |
| Atlanan 27 pytest | 21 test ZIP'e dahil olmayan tarihsel Git commit'ine sabitlenmiş; altı eski koşulsuz entegrasyon yer tutucusu. [Nedenler](final-integration-tests.txt). Bunlar geçer gibi sayılmadı; güncel gerçek-veri kontrolleri ayrı uygulandı. |
| Son tarayıcı/GPU kabulü | **Tamamlanmadı.** Önceki oturumda URL doğrulaması durdu. Bu denetimde tarayıcı penceresi yeniden bulundu; giriş geometrisi alınamadı ve pencere bilgisi yenilenerek tekrarlanan etkinleştirme de `failed to activate captured window` hatası verdi. Computer Use yönergesindeki tek tekrar sonrası durma kuralı uygulandı. Yakın/uzak son frame, döndürme, tüm katmanların son-build piksel çıktısı, saydamlık ve konsol hataları bu sürüm için “hatasız” ilan edilmez. Eski ekran görüntüleri yeni son build'in kanıtı değildir. |
| Space Apps göreve özgü son uygunluk | **Kaynak sekmesi erişimi nedeniyle açık.** Genel resmî NASA veri/atıf şartı incelendi; görevin güncel Resources üyeliği ve son form/yerel etkinlik şartları kesin onaylanmadı. |

Gerçek fiziksel/çevresel veri olmayan yerde 0 risk veya kesin tehlike yazılmıyor. MOLA'nın kaba çözünürlüğü, uyarlamalı arama penceresi, model varsayımları ve eksik çevre verileri nedeniyle operasyonel astronot emniyeti iddia edilmiyor. Yerel uygulama `http://127.0.0.1:5051/` üzerinden çalıştırıldı; kaynak ve sonuç dosyaları ekip entegrasyonuna hazır, ancak bu rapor son tarayıcı kabulü veya NASA onayı değildir.
