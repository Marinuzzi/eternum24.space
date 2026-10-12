// Nuvole reali sul mappamondo, condivise dalle pagine di eternum24.space.
// Fonte primaria: mappa mondiale EUMETSAT (infrarosso 10.8 µm, una ogni 3 ore), con l'ora esatta dell'immagine.
// Riserva: clouds.matteason.co.uk (stessa fonte, già elaborata). Ogni 30 minuti si controlla se c'è una mappa nuova;
// se un download fallisce resta quella precedente.

const LAYER = "mumi:worldcloudmap_ir108";
const CAPS = `https://view.eumetsat.int/geoserver/mumi/worldcloudmap_ir108/ows?service=WMS&request=GetCapabilities&version=1.3.0`;
const MAP = t => `https://view.eumetsat.int/geoserver/ows?service=WMS&request=GetMap&version=1.3.0&layers=${LAYER}` +
  `&styles=&format=image/png&crs=EPSG:4326&bbox=-90,-180,90,180&width=2048&height=1024&time=${encodeURIComponent(t)}`;
const RISERVA = "https://clouds.matteason.co.uk/images/2048x1024/clouds-alpha.png";
const OGNI = 30 * 60 * 1000;

function carica(url) {
  return new Promise((ok, ko) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => ok(img);
    img.onerror = () => ko(new Error("immagine non disponibile"));
    img.src = url;
  });
}

async function ultimaOra() {
  const r = await fetch(CAPS, { cache: "no-store" });
  const xml = await r.text();
  const m = xml.match(/<Dimension name="time"[^>]*default="([^"]+)"/);
  if (!m) throw new Error("ora non trovata");
  return m[1];
}

// Infrarosso grezzo → nuvole bianche su trasparente: più è freddo (chiaro), più è nuvola.
// Oltre i 60° di latitudine il segnale si confonde con ghiacci e zone senza dati: si sfuma fino a 76°.
function inNuvole(img) {
  const c = document.createElement("canvas");
  c.width = img.naturalWidth; c.height = img.naturalHeight;
  const g = c.getContext("2d", { willReadFrequently: true });
  g.drawImage(img, 0, 0);
  const d = g.getImageData(0, 0, c.width, c.height), p = d.data;
  for (let y = 0; y < c.height; y++) {
    const lat = Math.abs(90 - (y + .5) * 180 / c.height);
    const fade = lat <= 60 ? 1 : lat >= 76 ? 0 : 1 - (lat - 60) / 16;
    for (let x = 0; x < c.width; x++) {
      const i = (y * c.width + x) * 4;
      let a = (p[i] - 110) / 90;
      a = a <= 0 ? 0 : a >= 1 ? 1 : a * a * (3 - 2 * a);
      const v = Math.round(a * fade * 255);
      p[i] = p[i + 1] = p[i + 2] = v; p[i + 3] = 255;
    }
  }
  g.putImageData(d, 0, 0);
  return c;
}

function dissolvi(material, verso, ms = 900) {
  const da = material.opacity, a = verso;
  return new Promise(ok => {
    const t0 = performance.now();
    const passo = now => {
      const k = Math.min(1, (now - t0) / ms);
      material.opacity = da + (a - da) * k;
      k < 1 ? requestAnimationFrame(passo) : ok();
    };
    requestAnimationFrame(passo);
  });
}

/**
 * Collega le nuvole reali a un materiale three.js (MeshBasicMaterial con blending additivo).
 * onUpdate({ ora: Date|null, fonte }) viene chiamato a ogni nuova mappa applicata.
 */
export function nuvoleReali(THREE, material, { onUpdate = () => {}, opacita = material.opacity } = {}) {
  let mostrata = null, prima = true;

  async function applica(tex, info) {
    const vecchia = material.map;
    if (!prima) await dissolvi(material, 0);
    material.map = tex; material.alphaMap = tex; material.needsUpdate = true;
    if (vecchia && vecchia !== tex) vecchia.dispose();
    if (prima) material.opacity = 0;
    prima = false;
    await dissolvi(material, opacita);
    onUpdate(info);
  }

  async function aggiorna() {
    let ora = null;
    try {
      ora = await ultimaOra();
      if (ora === mostrata) return;
      const tex = new THREE.CanvasTexture(inNuvole(await carica(MAP(ora))));
      tex.colorSpace = THREE.NoColorSpace;
      await applica(tex, { ora: new Date(ora), fonte: "EUMETSAT" });
      mostrata = ora;
      return;
    } catch (e) {
      console.warn("Nuvole EUMETSAT non disponibili, uso la riserva", e);
    }
    if (mostrata) return;                         // meglio la mappa già mostrata che una riserva più vecchia
    try {
      const slot = Math.floor(Date.now() / (3 * 3600 * 1000));
      const tex = new THREE.Texture(await carica(`${RISERVA}?v=${slot}`));
      tex.needsUpdate = true;
      await applica(tex, { ora: null, fonte: "EUMETSAT" });
      mostrata = "riserva";
    } catch (e) {
      console.warn("Nuvole non disponibili", e);
    }
  }

  aggiorna();
  setInterval(aggiorna, OGNI);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) aggiorna(); });
}

export function etichettaNuvole({ ora, fonte }) {
  if (!ora) return `☁ ${fonte}`;
  const oggi = new Date().toLocaleDateString("it-IT", { timeZone: "Europe/Rome" });
  const giorno = ora.toLocaleDateString("it-IT", { timeZone: "Europe/Rome", day: "2-digit", month: "2-digit" });
  const hhmm = ora.toLocaleTimeString("it-IT", { timeZone: "Europe/Rome", hour: "2-digit", minute: "2-digit" });
  return `☁ ${fonte} · ${ora.toLocaleDateString("it-IT", { timeZone: "Europe/Rome" }) === oggi ? hhmm : giorno + " " + hhmm}`;
}
