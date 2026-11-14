// =====================================================================
// app.js — Harita, tıklama ile nokta seçimi, backend'den rota isteme
// ve rotayı çizme. Ayarlar config.js'te.
// =====================================================================

// ---------- 1) Harita ----------
// Mars verisi Web Mercator DEĞİL, eşdikdörtgen (enlem/boylam) ızgarada.
// L.CRS.EPSG4326'nın tile ızgarası (zoom 0 = 2x1 tile, sol üst -180,90)
// NASA'nın default028mm ızgarasıyla birebir aynı; bu yüzden tms/{-y} gerekmez.
// Telefon gibi dar ekran mı? (Sayfa açılırken bir kez bakılır; CSS'teki
// @media (max-width: 600px) ile aynı sınır.)
const DAR_EKRAN = window.matchMedia("(max-width: 600px)").matches;

// Leaflet'in EPSG4326'sı mesafeyi DÜNYA yarıçapıyla (6371 km) ölçer; ölçek
// çubuğu bu yüzden Mars'ta ~1,88 kat yanlış çıkardı. Tile ızgarası aynı
// kalsın, sadece yarıçap Mars olsun (backend'deki Mars 2000 küresiyle aynı: 3396190 m).
const MARS_CRS = L.extend({}, L.CRS.EPSG4326, { R: 3396190 });

const map = L.map("map", {
  crs: MARS_CRS,
  center: MAP_CENTER,
  zoom: MAP_ZOOM,
  maxZoom: HIRISE.maxZoom,
});

// ---------- 2) Katmanlar ----------
// MOLA altlığı (tüm Mars): HiRISE kutusunun dışı siyah kalmasın diye.
// zIndex 0 → panelden kapatıp açınca bile her zaman HiRISE'ın (zIndex 1) altında kalır.
const molaKatmani = L.tileLayer(MOLA.url, {
  attribution: MOLA.attribution,
  maxNativeZoom: MOLA.maxNativeZoom,
  maxZoom: HIRISE.maxZoom,
  zIndex: 0,
}).addTo(map);

// HiRISE görüntü katmanı. "bounds" sayesinde kapsama dışı için istek atılmaz.
const hiriseLayer = L.tileLayer(HIRISE.url, {
  attribution: HIRISE.attribution,
  maxNativeZoom: HIRISE.maxNativeZoom,
  maxZoom: HIRISE.maxZoom,
  bounds: HIRISE.bounds,
}).addTo(map);

// HiRISE'ın kapsadığı alanı kesikli çizgiyle gösteren kutu. Kullanıcı
// yüksek çözünürlüklü görüntünün nerede bittiğini görsün diye. interactive:false →
// tıklamaları engellemez, tıklama haritaya geçer.
const kapsamaKutusu = L.rectangle(HIRISE.bounds, {
  color: "#ffcc00", weight: 1, dashArray: "6 4", fill: false, interactive: false,
}).addTo(map);

// Bilim noktaları katmanı: önce boş oluşturulur, veri gelince doldurulur
// (bkz. bölüm 7). Boş da olsa katman listesinde görünür.
const bilimKatmani = L.layerGroup().addTo(map);

// Katman aç/kapa kontrolü (sağ üst). Değişkende tutuyoruz ki sonradan
// yüklenen katmanlar (eğim haritası) addOverlay ile eklenebilsin.
const katmanKontrol = L.control.layers(null, {
  "MOLA colour relief (global, 463 m)": molaKatmani,
  "HiRISE Jezero (25 cm)": hiriseLayer,
  "HiRISE coverage": kapsamaKutusu,
  "Science sites (Perseverance)": bilimKatmani,
}, { collapsed: DAR_EKRAN }).addTo(map); // telefonda katman paneli simgeye küçülür

L.control.scale({ imperial: false }).addTo(map);

