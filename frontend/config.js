// =====================================================================
// config.js — Değişebilecek HER ŞEY burada. Başka dosyaya dokunmadan
// backend adresini, istek formatını ve katman ayarlarını buradan değiştirin.
// =====================================================================

// Backend rota servisinin adresi. Sunucu başka makinede/portta çalışırsa
// sadece bu satırı değiştirin.
const API_URL = "http://localhost:5000/route";

// Backend cevap vermezse kaç milisaniye sonra vazgeçelim (30 sn).
const API_TIMEOUT_MS = 30000;

// İstek gövdesini kuran TEK fonksiyon. Backend formatı değişirse yalnızca
// burayı düzeltin. start/end, Leaflet'in L.LatLng nesneleridir.
// DİKKAT: Alanları isimle (lat/lng) gönderiyoruz, dizi sırasına güvenmiyoruz;
// böylece GeoJSON'un [boylam, enlem] sırasıyla karışma riski yok.
// Boylamı hem "lng" (Leaflet adı) hem "lon" (backend'in ilk adı) olarak
// gönderiyoruz: backend'in eski sürümü sadece "lon" okuyordu, yenisi ikisini
// de kabul ediyor. Böylece backend'in hangi sürümü çalışırsa çalışsın 400 almayız.
function buildRouteRequest(start, end) {
  return {
    start: { lat: start.lat, lng: start.lng, lon: start.lng },
    end:   { lat: end.lat,   lng: end.lng,   lon: end.lng },
  };
}

// Backend'in eğim sınırı (backend/routing.py → SAFETY_THRESHOLD_DEG).
// Sadece özet kutusunda bilgi olarak gösterilir; rotayı backend sınırlar.
// Backend değeri değişirse burayı da güncelleyin.
const SLOPE_THRESHOLD_DEG = 20;

// Veri rolünün hazırladığı bilim noktaları (GeoJSON FeatureCollection).
// Yol sayfaya göredir: sayfa REPO KÖKÜNDEN sunulmalı
// (repo kökünde "python -m http.server 8000" → http://localhost:8000/frontend/index.html),
// yoksa ../data klasörüne erişilemez. Dosya bulunamazsa harita yine çalışır.
const SCIENCE_POINTS_URL = "../data/science_points.json";

// Haritanın açılış görünümü: Jezero Krateri (HiRISE mozaiğinin ortası).
const MAP_CENTER = [18.45, 77.40]; // Leaflet sırası: [enlem, boylam]
const MAP_ZOOM = 12;

// NASA Mars Trek HiRISE Jezero ortomozaiği (25 cm/piksel).
// Adresi DEĞİŞTİRMEYİN: çift "//" kasıtlı, sıra {z}/{y}/{x} (satır/sütun).
// curl ile doğrulandı: z0..z17 var, z18 ve üstü 404 döner.
const HIRISE = {
  url: "https://trek.nasa.gov/tiles/Mars/EQ/JEZ_hirise_soc_006_orthoMosaic_25cm_Eqc_latTs0_lon0_first_dd/1.0.0//default/default028mm/{z}/{y}/{x}.png",
  attribution: "NASA/JPL-Caltech/USGS",
  maxNativeZoom: 17, // Sunucudaki en yüksek gerçek zoom seviyesi
  maxZoom: 19,       // 18-19'da Leaflet z17 tile'larını büyüterek gösterir
  // Kapsama alanı (WMTSCapabilities.xml'deki LowerCorner/UpperCorner).
  // Bu kutunun dışı için tile istenmez; dışarısı zaten boş/404'tür.
  bounds: [
    [18.3067994, 77.2229331], // güneybatı köşe [enlem, boylam]
    [18.669315, 77.583964],   // kuzeydoğu köşe
  ],
};
