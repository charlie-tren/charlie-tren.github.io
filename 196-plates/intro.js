// 196 Plates intro: the search page's spinning globe and the dive to the city (design 369: one continuous camera, OSM raster to land on). It is a hook on a map the app owns:
//   const intro = runIntro(map, opts); intro.ready -> first frame; intro.go() -> the dive; intro.skip() -> the end state.
// opts: { base: the city's asset folder, bounds, land() -> { center, zoom, padding }, reduce, osm: layer id,
//   pinsAt(seconds) pops the app's pins in, onArrive() once the camera is down and the map is the
//   app's again, onDone() once the intro's layers are gone }.
// Everything that moves is a function of one time, frame(T).
(function () {
  window.runIntro = (map, o) => {
    const D2R = Math.PI / 180, SPIN = 4, LAT0 = 8, LON0 = 150, reduce = !!o.reduce;
    const MC = maplibregl.MercatorCoordinate;
    const el = map.getContainer();
    const W = el.clientWidth, H = el.clientHeight, phone = W < 761;
    const R = (phone ? .46 : .40) * Math.min(W, H), cy = (phone ? .42 : .5) * H;
    // camera 1.5 x the map height away (36.87 deg field of view): the sphere radius whose silhouette is R pixels
    const zoomFor = (r0, lat) => { const d = 1.5 * H, r = (r0 * r0 + r0 * Math.sqrt(r0 * r0 + d * d)) / d; return Math.log2(2 * Math.PI * r * Math.cos(lat * D2R) / 512); };
    const Z0 = zoomFor(R, LAT0), PADB = Math.max(0, H - 2 * cy);
    let BASE = o.base || "", GEN = 0; // GEN counts retargets: work started for an earlier city drops its result

    // the satellite: tiles on the dive path are hosted with the site (dive/), the rest come from EOX
    const EOX = (z, x, y) => `https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2024_3857/default/g/${z}/${y}/${x}.jpg`;
    let DIVE = new Set();
    const loadDive = () => { const g = GEN; DIVE = new Set();
      fetch(`${BASE}dive/manifest.json`).then(r => r.ok ? r.json() : []).then(a => { if (g === GEN) DIVE = new Set(a); }).catch(() => {}); };
    loadDive();
    const satUrl = (z, x, y) => DIVE.has(`${z}/${x}/${y}`) ? `${BASE}dive/${z}/${x}/${y}.jpg` : EOX(z, x, y);
    // a dive passes a zoom level every third of a second; 16 requests in flight (the default) cannot keep up
    maplibregl.setMaxParallelImageRequests(64);
    // MapLibre 5.24's image queue throws on a request it has already cancelled; the next request starts the queue again
    addEventListener("unhandledrejection", e => { if (/reading 'signal'/.test(String(e.reason && e.reason.message))) e.preventDefault(); });
    // a tile that fails or is cancelled comes back empty: MapLibre mishandles a rejection after it has dropped the request
    // (fully transparent: the old pixel was half-opaque blue, and tinted every failed tile)
    const BLANK = Uint8Array.from(atob("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNgYGBgAAAABQABeqhXUAAAAABJRU5ErkJggg=="), c => c.charCodeAt(0)).buffer;
    const token = window.__satToken = {};
    const tileLat = (y, z) => Math.atan(Math.sinh(Math.PI * (1 - 2 * y / 2 ** z))) / D2R;
    maplibregl.addProtocol("sat", async (req, abort) => {
      const [z, x, y] = req.url.slice(6).split("/").map(Number);
      try {
        const r = await fetch(satUrl(z, x, y), { signal: abort && abort.signal });
        if (!r.ok) return { data: BLANK.slice(0) };
        // EOX has no imagery of Antarctica, only flat white: tone it the way the globe texture is toned
        if (tileLat(y + 1, z) < -55 && typeof OffscreenCanvas === "function") return { data: await iceOff(await r.blob(), x, y, z) };
        return { data: await r.arrayBuffer() };
      } catch (e) { return { data: BLANK.slice(0) }; }
    });
    // the same formula as tone_antarctica.py, so the tiles meet the texture without a seam
    const ICE = lat => { const t = Math.min(1, Math.max(0, (-lat - 60) / 25)) ** .8; return [214 - 36 * t, 222 - 32 * t, 231 - 27 * t]; };
    const iceNoise = (lon, lat) => 1 + .05 * (.5 * Math.sin(.13 * lon + .9 * Math.sin(.05 * lon)) * Math.cos(.31 * lat) + .5 * Math.sin(.047 * lon - .21 * lat + 1.7));
    const iceTile = async (blob, x, y, z) => {
      const bm = await createImageBitmap(blob), n = bm.width, cv = new OffscreenCanvas(n, n), cx = cv.getContext("2d");
      cx.drawImage(bm, 0, 0); const im = cx.getImageData(0, 0, n, n), d = im.data, Z = 2 ** z;
      for (let j = 0; j < n; j++) {
        const lat = tileLat(y + (j + .5) / n, z), band = Math.min(1, Math.max(0, (-lat - 55) / 5)); if (!band) continue;
        const c = ICE(lat);
        for (let i = 0; i < n; i++) {
          const k = 4 * (j * n + i), mn = Math.min(d[k], d[k + 1], d[k + 2]), w = band * Math.min(1, Math.max(0, (mn - 200) / 45)); if (!w) continue;
          const f = iceNoise(((x + (i + .5) / n) / Z) * 360 - 180, lat);
          d[k] += (c[0] * f - d[k]) * w; d[k + 1] += (c[1] * f - d[k + 1]) * w; d[k + 2] += (c[2] * f - d[k + 2]) * w;
        }
      }
      cx.putImageData(im, 0, 0);
      return (await cv.convertToBlob({ type: "image/jpeg", quality: .9 })).arrayBuffer();
    };
    // the toning is 260k pixels of JavaScript a tile: it runs in two workers, from this same function, so the main thread keeps its frames
    let iceWs = null, iceId = 0; const icePending = new Map();
    const iceOff = (blob, x, y, z) => {
        if (iceWs === null) try {
            const code = `const D2R=${D2R};const tileLat=${tileLat};const ICE=${ICE};const iceNoise=${iceNoise};const iceTile=${iceTile};` +
                `onmessage=async e=>{const{id,blob,x,y,z}=e.data;try{const out=await iceTile(blob,x,y,z);postMessage({id,out},[out]);}catch(err){postMessage({id,err:String(err)});}};`;
            const url = URL.createObjectURL(new Blob([code], { type: "text/javascript" }));
            iceWs = [0, 1].map(() => { const w = new Worker(url); w.onmessage = e => { const p = icePending.get(e.data.id); icePending.delete(e.data.id); if (p) e.data.err ? p.rej(new Error(e.data.err)) : p.res(e.data.out); }; return w; });
        } catch (e) { iceWs = false; }
        if (iceWs) return new Promise((res, rej) => { const id = ++iceId; icePending.set(id, { res, rej }); iceWs[id & 1].postMessage({ id, blob, x, y, z }); }).catch(() => iceTile(blob, x, y, z));
        return iceTile(blob, x, y, z);
    };
    // the protocol outlives the intro by a few seconds, for tiles still in flight; a newer intro's protocol is left alone
    const dropProtocol = () => setTimeout(() => { if (window.__satToken === token) { try { maplibregl.removeProtocol("sat"); } catch (e) {} if (iceWs) iceWs.forEach(w => w.terminate()); } }, 4000);

    // ---- space: a deep gradient and a seeded starfield behind the transparent map, and the atmosphere's halo ----
    const sky = document.createElement("canvas"), halo = document.createElement("div");
    sky.className = "intro-sky"; halo.className = "intro-halo";
    el.parentNode.insertBefore(sky, el); el.parentNode.appendChild(halo);
    (() => {
      const dpr = Math.min(devicePixelRatio || 1, 2); sky.width = W * dpr; sky.height = H * dpr;
      const x = sky.getContext("2d"); x.scale(dpr, dpr);
      const g = x.createRadialGradient(W / 2, cy, R * .8, W / 2, cy, Math.max(W, H) * 1.1);
      g.addColorStop(0, "#0c1424"); g.addColorStop(.45, "#070b14"); g.addColorStop(1, "#030407");
      x.fillStyle = g; x.fillRect(0, 0, W, H);
      let s = 196; const rnd = () => { s = (s + 0x6D2B79F5) | 0; let t = Math.imul(s ^ (s >>> 15), 1 | s); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
      for (let i = 0, n = Math.round(W * H / 2600); i < n; i++) {
        const px = rnd() * W, py = rnd() * H, m = rnd() ** 3, a = .18 + m * .7, tint = rnd();
        x.fillStyle = tint < .15 ? `rgba(255,226,196,${a})` : tint > .85 ? `rgba(196,214,255,${a})` : `rgba(255,255,255,${a})`;
        x.beginPath(); x.arc(px, py, .35 + m * 1.1, 0, Math.PI * 2); x.fill();
      }
      const hs = 2.5 * R;
      Object.assign(halo.style, { width: hs + "px", height: hs + "px", left: (W / 2 - hs / 2) + "px", top: (cy - hs / 2) + "px" });
    })();

    // ---- the night side: soft twilight bands from a sun held to the camera's left ----
    const SUNV = [-1.0, 0.22, 0.38], sl = Math.hypot(...SUNV), TH = Math.acos(SUNV[2] / sl), BE = Math.atan2(SUNV[0], SUNV[1]);
    const sunFor = ([lon, lat]) => { const f = lat * D2R, la = Math.asin(Math.sin(f) * Math.cos(TH) + Math.cos(f) * Math.sin(TH) * Math.cos(BE));
      return [lon + Math.atan2(Math.sin(BE) * Math.sin(TH) * Math.cos(f), Math.cos(TH) - Math.sin(f) * Math.sin(la)) / D2R, la / D2R]; };
    // many faint steps, the same total dark as 7 steps of 16%, whose edges showed as rings on the night side
    const NSTEP = .5, NA = 1 - Math.pow(.84, 7 / (18 / NSTEP + 1));
    const night = ([lonS, latS]) => {
      lonS = ((lonS + 540) % 360) - 180;
      const sg = latS >= 0 ? 1 : -1, ps = Math.abs(latS) * D2R, feats = [];
      for (let e = -12; e <= 6; e += NSTEP) {
        const se = Math.sin(e * D2R), ring = [];
        for (let lon = -180; lon <= 180; lon += 2.5) {
          const a = Math.sin(ps), b = Math.cos(ps) * Math.cos((lon - lonS) * D2R), x = se / Math.hypot(a, b);
          const phi = x >= 1 ? 1.4844 : x <= -1 ? -1.4844 : Math.max(-1.4844, Math.min(1.4844, Math.asin(x) - Math.atan2(b, a)));
          ring.push([lon, sg * phi / D2R]);
        }
        ring.push([180, -sg * 85.05], [-180, -sg * 85.05], ring[0]);
        feats.push({ type: "Feature", properties: {}, geometry: { type: "Polygon", coordinates: [ring] } });
      }
      return { type: "FeatureCollection", features: feats };
    };

    // ---- the intro's layers, under the app's pins; everything that animates reads a global-state value ----
    const gs = k => ["global-state", k], clamp01 = e => ["min", 1, ["max", 0, e]];
    const setG = (k, v) => { v = Math.round(v * 1000) / 1000; if (!map.style) return; if (setG[k] !== v) { setG[k] = v; map.setGlobalStateProperty(k, v); } };
    // the tile size that draws one texel per screen pixel; on a 1x screen the dive asks one level finer, so while the next
    // level loads the tiles standing in for it are still at screen density. A high-density screen asks at screen density:
    // one level finer there is 16x the tiles of 256px slots, and cost a phone ~45% more stalling (4+4 filmed runs, 10/11/2026)
    const hiDpi = (devicePixelRatio || 1) >= 1.5, tileNeed = hiDpi ? 128 : 256, tile = hiDpi ? tileNeed : tileNeed / 2;
    const FADE_OUT = [Z0 + 1.6, Z0 + 3.2];
    let osmBefore = null;
    const below = () => map.getLayer("pins") ? "pins" : undefined;
    // MapLibre compiles a shader the first time a layer type is drawn in a projection: at zoom 8, where the globe goes flat, that
    // is the raster, line and icon programs together (~60 ms each, inside the dive's frames). Compile them while the globe still spins
    const WARM = { raster: 1, line: 1, symbolIcon: 1, projectionErrorMeasurement: 1 }; let warmQ = [], warmUse = null, warmAt = 0;
    const warmInit = () => { try {
      const P = map.painter, use = P.useProgram, seen = {}; if (typeof use !== "function") return; warmUse = use;
      P.useProgram = function (name, cfg, fsp, defs) {
        if (WARM[name] && !fsp && map.transform.zoom < 5) { const k = name + (cfg ? cfg.cacheKey : "") + defs; if (!seen[k]) { seen[k] = 1; warmQ.push([name, cfg, defs]); } }
        return use.apply(this, arguments); };
    } catch (e) {} };
    const warmStep = (T, now) => { if (!warmUse) return;
      if (GO !== null) return warmDone();
      if (T < 1.5 || now - warmAt < 350) return;
      if (warmQ.length) { warmAt = now; const [n, c, d] = warmQ.shift(); try { warmUse.call(map.painter, n, c, true, d); } catch (e) {} }
      else if (T > 5) warmDone(); };
    const warmDone = () => { try { delete map.painter.useProgram; } catch (e) {} warmUse = null; warmQ = []; };
    const OWN = { layers: ["pole", "day", "eox", "night"], sources: ["day", "eox", "night"] };
    const setup = () => {
      Object.entries({ nk: 1, hold: 1 }).forEach(([k, v]) => setG(k, v));
      map.setLayerZoomRange(o.osm, 8, 24); map.setPaintProperty(o.osm, "raster-fade-duration", 0);
      map.setProjection({ type: ["interpolate", ["linear"], ["zoom"], 5, "vertical-perspective", 8, "mercator"] });
      map.setSky({ "atmosphere-blend": ["interpolate", ["linear"], ["zoom"], 0, 1, 5, 1, 7, 0] });
      map.addSource("day", { type: "image", url: "day-1024.webp", coordinates: [[-180, 85.0511], [180, 85.0511], [180, -85.0511], [-180, -85.0511]] });
      map.addSource("eox", { type: "raster", tiles: ["sat://{z}/{x}/{y}"], tileSize: tile, maxzoom: 14,
        attribution: '<a href="https://cloudless.eox.at" target="_blank" rel="noopener">EOxCloudless</a> by EOX IT Services GmbH (Contains modified Copernicus Sentinel data 2024)' });
      map.addSource("night", { type: "geojson", data: night(sunFor([LON0, LAT0])) });
      map.setLayoutProperty(o.osm, "visibility", "none");
      { const ls = map.getStyle().layers, i = ls.findIndex(l => l.id === o.osm); osmBefore = ls[i + 1] && ls[i + 1].id; }
      map.setPaintProperty(o.osm, "raster-opacity", ["-", 1, gs("hold")]);
      // the globe's surface under everything: it fills the caps past 85 degrees that no image reaches (a black dot at the
      // south pole), in the toned ice colour of the texture's last row (tone_antarctica.py)
      map.addLayer({ id: "pole", type: "background", maxzoom: 8, paint: { "background-color": "rgb(177,189,203)" } }, map.getStyle().layers[0].id);
      map.addLayer({ id: "day", type: "raster", source: "day", maxzoom: 10, paint: { "raster-opacity": ["interpolate", ["linear"], ["zoom"], 7, 1, 10, 0], "raster-fade-duration": 0 } }, below());
      // the satellite holds until the basemap under it has loaded (hold), then crossfades; it never leaves a blank
      map.addLayer({ id: "eox", type: "raster", source: "eox", maxzoom: 14, minzoom: Z0 + .6, paint: { "raster-opacity": 1, "raster-fade-duration": 0 } }, below());
      map.addLayer({ id: "night", type: "fill", source: "night", paint: { "fill-color": "#02040a", "fill-antialias": false,
        "fill-opacity": ["interpolate", ["linear"], ["zoom"], FADE_OUT[0] - 1, ["*", NA, gs("nk")], FADE_OUT[0], 0] } }, below());
      map.jumpTo({ center: [LON0, LAT0], zoom: Z0, padding: { top: 0, bottom: PADB, left: 0, right: 0 } });
      warmInit();
    };
    if (map.style && map.getStyle()) setup(); else map.once("style.load", setup); // isStyleLoaded() is false while tiles load, after style.load has fired

    // the first frame needs only the small preloaded image, not the satellite tiles that sharpen it after
    let firstFrame; const ready = new Promise(r => { firstFrame = r; });
    map.on("render", function first() { if (map.style && map.getSource("day") && map.isSourceLoaded("day")) { map.off("render", first); performance.mark("globe-first-frame"); firstFrame(); } });

    // the spinning globe is one texture, sharp at its size on this screen, swapped in once the small one is up
    const SHARP_TEX = (devicePixelRatio || 1) * R * Math.PI > 2600 ? "globe/day-4096.webp" : "globe/day-2048.webp";
    ready.then(() => {
      // while the globe spins: the first levels of the dive imagery, and the satellite tiles for the globe end of the dive
      mosReady.then(() => { if (dead || !map.style) return; addMosaics(() => true); if (GO === null) { land = o.land(); start = map.getCenter().toArray(); buildCont(); prefetchCity(); } });
      if (!reduce) { const im = new Image(); im.src = SHARP_TEX; im.decode().then(() => { if (GO === null && !dead && map.style) map.getSource("day").updateImage({ url: SHARP_TEX }); }).catch(() => {}); } });

    // ---- the dive ----
    const lin = (t, a, b) => Math.min(1, Math.max(0, (t - a) / (b - a)));
    const sm = x => x * x * (3 - 2 * x);
    const TT = 2.7, TZ = 2.0, TE = 5.3, CF = .7, PLATE_T = 1.0;
    let GO = null, start = null, total = TE, contAt = null, land = null, dead = false;

    // ---- the dive's satellite: one pre-built image per half zoom level, cut to the view along the fixed path to the city,
    // at the screen's density (2x at most) at the deep end of its band, so no frame of the dive is drawn coarser than the
    // screen. Built by build_mosaics.py; without it the dive falls back to satellite tiles ----
    const PROFILE = phone ? "phone" : "desktop";
    let MOS = null;
    const nc = navigator.connection, slow = !!nc && (nc.saveData || /^(slow-2g|2g|3g)$/.test(nc.effectiveType || ""));
    const loadMos = () => { const g = GEN; return reduce || slow ? Promise.resolve() : fetch(`${BASE}mosaic/${PROFILE}/manifest.json`).then(r => r.ok ? r.json() : null)
      .then(m => { if (g === GEN && m && m.levels && m.levels.length) { MOS = m.levels; return ready.then(() => { if (g === GEN && !dead && map.style) map.setLayerZoomRange("eox", Z0 + .6, MOS[0].z0 + .02); }); } }).catch(() => {}); };
    let mosReady = loadMos();
    // the pieces are fetched in dive order (the first levels while the globe spins, the rest on the pick) and held as blobs;
    // each joins the map as a layer only about a second before the camera reaches its band, one a frame, and leaves once
    // the camera is past it, so the map carries a few dozen layers at a time rather than all of them
    const LEAD = 3.2, mosBlob = {}, mosFetchQ = [], mosLive = [];
    const mosAdded = {}, mosFail = {}; let fetch0 = 0, bytesIn = 0, pathBytes = 0, mosFetching = 0, mosNext = 0, mosOrder = null, mosAt = 0, pathN = 0, pathDone = 0, built = false;
    // requests in flight (Pages is HTTP/2, so the browser's 6-per-host cap does not apply). At 6 the ~350 small requests
    // of the desktop dive were round-trip bound: the last arrived ~14 s after load, and a pick before that waited
    const PAR = 24;
    const pump = () => { if (!fetch0 && mosFetchQ.length) fetch0 = performance.now();
      while (!dead && mosFetching < PAR && mosFetchQ.length) { const [i, j] = mosFetchQ.shift(), g = GEN; mosFetching++;
      fetch(`${BASE}mosaic/${PROFILE}/${MOS[i].chunks[j].file}`).then(r => r.blob()).then(x => { if (g !== GEN) return; bytesIn += x.size; mosBlob[i + "_" + j] = URL.createObjectURL(x); })
        .catch(() => { if (g === GEN) mosFail[i + "_" + j] = 1; }).finally(() => { mosFetching--; pump(); }); } };
    const addMosaics = which => { if (!MOS) return;
      if (!mosOrder) { mosOrder = []; MOS.forEach((L, i) => L.chunks.forEach((c, j) => mosOrder.push([i, j]))); }
      MOS.forEach((L, i) => { if (L.queued || !which(L)) return; L.queued = true; L.chunks.forEach((c, j) => mosFetchQ.push([i, j])); });
      // in the order the camera needs them; a level the camera never reaches goes last
      const key = i => !land || MOS[i].z0 - .45 < land.zoom ? i : 99 + i;
      mosFetchQ.sort((p, q) => key(p[0]) - key(q[0]) || p[1] - q[1]); pump(); };
    const dropMosaics = () => { MOS = null; mosFetchQ.length = 0;
      mosLive.forEach(([, id]) => { if (map.getLayer(id)) map.removeLayer(id); if (map.getSource(id)) map.removeSource(id); }); mosLive.length = 0;
      Object.values(mosBlob).forEach(u => URL.revokeObjectURL(u));
      if (map.getLayer("eox")) map.setLayerZoomRange("eox", Z0 + .6, 24); };
    const feed = T => {
      if (!MOS || !mosOrder || !map.style) return;
      const now = performance.now(), z = map.getZoom();
      const zAhead = GO === null ? MOS[0].z1 - .01 : contAt(Math.min(total, T - GO + LEAD)).zoom;
      const due = GO === null ? now - mosAt > 45 : true;
      // each piece joins once its blob is in (a late one never holds up the rest, and is never fetched a second time)
      let n = 0;
      for (let k = mosNext; k < mosOrder.length && n < 4 && due; k++) { const [i, j] = mosOrder[k], L = MOS[i], c = L.chunks[j], id = `mos${i}_${j}`;
        if (L.z0 - .45 >= zAhead) break;
        if (mosAdded[id]) { if (k === mosNext) mosNext++; continue; }
        const blob = mosBlob[i + "_" + j]; if (!blob) continue;
        if (L.z1 + .8 < z) { mosAdded[id] = 1; continue; } // the camera is past it
        if (n && L.z0 - .45 > z + .25) break; // a second piece in the same frame only when the camera is close to it
        mosAdded[id] = 1; n++; mosAt = now; if (k === mosNext) mosNext++;
        map.addSource(id, { type: "image", url: blob, coordinates: c.coords });
        const mn = L.z0 - .45 + .4 * j / L.chunks.length; // each piece fades in over the level below it, which stays until it is whole
        map.addLayer({ id, type: "raster", source: id, minzoom: mn, maxzoom: L.z1 + .8, paint: { "raster-opacity": ["interpolate", ["linear"], ["zoom"], mn, 0, mn + .8, 1], "raster-fade-duration": 0 } }, "night");
        mosLive.push([i, id]); }
      if (GO !== null && mosLive.length && MOS[mosLive[0][0]].z1 < z - 1) { const [, id] = mosLive.shift(); map.removeLayer(id); map.removeSource(id); }
    };
    // share of the view not drawn at screen density: outside the active level, or its image not in yet (a measure, not a gate)
    const coarse = () => { const tm = map.style.tileManagers && map.style.tileManagers.eox; if (!tm || map.getZoom() > 10.5) return 0;
      const ideal = Math.round(map.getZoom() + Math.log2(512 / tileNeed)), ids = tm.getRenderableIds();
      if (!ids.length) return 0; let n = 0; for (const id of ids) if (tm.getTileByID(id).tileID.canonical.z < Math.min(ideal, 14) - .5) n++;
      return +(n / ids.length).toFixed(2); };
    window.__mosCoarse = () => {
      if (!MOS) return coarse();
      if (dead) return 0;
      const z = map.getZoom(); if (z < MOS[0].z0) return coarse(); // the globe end of the dive is on satellite tiles
      const i = MOS.findIndex(L => z >= L.z0 && z < L.z1); if (i < 0) return z > MOS[MOS.length - 1].z1 ? 0 : 1;
      const L = MOS[i]; if (!L.chunks.every((c, j) => map.getSource(`mos${i}_${j}`) && map.isSourceLoaded(`mos${i}_${j}`))) return 1;
      // the part of the canvas the reader sees: the panel or the sheet covers the rest
      const pd = map.getPadding(), b0 = map.getBounds(), m = ll => MC.fromLngLat(ll);
      const cw = el.clientWidth, ch = el.clientHeight, nw = map.unproject([pd.left, pd.top]), se = map.unproject([cw - pd.right, ch - pd.bottom]);
      const b = isFinite(nw.lng + nw.lat + se.lng + se.lat) ? { getWest: () => nw.lng, getEast: () => se.lng, getNorth: () => nw.lat, getSouth: () => se.lat } : b0;
      const sh = 360 * Math.round(((b.getWest() + b.getEast()) / 2 - (L.box[0][0] + L.box[1][0]) / 2) / 360);
      const v0 = m([b.getWest() - sh, b.getNorth()]), v1 = m([b.getEast() - sh, b.getSouth()]), l0 = m(L.box[0]), l1 = m(L.box[1]);
      const ix = Math.max(0, Math.min(v1.x, l1.x) - Math.max(v0.x, l0.x)), iy = Math.max(0, Math.min(v1.y, l1.y) - Math.max(v0.y, l0.y));
      return +(1 - ix * iy / ((v1.x - v0.x) * (v1.y - v0.y))).toFixed(3); };
    const buildCont = () => {
      const L0 = start[0], A0 = start[1];
      let d = ((L0 - land.center[0]) % 360 + 360) % 360; if (d < 300) d += 360; // at least most of a turn, the way it was spinning
      const L1 = L0 - d, m0 = -SPIN * TT; // the spin's own speed in, at rest on the city out
      const lp = land.padding;
      contAt = t => {
        const s = Math.min(1, t / TT), s2 = s * s, s3 = s2 * s;
        const lon = (2 * s3 - 3 * s2 + 1) * L0 + (s3 - 2 * s2 + s) * m0 + (-2 * s3 + 3 * s2) * L1;
        const lat = A0 + (land.center[1] - A0) * sm(s);
        const u = lin(t, TZ, TE), k = sm(u), dive = (land.zoom - Z0) * (1 - Math.cos(Math.PI * u)) / 2;
        return { center: [lon, lat], zoom: Z0 - .2 * Math.sin(Math.PI * s) + dive,
          padding: { top: lp.top * k, bottom: PADB * (1 - k) + lp.bottom * k, left: lp.left * k, right: lp.right * k } };
      };
      for (const k in needT) delete needT[k];
      pathPrefetch(); built = true;
    };
    // the satellite tiles the dive will ask for, fetched as soon as the city is picked, in the order the camera needs them
    const pathPrefetch = () => {
      const seen = new Set(), list = [];
      for (let i = 0; i <= 40; i++) {
        const c = contAt(TZ + (TE - TZ) * i / 40), tz = Math.min(14, Math.round(c.zoom + Math.log2(512 / tile)));
        if (c.zoom < 3 || (MOS && c.zoom > MOS[0].z0 + .05)) continue; // the spin has the globe; the mosaics take over from their first level
        const f = c.zoom < 9 ? .6 : 1.05, m = MC.fromLngLat(c.center), n = 2 ** tz, hw = f * W / 2 / (512 * 2 ** c.zoom), hh = f * H / 2 / (512 * 2 ** c.zoom);
        for (let x = Math.floor((m.x - hw) * n); x <= Math.floor((m.x + hw) * n); x++)
          for (let y = Math.max(0, Math.floor((m.y - hh) * n)); y <= Math.min(n - 1, Math.floor((m.y + hh) * n)); y++) {
            const k = tz + "/" + ((x % n) + n) % n + "/" + y; if (!seen.has(k)) { seen.add(k); list.push([tz, ((x % n) + n) % n, y]); } }
      }
      pathN = list.length; pathDone = 0; if (!fetch0) fetch0 = performance.now();
      const g = GEN; let i = 0; const next = () => { if (i >= list.length || dead || g !== GEN) return; const [z, x, y] = list[i++];
        fetch(satUrl(z, x, y)).then(r => r.blob()).then(x => { if (g === GEN) { bytesIn += x.size; pathBytes += x.size; } }).catch(() => {}).finally(() => { if (g === GEN) pathDone++; next(); }); };
      for (let k = 0; k < PAR; k++) next();
    };
    // the city's OSM tiles, fetched the moment a city is picked so the cache has them when the camera arrives
    const prefetchCity = () => {
      const st = map.style && map.getStyle(), src = st && st.sources[o.osm]; if (!src || !src.tiles) return;
      const b = o.bounds, pad = .6, w = b[1][0] - b[0][0], h = b[1][1] - b[0][1];
      const lo = [b[0][0] - w * pad, b[0][1] - h * pad], hi = [b[1][0] + w * pad, b[1][1] + h * pad];
      const xy = (ll, z) => { const m = MC.fromLngLat(ll); return [Math.floor(m.x * 2 ** z), Math.floor(m.y * 2 ** z)]; };
      const zf = Math.floor(land.zoom) + 1;
      for (let z = Math.max(0, zf - 3); z <= Math.min(zf, 19); z++) {
        const [x0, y0] = xy(lo, z), [x1, y1] = xy(hi, z);
        for (let x = x0; x <= x1; x++) for (let y = Math.min(y0, y1); y <= Math.max(y0, y1); y++)
          fetch(src.tiles[0].replace("{z}", z).replace("{x}", x).replace("{y}", y), { mode: "cors", credentials: "omit" }).catch(() => {});
      }
    };

    // ---- one clock ----
    let lastT = null, t0 = null, lastNight = null, osmOn = false, baseIn = null, arrivedAt = null, cleaned = false, arrive, done;
    const arrived = new Promise(r => { arrive = r; }), finished = new Promise(r => { done = r; });
    const clock = () => (performance.now() - t0) / 1000;
    function frame(T) {
      if (dead || !map.style) return; // no style while the WebGL context is lost
      try { feed(T); } catch (e) {} // a style that is mid-rebuild refuses layers
      if (GO === null) { // spinning; the night follows the sun held to the camera's left
        warmStep(T, performance.now());
        const lon = LON0 - (reduce ? 0 : SPIN * T);
        map.jumpTo({ center: [lon, LAT0] });
        if (lastNight === null || Math.abs(lon - lastNight) > .25) { lastNight = lon; const s = map.getSource("night"); if (s) s.setData(night(sunFor([lon, LAT0]))); }
        return;
      }
      // the landing levels' pieces not yet in as the camera nears them: the ease waits for them, 0.6 s at most
      lastT = T;
      const t = T - GO;
      halo.style.opacity = 1 - lin(t, 0, .6); sky.style.opacity = 1 - lin(t, TZ, TE - .4);
      setG("nk", 1 - lin(t, 0, .8));
      // the hand-off to OSM: OSM on beneath from 1.3 s out (its tiles for this zoom and one below are cached), then an eased
      // crossfade from the last half second of the dive, as soon as every OSM tile in view is in (or after 0.6 s more)
      const tc = (reduce ? 0 : total) - .5;
      if (t >= tc - .8 && !osmOn) { osmOn = true; map.moveLayer(o.osm, below()); map.setLayoutProperty(o.osm, "visibility", "visible"); }
      if (baseIn === null && t >= tc && osmOn) baseIn = t; // never waits: the camera does not pause
      setG("hold", baseIn === null ? 1 : 1 - sm(lin(t, baseIn, baseIn + CF)));
      if (arrivedAt === null) {
        if (o.layoutAt) o.layoutAt(reduce ? 1 : sm(lin(t, TZ, TE)));
        if (reduce) map.jumpTo(land);
        else {
          const c = contAt(Math.min(t, total));
          map.jumpTo(c);
        }
      }
      if ((reduce || t >= total) && baseIn !== null && t >= baseIn + CF) {
        if (arrivedAt === null) { arrivedAt = t; map.setProjection({ type: "mercator" }); map.jumpTo(land); sky.style.display = halo.style.display = "none"; arrive(); }
        // the plates pop in, each on its own beat
        const pt = t - arrivedAt; o.pinsAt(reduce ? 9 : pt);
        if (reduce || pt >= PLATE_T) cleanup();
      }
    }
    const loop = () => { try { frame(clock()); } catch (e) { if (!/not done loading/.test(e.message)) console.error(e); } if (!dead) requestAnimationFrame(loop); }; // a map mid-rebuild refuses style calls
    const cleanup = () => {
      if (cleaned || !map.style) return; cleaned = true; dead = true;
      mosLive.forEach(([, id]) => { if (map.getLayer(id)) map.removeLayer(id); if (map.getSource(id)) map.removeSource(id); });
      Object.values(mosBlob).forEach(u => URL.revokeObjectURL(u));
      OWN.layers.forEach(id => map.getLayer(id) && map.removeLayer(id));
      OWN.sources.forEach(id => map.getSource(id) && map.removeSource(id));
      map.setLayerZoomRange(o.osm, 0, 24); map.setPaintProperty(o.osm, "raster-fade-duration", 100);
      map.setPaintProperty(o.osm, "raster-opacity", 1); if (osmBefore && map.getLayer(osmBefore)) map.moveLayer(o.osm, osmBefore);
      map.setSky({ "atmosphere-blend": 0 }); map.setProjection({ type: "mercator" });
      dropProtocol(); warmDone();
      sky.remove(); halo.remove();
      done();
    };
    ready.then(() => { if (t0 === null) { t0 = performance.now(); requestAnimationFrame(loop); } });

    // share of the dive's imagery in the cache (a mosaic piece weighs about five satellite tiles)
    const progress = () => { if (reduce || slow) return 1; if (!built) return 0;
      let need = pathN, have = pathDone;
      if (MOS) MOS.forEach((L, i) => { if (L.z0 - .45 >= land.zoom) return;
        L.chunks.forEach((c, j) => { need += 5; if (mosBlob[i + "_" + j] || mosFail[i + "_" + j]) have += 5; }); });
      return need ? Math.min(1, have / need) : 1; };
    // the dive need not wait for everything: each piece still to come only has to arrive before the camera reaches its
    // level (the first mosaic level is 3.2 s in, the last 4.7 s), projected from the rate so far with a margin. A piece
    // that is late anyway leaves the level below it on screen, never a gap.
    const MARGIN = 1, needT = {};
    const zoomT = z => needT[z] !== undefined ? needT[z] : (needT[z] = (() => { for (let t = 0; t <= total; t += .05) if (contAt(t).zoom >= z) return t; return total; })());
    const levelT = i => zoomT(MOS[i].z0 - .45);
    const safe = () => { if (reduce || slow) return true; if (!built || !fetch0) return false;
      const el = (performance.now() - fetch0) / 1000;
      if (el < 1 || !bytesIn) return progress() >= 1;
      const rate = bytesIn / el, tileB = pathDone ? pathBytes / pathDone : 15e3; // bytes a second since the first request
      let q = (pathN - pathDone) * tileB;
      if (q / rate > zoomT(3) - MARGIN) return false; // the satellite tiles for the globe end, needed from zoom 3 (pathPrefetch)
      if (!MOS) return true;
      const rest = (mosOrder || []).filter(([i, j]) => MOS[i].z0 - .45 < land.zoom && !mosBlob[i + "_" + j] && !mosFail[i + "_" + j]);
      const b = ([i, j]) => MOS[i].chunks[j].b || 5 * tileB; // sizes from the manifest
      // PAR pieces download at once and share the line: a piece lands after the ones ahead of it and about half of the
      // ones beside it (an in-order estimate let an immediate pick on live 4G draw half its frames soft)
      for (let k = 0; k < rest.length; k++) { q += b(rest[k]); let side = 0;
        for (let m = k + 1; m < Math.min(rest.length, k + PAR); m++) side += b(rest[m]);
        if ((q + side / 2) / rate > levelT(rest[k][0]) - MARGIN) return false; }
      return true; };
    return {
      ready, progress, safe,
      // another city, picked while the globe still spins: its bounds and imagery replace the first city's
      retarget(o2) {
        if (GO !== null || dead) return; GEN++; Object.assign(o, o2); BASE = o.base || "";
        mosFetchQ.length = 0; mosLive.forEach(([, id]) => { if (map.getLayer(id)) map.removeLayer(id); if (map.getSource(id)) map.removeSource(id); }); mosLive.length = 0;
        Object.values(mosBlob).forEach(u => URL.revokeObjectURL(u));
        [mosBlob, mosAdded, mosFail, needT].forEach(h => { for (const k in h) delete h[k]; });
        MOS = null; mosOrder = null; mosNext = mosAt = fetch0 = bytesIn = pathBytes = pathN = pathDone = 0; built = false;
        if (map.getLayer("eox")) map.setLayerZoomRange("eox", Z0 + .6, 24);
        loadDive(); const g = GEN; mosReady = loadMos();
        mosReady.then(() => { if (g !== GEN || dead || !map.style || GO !== null) return; addMosaics(() => true); land = o.land(); start = map.getCenter().toArray(); buildCont(); prefetchCity(); });
      },
      // the dive to the city; resolves once the camera is down
      go() {
        if (GO !== null) return arrived;
        land = o.land(); start = map.getCenter().toArray();
        // the dive never waits past the pick's cap: if the mosaics will not arrive in time it goes on the satellite tiles
        if (MOS && !safe() && !MOS[0].chunks.every((c, j) => mosBlob["0_" + j])) dropMosaics();
        GO = t0 === null ? 0 : clock();
        if (t0 === null) { t0 = performance.now(); requestAnimationFrame(loop); }
        if (MOS) mosFetchQ.splice(0, mosFetchQ.length, ...mosFetchQ.filter(([i]) => MOS[i].z0 - .45 < land.zoom));
        prefetchCity(); buildCont();
        addMosaics(() => true); // the rest of the dive's levels on the pick
        return arrived;
      },
      // straight to the end state: the camera on the city, the satellite gone as soon as the OSM tiles are in
      // the app is rebuilding the map: stop, touch nothing, let go() return
      abort() { if (dead) return; dead = true; cleaned = true; warmDone(); Object.values(mosBlob).forEach(u => URL.revokeObjectURL(u)); dropProtocol(); sky.remove(); halo.remove(); arrive(); done(); },
      skip() { if (GO === null || arrivedAt !== null) return; GO = clock() - total; },
      arrived, finished
    };
  };
})();