// ---------- 2b) Eğim tehlike haritası ----------
// Önce JSON'dan sınırları okur, sonra PNG'yi o sınırlara gerer.
// Dosyalar yoksa harita normal çalışır, panelde bu katman görünmez.
let egimKatmani = null;

// Lejant (sağ alt): sadece eğim katmanı açıkken görünür.
const EgimLejanti = L.Control.extend({
  onAdd: function () {
    const d = L.DomUtil.create("div", "durum-kutusu egim-lejant");
    const baslik = document.createElement("div");
    baslik.className = "baslik"; baslik.textContent = "Slope (data used by the router)";
    d.append(baslik);
    SLOPE_OVERLAY.siniflar.forEach((s) => {
      const satir = document.createElement("div");
      const kare = document.createElement("span");
      kare.className = "kare"; kare.style.background = s.renk;
      satir.append(kare, document.createTextNode(s.metin.replaceAll("{sinir}", this.options.sinir)));
      d.append(satir);
    });
    return d;
  },
});
let egimLejanti = null;
map.on("overlayadd", (e) => { if (e.layer === egimKatmani && egimLejanti) egimLejanti.addTo(map); });
map.on("overlayremove", (e) => { if (e.layer === egimKatmani && egimLejanti) egimLejanti.remove(); });

