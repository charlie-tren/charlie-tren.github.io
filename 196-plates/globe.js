// The search page's globe: EOX Sentinel-2 day imagery, NASA Black Marble lights on the night side, a starfield.
// Loaded only on the search page, after three.js. Globe.start(host) resolves once the first frame is drawn.
window.Globe = (function () {
  const D2R = Math.PI / 180, FOV = 30, SPIN = 4; // degrees of longitude a second
  const SUN = [-1.0, 0.22, 0.38];               // from the left: the day-night line runs through the right third
  const ease = x => x < .5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2;
  const VERT = `
    varying vec2 vUv; varying vec3 vN; varying vec3 vO; varying vec3 vP;
    void main() { vUv = uv; vO = normal; vN = normalize(mat3(modelMatrix) * normal);
      vec4 w = modelMatrix * vec4(position, 1.0); vP = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }`;
  const FRAG = `
    uniform sampler2D dayT, lightT, landT; uniform vec3 sun;
    varying vec2 vUv; varying vec3 vN; varying vec3 vO; varying vec3 vP;
    void main() {
      float lat = asin(clamp(vO.y, -1.0, 1.0));
      float m = log(tan(0.785398 + clamp(lat, -1.4844, 1.4844) * 0.5));
      vec2 uv = vec2(vUv.x, 0.5 + m / 6.283185);
      vec3 day = texture2D(dayT, uv).rgb * mix(1.0, 0.7, smoothstep(1.05, 1.3, abs(lat)));
      float lights = texture2D(lightT, uv).r, land = texture2D(landT, uv).r;
      vec3 N = normalize(vN), V = normalize(cameraPosition - vP), L = normalize(sun);
      float ndl = dot(N, L);
      float lit = smoothstep(-0.10, 0.22, ndl);
      vec3 dayC = day * (0.06 + 0.94 * 1.12 * max(ndl, 0.0));
      vec3 nightC = day * vec3(0.05, 0.06, 0.09) + vec3(1.0, 0.74, 0.42) * smoothstep(0.05, 0.8, lights) * 1.25;
      vec3 col = mix(nightC, dayC, lit);
      vec3 H = normalize(L + V);
      col += vec3(1.0, 0.95, 0.86) * pow(max(dot(N, H), 0.0), 220.0) * 0.14 * (1.0 - land) * smoothstep(0.0, 0.3, ndl);
      float fr = pow(1.0 - max(dot(N, V), 0.0), 2.6);
      col += vec3(0.32, 0.58, 1.0) * fr * (0.12 + 0.75 * smoothstep(-0.3, 0.45, ndl));
      gl_FragColor = vec4(col, 1.0);
    }`;
  // the atmosphere: a glow outside the limb, brightest on the sun side, faded out before its own sphere's edge
  const GLOW = `
    uniform vec3 sun; varying vec3 vP;
    void main() {
      vec3 D = normalize(vP - cameraPosition), C = -cameraPosition;
      vec3 p = cameraPosition + D * dot(C, D);
      float h = length(p);
      if (h < 1.0) discard;
      float g = (exp(-(h - 1.0) * 26.0) * 0.95 + exp(-(h - 1.0) * 7.0) * 0.18) * smoothstep(1.34, 1.18, h);
      float s = dot(normalize(p), normalize(sun));
      float k = 0.28 + 0.72 * smoothstep(-0.55, 0.75, s);
      vec3 o = mix(vec3(0.22, 0.45, 1.0), vec3(0.62, 0.82, 1.0), exp(-(h - 1.0) * 40.0)) * g * k;
      gl_FragColor = vec4(o, max(o.r, max(o.g, o.b)));
    }`;

  function start(host, opt) {
    const T = THREE, reduce = !!opt.reduce, base = opt.base || "globe/";
    const sky = document.createElement("canvas"), cv = document.createElement("canvas");
    sky.className = "globe-sky"; cv.className = "globe-gl";
    host.prepend(cv); host.prepend(sky);
    const renderer = new T.WebGLRenderer({ canvas: cv, antialias: true, alpha: true, powerPreference: "high-performance" });
    renderer.setClearColor(0x000000, 0);
    const scene = new T.Scene(), camera = new T.PerspectiveCamera(FOV, 1, 0.05, 100);
    const sun = new T.Vector3(...SUN).normalize();
    const loader = new T.TextureLoader(), aniso = renderer.capabilities.getMaxAnisotropy();
    const tex = url => new Promise((res, rej) => loader.load(base + url, t => { t.anisotropy = aniso; res(t); }, undefined, rej));
    const mat = new T.ShaderMaterial({ uniforms: { dayT: { value: null }, lightT: { value: null }, landT: { value: null }, sun: { value: sun } }, vertexShader: VERT, fragmentShader: FRAG });
    const glowMat = new T.ShaderMaterial({ uniforms: { sun: { value: sun } }, vertexShader: "varying vec3 vP; void main() { vec4 w = modelMatrix * vec4(position, 1.0); vP = w.xyz; gl_Position = projectionMatrix * viewMatrix * w; }",
      fragmentShader: GLOW, side: T.BackSide, transparent: true, depthWrite: false,
      blending: T.CustomBlending, blendSrc: T.OneFactor, blendDst: T.OneFactor, blendSrcAlpha: T.OneFactor, blendDstAlpha: T.OneFactor });
    const latG = new T.Group(), spin = new T.Group();
    scene.add(latG); latG.add(spin);
    const geo = new T.SphereGeometry(1, 160, 112), glowGeo = new T.SphereGeometry(1.35, 80, 56);
    spin.add(new T.Mesh(geo, mat)); scene.add(new T.Mesh(glowGeo, glowMat));

    let W = 0, H = 0, R = 0, phone = false;
    const layout = () => {
      W = host.clientWidth; H = host.clientHeight; phone = W < 761;
      const dpr = Math.min(window.devicePixelRatio || 1, 2);
      R = (phone ? .46 : .40) * Math.min(W, H);
      const cx = W / 2, cy = (phone ? .42 : .5) * H;
      renderer.setPixelRatio(dpr); renderer.setSize(W, H, false);
      camera.aspect = W / H; camera.setViewOffset(W, H, W / 2 - cx, H / 2 - cy, W, H);
      sky.width = W * dpr; sky.height = H * dpr;
      const c = sky.getContext("2d"); c.setTransform(dpr, 0, 0, dpr, 0, 0);
      const g = c.createRadialGradient(cx, cy, R * .8, cx, cy, Math.max(W, H) * 1.1);
      g.addColorStop(0, "#0c1424"); g.addColorStop(.45, "#070b14"); g.addColorStop(1, "#030407");
      c.fillStyle = g; c.fillRect(0, 0, W, H);
      let s = 196; const rnd = () => { s = (s + 0x6D2B79F5) | 0; let t = Math.imul(s ^ (s >>> 15), 1 | s); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
      for (let i = 0, n = Math.round(W * H / 2600); i < n; i++) {
        const x = rnd() * W, y = rnd() * H, m = rnd() ** 3, a = .18 + m * .7, tint = rnd();
        c.fillStyle = tint < .15 ? `rgba(255,226,196,${a})` : tint > .85 ? `rgba(196,214,255,${a})` : `rgba(255,255,255,${a})`;
        c.beginPath(); c.arc(x, y, .35 + m * 1.1, 0, Math.PI * 2); c.fill();
      }
    };
    // camera distance that gives the sphere a silhouette radius of r pixels
    const dist = r => 1 / Math.sin(Math.atan(2 * r / H * Math.tan(FOV * D2R / 2)));
    let lon = 150, lat = 8, zoom = 1, raf = 0, dead = false, last = 0;
    const draw = () => {
      spin.rotation.y = -(90 + lon) * D2R; latG.rotation.x = lat * D2R;
      camera.position.set(0, 0, dist(R * zoom)); camera.lookAt(0, 0, 0); camera.updateProjectionMatrix();
      renderer.render(scene, camera);
    };
    const loop = now => {
      if (dead) return;
      if (last) lon -= SPIN * (now - last) / 1000;
      last = now; draw(); raf = requestAnimationFrame(loop);
    };
    const onResize = () => { layout(); draw(); };

    return Promise.all([tex("day-2048.webp"), tex("lights-2048.webp"), tex("land-1024.webp")]).then(([day, lights, land]) => {
      mat.uniforms.dayT.value = day; mat.uniforms.lightT.value = lights; mat.uniforms.landT.value = land;
      layout(); draw();
      performance.mark("globe-first-frame");
      host.classList.add("globe-on");
      addEventListener("resize", onResize);
      if (!reduce) raf = requestAnimationFrame(loop);
      // the 4096 day texture on large or high-density desktop screens, once the page has loaded or 3 s have passed
      const big = !phone && ((window.devicePixelRatio || 1) >= 2 || innerWidth >= 1400);
      if (big) {
        let asked = false;
        const swap = () => { if (asked || dead) return; asked = true;
          tex("day-4096.webp").then(t => { if (dead) return t.dispose(); const old = mat.uniforms.dayT.value; mat.uniforms.dayT.value = t; old.dispose(); if (reduce) draw(); }).catch(() => {}); };
        if (document.readyState === "complete") swap(); else { addEventListener("load", swap, { once: true }); setTimeout(swap, 3000); }
      }
      return {
        // ease round to a place over ms, pushing in a little, then resolve
        turnTo(toLon, toLat, ms) {
          if (reduce || dead) return Promise.resolve();
          cancelAnimationFrame(raf);
          const l0 = lon, a0 = lat, t0 = performance.now();
          let dl = ((toLon - l0) % 360 + 540) % 360 - 180;
          return new Promise(res => {
            const step = now => {
              if (dead) return res();
              const e = ease(Math.min(1, (now - t0) / ms));
              lon = l0 + dl * e; lat = a0 + (toLat - a0) * e; zoom = 1 + .5 * e; draw();
              if (e < 1) raf = requestAnimationFrame(step); else res();
            };
            raf = requestAnimationFrame(step);
          });
        },
        destroy() {
          dead = true; cancelAnimationFrame(raf); removeEventListener("resize", onResize);
          [mat.uniforms.dayT.value, mat.uniforms.lightT.value, mat.uniforms.landT.value].forEach(t => t && t.dispose());
          mat.dispose(); glowMat.dispose(); geo.dispose(); glowGeo.dispose();
          renderer.dispose(); renderer.forceContextLoss(); cv.remove(); sky.remove();
        }
      };
    }, e => { renderer.dispose(); cv.remove(); sky.remove(); throw e; });
  }
  return { start };
})();