fetch(SLOPE_OVERLAY.metaUrl)
  .then((r) => { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
  .then((meta) => {
    const sinir = meta.slope_limit_deg;
    if (sinir !== SLOPE_THRESHOLD_DEG) {
      console.warn(`Eğim sınırı uyuşmuyor: overlay ${sinir}°, config.js ${SLOPE_THRESHOLD_DEG}°`);
    }
    // interactive:false → üstüne tıklamak haritaya tıklama sayılır (rota seçimi bozulmaz).
    // className → CSS'te "pixelated": 20 m'lik hücreler bulanıklaşmadan görünür.
    egimKatmani = L.imageOverlay(SLOPE_OVERLAY.url, meta.bounds, {
      interactive: false, className: "egim-katmani",
    });
    egimKatmani.on("error", () => console.warn("Eğim resmi yüklenemedi:", SLOPE_OVERLAY.url));
    // Telefonda alt köşeler rota özetine yetmiyor; lejant sol üste (zoom düğmelerinin altına) gider.
    egimLejanti = new EgimLejanti({ position: DAR_EKRAN ? "topleft" : "bottomright", sinir });
    katmanKontrol.addOverlay(egimKatmani, "Slope hazard (CTX DEM, 20 m)");
    if (SLOPE_OVERLAY.showOnStart) map.addLayer(egimKatmani); // overlayadd → lejant da açılır
  })
  .catch((hata) => console.warn("Eğim katmanı bulunamadı (" + SLOPE_OVERLAY.metaUrl + "):", hata.message));

// ---------- 3) Durum kutusu (sol alt) ----------
// Kullanıcıya talimat, "hesaplanıyor" ve hata mesajlarını gösterir.
const DurumKontrol = L.Control.extend({
  onAdd: function () {
    this._div = L.DomUtil.create("div", "durum-kutusu");
    // Kutunun üstüne tıklamak haritaya tıklama sayılmasın:
    L.DomEvent.disableClickPropagation(this._div);
    return this._div;
  },
});
const durum = new DurumKontrol({ position: "bottomleft" }).addTo(map);

// tur: "" (normal), "yukleniyor" veya "hata". textContent kullanıyoruz ki
// sunucudan gelen metin HTML olarak yorumlanmasın (güvenlik).
function durumGoster(metin, tur = "") {
  durum._div.className = "durum-kutusu" + (tur ? " " + tur : "");
  durum._div.textContent = metin;
  // Hesaplanırken imleç "bekleniyor" olur (CSS: .rota-hesaplaniyor)
  map.getContainer().classList.toggle("rota-hesaplaniyor", tur === "yukleniyor");
}

// ---------- 4) Tıklama durumu ----------
let baslangic = null;      // ilk tıklanan nokta (L.LatLng)
let baslangicIsaret = null;
let bitisIsaret = null;
let rotaKatmani = null;
let aktifIstek = null;     // devam eden fetch'i iptal etmek için AbortController

// Her şeyi temizler: işaretçiler, rota ve (varsa) yarım kalan istek.
function sifirla() {
  if (aktifIstek) { aktifIstek.abort(); aktifIstek = null; }
  [baslangicIsaret, bitisIsaret, rotaKatmani].forEach((k) => { if (k) map.removeLayer(k); });
  baslangic = baslangicIsaret = bitisIsaret = rotaKatmani = null;
}

// Basit renkli daire işaretçi (resim dosyası gerektirmez).
function isaretKoy(latlng, renk, etiket) {
  return L.circleMarker(latlng, {
    radius: 8, color: "#fff", weight: 2, fillColor: renk, fillOpacity: 1,
  }).bindTooltip(etiket).addTo(map);
}

map.on("click", (e) => {
  if (baslangic === null || bitisIsaret !== null) {
    // 1. tıklama (veya 3. tıklama → önce sıfırla): başlangıç noktası
    sifirla();
    baslangic = e.latlng;
    baslangicIsaret = isaretKoy(e.latlng, "#2e9e44", "Start");
    durumGoster("Click to set the end point.");
  } else {
    // 2. tıklama: bitiş noktası → rotayı iste
    bitisIsaret = isaretKoy(e.latlng, "#d33", "End");
    rotaIste(baslangic, e.latlng);
  }
});

// ---------- 5) Backend'den rota isteme ----------
async function rotaIste(start, end) {
  durumGoster("Computing route…", "yukleniyor");

  const kontrol = new AbortController();
  aktifIstek = kontrol;
  // Zaman aşımında isteği iptal et; "zamanAsimi" bayrağı ile kullanıcı
  // sıfırlamasından ayırt ediyoruz.
  let zamanAsimi = false;
  const zamanlayici = setTimeout(() => { zamanAsimi = true; kontrol.abort(); }, API_TIMEOUT_MS);

  try {
    const yanit = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildRouteRequest(start, end)),
      signal: kontrol.signal,
    });

    // Gövdeyi JSON olarak okumayı dene; bozuksa null kalır.
    let veri = null;
    try { veri = await yanit.json(); } catch (_) { /* JSON değil */ }

    if (!yanit.ok) {
      // Backend hata formatı: {"error": "<Türkçe mesaj>"} + 400/422
      const mesaj = veri && veri.error ? veri.error : `Server error (HTTP ${yanit.status}).`;
      throw new Error(mesaj);
    }
    // Çizmeden önce geometriyi doğrula; bozuksa hata fırlatır (catch'e düşer).
    const geometri = rotaGeometrisiAl(veri);
    rotaCiz(geometri, (veri && veri.properties) || {});
  } catch (hata) {
    if (hata.name === "AbortError" && !zamanAsimi) return; // kullanıcı sıfırladı, sessiz geç
    let mesaj = hata.message;
    if (zamanAsimi) mesaj = "The server did not respond in time.";
    else if (hata instanceof TypeError) mesaj = "Could not reach the server.";
    durumGoster("Error: " + mesaj + " (Click the map to try again.)", "hata");
  } finally {
    clearTimeout(zamanlayici);
    if (aktifIstek === kontrol) aktifIstek = null;
  }
}

// ---------- 6) Yanıtı doğrulama ve rotayı çizme ----------
// Sonlu (NaN/Infinity olmayan) gerçek bir sayı mı?
const sonluSayi = (v) => typeof v === "number" && Number.isFinite(v);

// Kabul edilen yanıt: GeoJSON Feature (backend'in formatı) ya da çıplak
// LineString. Geometri LineString olmalı ve en az 2 geçerli [boylam, enlem]
// içermeli. Değilse hata fırlatır; rota haritaya ÇİZİLMEZ.
function rotaGeometrisiAl(veri) {
  const hatali = new Error("The server sent an invalid route.");
  if (!veri || typeof veri !== "object") throw hatali;
  const g = veri.type === "Feature" ? veri.geometry : veri;
  if (!g || g.type !== "LineString" || !Array.isArray(g.coordinates)) throw hatali;
  if (g.coordinates.length < 2) throw hatali; // tek nokta çizgi değildir
  // GeoJSON sırası [boylam, enlem]: c[0] boylam (−180…180), c[1] enlem (−90…90).
  const gecerliNokta = (c) => Array.isArray(c) && c.length >= 2 &&
    sonluSayi(c[0]) && sonluSayi(c[1]) &&
    Math.abs(c[0]) <= 180 && Math.abs(c[1]) <= 90;
  if (!g.coordinates.every(gecerliNokta)) throw hatali;
  return g;
}

// L.geoJSON, GeoJSON'un [boylam, enlem] sırasını Leaflet'in [enlem, boylam]
// sırasına kendisi çevirir. Sadece doğrulanmış geometri buraya gelir.
function rotaCiz(geometri, ozellikler) {
  // İki katmanlı çizgi: altta koyu, kalın bir "kenar", üstte camgöbeği çizgi.
  // Böylece rota sarı/turuncu eğim katmanının ve açık renkli arazinin
  // üstünde de (projektörde bile) net seçilir.
  rotaKatmani = L.featureGroup([
    L.geoJSON(geometri, { style: { color: "#002b36", weight: 8, opacity: 0.7 } }),
    L.geoJSON(geometri, { style: { color: "#00e5ff", weight: 4.5, opacity: 1 } }),
  ]).addTo(map);

  const m = rotaMetrikleri(ozellikler);
  rotaKatmani.bindPopup(`Distance: ${m.mesafe} · Est. walking time: ${m.sure} · Max. slope: ${m.egim}`);
  rotaKutusuGoster(m);
  // maxZoom: çok kısa rotada (ör. başlangıç ve bitiş aynı DEM hücresinde,
  // backend 2 aynı noktalı çizgi döner) harita en yakın zoom'a zıplamasın.
  map.fitBounds(rotaKatmani.getBounds(), { padding: [40, 40], maxZoom: 16 });
}

// Backend'in properties alanlarını okunur metinlere çevirir.
// Alan yok → "—". Alan var ama sayısal/sonlu/negatif-olmayan değil → "geçersiz"
// (yanlış bir sayıyı, ör. negatif mesafeyi, kullanıcıya göstermeyiz).
function rotaMetrikleri(p) {
  const metin = (ad, bicim) => {
    const v = p[ad];
    if (v === undefined || v === null) return "—";
    if (!sonluSayi(v) || v < 0) {
      console.warn(`Geçersiz rota metriği ${ad}:`, v);
      return "invalid";
    }
    return bicim(v);
  };
  const tr = (v, basamak) => v.toLocaleString("en-US", { maximumFractionDigits: basamak });
  // Saati "1 sa 43 dk" biçimine çevirir (1,72 saat'ten daha kolay okunur).
  const saatDakika = (saat) => {
    const dk = Math.round(saat * 60);
    return dk < 60 ? `${dk} min` : `${Math.floor(dk / 60)} h ${dk % 60} min`;
  };
  return {
    mesafe: metin("distance_km", (v) => tr(v, 2) + " km"),
    sure: metin("estimated_time_hours", saatDakika),
    egim: metin("max_slope_deg", (v) => tr(v, 1) + "°"),
  };
}

// Sol alttaki kutuyu rota özetine çevirir: başlık + 3 metrik + ipucu.
// DOM ile kuruluyor (textContent), sunucudan gelen hiçbir şey HTML olarak yorumlanmaz.
function rotaKutusuGoster(m) {
  const d = durum._div;
  d.className = "durum-kutusu rota-ozeti";
  const satir = (etiket, deger, not) => {
    const s = document.createElement("div");
    s.className = "metrik";
    const e = document.createElement("span"); e.className = "etiket"; e.textContent = etiket;
    const v = document.createElement("b"); v.textContent = deger;
    s.append(e, v);
    if (not) { const n = document.createElement("span"); n.className = "not"; n.textContent = not; s.append(n); }
    return s;
  };
  const baslik = document.createElement("div");
  baslik.className = "baslik"; baslik.textContent = "Safe walking route";
  const ipucu = document.createElement("div");
  ipucu.className = "ipucu"; ipucu.textContent = "Click the map to start a new route.";
  d.replaceChildren(
    baslik,
    satir("Distance", m.mesafe),
    satir("Est. walking time", m.sure, "Tobler hiking model"),
    satir("Max. slope", m.egim, `limit: ${SLOPE_THRESHOLD_DEG}°`),
    ipucu,
  );
}

// ---------- 7) Bilim noktaları ----------
// Popup içeriğini DOM ile kuruyoruz (innerHTML değil): dosyadaki metinler
// HTML olarak yorumlanmaz, bozuk/kötü içerik sayfayı etkileyemez.
function el(etiket, metin, ozellikler = {}) {
  const e = document.createElement(etiket);
  if (metin) e.textContent = metin;
  Object.assign(e, ozellikler);
  return e;
}

function bilimPopup(p) {
  const kutu = el("div", "", { className: "bilim-popup" });
  kutu.append(el("h3", p.name || "Unnamed site"));
  if (p.image_preview_url) {
    // loading="lazy": resim sadece popup açılınca indirilir. Resmin yeri CSS'te
    // sabit oranla ayrılır, böylece popup açıldığı anda son boyutundadır ve
    // Leaflet haritayı doğru kaydırır (resim sonradan gelip popup'ı uzatmaz).
    kutu.append(el("img", "", { src: p.image_preview_url, alt: p.image_caption || "", loading: "lazy" }));
    const alt = [p.image_caption, p.image_credit].filter(Boolean).join(" · ");
    if (alt) kutu.append(el("div", alt, { className: "kucuk" }));
  }
  if (p.science_summary) kutu.append(el("p", p.science_summary));
  if (p.coordinate_accuracy) kutu.append(el("div", "Location accuracy: " + p.coordinate_accuracy, { className: "kucuk" }));
  if (p.image_gallery_url) {
    kutu.append(el("a", "Open raw image at NASA ↗", { href: p.image_gallery_url, target: "_blank", rel: "noopener" }));
  }
  return kutu;
}

async function bilimNoktalariniYukle() {
  try {
    const yanit = await fetch(SCIENCE_POINTS_URL);
    if (!yanit.ok) throw new Error("HTTP " + yanit.status);
    const veri = await yanit.json();
    L.geoJSON(veri, {
      // GeoJSON noktasını turuncu daire olarak çiz.
      pointToLayer: (_, latlng) => L.circleMarker(latlng, {
        radius: 7, color: "#000", weight: 1, fillColor: "#ff9f1c", fillOpacity: 0.95,
        // Noktaya tıklamak haritaya tıklama sayılmasın (yoksa rota başlangıcı olur).
        bubblingMouseEvents: false,
      }),
      onEachFeature: (f, katman) => {
        katman.bindTooltip(f.properties.name || "");
        katman.bindPopup(() => bilimPopup(f.properties), { maxWidth: 300, minWidth: 260 });
      },
    }).eachLayer((k) => bilimKatmani.addLayer(k));
  } catch (hata) {
    // Bilim noktaları ek özellik: yüklenemezse rota planlama yine çalışsın.
    console.warn("Bilim noktaları yüklenemedi (" + SCIENCE_POINTS_URL + "):", hata.message);
  }
}
bilimNoktalariniYukle();

durumGoster("Click the map to set a start point.");
