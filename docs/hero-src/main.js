/* LAION-fMRI homepage hero.
 *
 * Renders the brain mesh as ~1800 instanced image sprites sampled from
 * a stimulus atlas, with gentle Y rotation and mouse parallax. Single
 * draw call, ES2020, no React. Mounted via window.LaionFmriHero.init.
 */

import {
  BufferAttribute,
  BufferGeometry,
  Color,
  Group,
  InstancedBufferAttribute,
  InstancedBufferGeometry,
  LineBasicMaterial,
  LineSegments,
  Mesh,
  PerspectiveCamera,
  Plane,
  PlaneGeometry,
  Raycaster,
  Scene,
  ShaderMaterial,
  TextureLoader,
  Vector2,
  Vector3,
  WebGLRenderer,
  WireframeGeometry,
  DoubleSide,
} from "three";

const VERTEX_SHADER = `
  attribute vec3 aInstancePos;
  attribute float aTileIndex;
  attribute float aJitter;

  varying vec2 vUv;
  varying float vTileIndex;
  varying float vDepth;
  varying float vJitter;
  varying float vPop;

  uniform float uSpriteSize;
  uniform vec3 uMouseWorld;
  uniform float uMouseRadius;
  uniform float uMouseStrength;

  void main() {
    vec4 worldPos = modelMatrix * vec4(aInstancePos, 1.0);
    float distToMouse = distance(worldPos.xyz, uMouseWorld);
    float pop = (1.0 - smoothstep(0.0, uMouseRadius, distToMouse)) * uMouseStrength;
    vPop = pop;

    vec4 mvCenter = viewMatrix * worldPos;
    // Pull the popped sprites slightly toward the camera so they layer
    // above their neighbours instead of just inflating in place.
    mvCenter.z += pop * 0.08;

    float popScale = 1.0 + pop * 0.7;
    float scale = uSpriteSize * (0.7 + 0.6 * aJitter) * popScale;
    vec2 corner = position.xy * scale;
    vec4 mvPos = mvCenter + vec4(corner, 0.0, 0.0);
    gl_Position = projectionMatrix * mvPos;
    vUv = vec2(position.x + 0.5, 0.5 - position.y);
    vTileIndex = aTileIndex;
    vDepth = -mvCenter.z;
    vJitter = aJitter;
  }
`;

const FRAGMENT_SHADER = `
  precision highp float;

  uniform sampler2D uAtlas;
  uniform float uGrid;
  uniform float uNear;
  uniform float uFar;
  uniform vec3 uTintCool;
  uniform vec3 uTintWarm;
  uniform float uOpacity;

  varying vec2 vUv;
  varying float vTileIndex;
  varying float vDepth;
  varying float vJitter;
  varying float vPop;

  void main() {
    float idx = floor(vTileIndex + 0.5);
    float col = mod(idx, uGrid);
    float row = floor(idx / uGrid);
    vec2 atlasUv = (vec2(col, row) + vUv) / uGrid;
    vec4 c = texture2D(uAtlas, atlasUv);

    // Depth fade: front sprites bright + warm, back sprites slightly dimmed
    // but never crushed — wireframe carries depth perception now.
    float depthT = clamp((vDepth - uNear) / (uFar - uNear), 0.0, 1.0);
    float dim = mix(1.25, 0.78, depthT);
    vec3 tint = mix(uTintWarm, uTintCool, depthT);
    vec3 col3 = c.rgb * dim;
    col3 = mix(col3, col3 * tint, 0.22);
    col3 = clamp(col3 * 1.15, 0.0, 1.0);

    // Hover pop: brighten and slightly desaturate-toward-white.
    col3 = mix(col3, min(col3 * 1.18 + 0.04, vec3(1.0)), vPop);

    // Soft circular vignette inside each tile so they feel like glyphs not
    // hard squares — keeps the brain shape visible at sprite boundaries.
    vec2 d = vUv - 0.5;
    float r = dot(d, d);
    float edge = 1.0 - smoothstep(0.18, 0.245, r);

    float alpha = uOpacity * edge;
    if (alpha < 0.01) discard;
    gl_FragColor = vec4(col3, alpha);
  }
`;

function fsToThree(verts) {
  // FreeSurfer (x = LR, y = PA, z = IS) → Three (x = LR, y = IS, z = PA)
  const out = new Float32Array(verts.length * 3);
  for (let i = 0; i < verts.length; i++) {
    out[i * 3] = verts[i][0];
    out[i * 3 + 1] = verts[i][2];
    out[i * 3 + 2] = verts[i][1];
  }
  return out;
}

function combineHemispheres(brain) {
  const lh = fsToThree(brain.lh.vertices);
  const rh = fsToThree(brain.rh.vertices);
  const total = new Float32Array(lh.length + rh.length);
  total.set(lh, 0);
  total.set(rh, lh.length);
  return total;
}

function normalizeAndCenter(verts) {
  let cx = 0, cy = 0, cz = 0;
  const n = verts.length / 3;
  for (let i = 0; i < n; i++) {
    cx += verts[i * 3];
    cy += verts[i * 3 + 1];
    cz += verts[i * 3 + 2];
  }
  cx /= n; cy /= n; cz /= n;

  let maxR = 0;
  for (let i = 0; i < n; i++) {
    const x = verts[i * 3] - cx;
    const y = verts[i * 3 + 1] - cy;
    const z = verts[i * 3 + 2] - cz;
    const r = Math.sqrt(x * x + y * y + z * z);
    if (r > maxR) maxR = r;
  }

  const scale = maxR > 0 ? 1.0 / maxR : 1.0;
  const out = new Float32Array(verts.length);
  for (let i = 0; i < n; i++) {
    out[i * 3] = (verts[i * 3] - cx) * scale;
    out[i * 3 + 1] = (verts[i * 3 + 1] - cy) * scale;
    out[i * 3 + 2] = (verts[i * 3 + 2] - cz) * scale;
  }
  return out;
}

function mulberry32(seed) {
  let t = seed >>> 0;
  return function () {
    t = (t + 0x6D2B79F5) >>> 0;
    let x = t;
    x = Math.imul(x ^ (x >>> 15), x | 1);
    x ^= x + Math.imul(x ^ (x >>> 7), x | 61);
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  };
}

function sampleIndices(total, target, rng) {
  if (target >= total) {
    const all = new Uint32Array(total);
    for (let i = 0; i < total; i++) all[i] = i;
    return all;
  }
  const seen = new Set();
  const out = new Uint32Array(target);
  let written = 0;
  while (written < target) {
    const idx = Math.floor(rng() * total);
    if (seen.has(idx)) continue;
    seen.add(idx);
    out[written++] = idx;
  }
  return out;
}

function buildHeroDom(opts) {
  const root = opts.root;
  root.classList.add("lf-hero");
  root.innerHTML = `
    <div class="lf-hero__inner">
      <div class="lf-hero__text">
        <img class="lf-hero__logo" src="${opts.logoSrc}" alt="LAION-fMRI" />
        <h1 class="lf-hero__title">${opts.title}</h1>
        <p class="lf-hero__lede">${opts.lede}</p>
        <div class="lf-hero__ctas">
          <a class="lf-hero__btn lf-hero__btn--primary" href="${opts.primaryHref}">
            ${opts.primaryLabel}
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M5 12h14M13 5l7 7-7 7" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </a>
          ${opts.secondaryHref && opts.secondaryLabel ? `
          <a class="lf-hero__btn lf-hero__btn--ghost" href="${opts.secondaryHref}" ${opts.secondaryExternal ? 'target="_blank" rel="noopener"' : ""}>
            ${opts.secondaryLabel}
            <svg viewBox="0 0 24 24" aria-hidden="true">
              ${opts.secondaryExternal
                ? '<path d="M14 5h5v5M19 5l-9 9M5 9v10h10" stroke-linecap="round" stroke-linejoin="round"/>'
                : '<path d="M5 12h14M13 5l7 7-7 7" stroke-linecap="round" stroke-linejoin="round"/>'}
            </svg>
          </a>` : ""}
        </div>
        <div class="lf-hero__meta">
          ${opts.meta.map((s) => `<span>${s}</span>`).join("")}
        </div>
      </div>
      <div class="lf-hero__canvas-wrap">
        <canvas class="lf-hero__canvas" aria-label="Rotating brain made of stimulus thumbnails"></canvas>
        <div class="lf-hero__loading">loading brain…</div>
      </div>
      <button class="lf-hero__scroll-hint" type="button" aria-label="Scroll to documentation">
        <span>Documentation</span>
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M6 9l6 6 6-6" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
  `;
  return {
    canvas: root.querySelector(".lf-hero__canvas"),
    canvasWrap: root.querySelector(".lf-hero__canvas-wrap"),
    text: root.querySelector(".lf-hero__text"),
    logo: root.querySelector(".lf-hero__logo"),
    scrollBtn: root.querySelector(".lf-hero__scroll-hint"),
  };
}

async function loadJson(url) {
  const r = await fetch(url, { cache: "force-cache" });
  if (!r.ok) throw new Error(`Failed to load ${url}: ${r.status}`);
  return r.json();
}

function loadTexture(url) {
  return new Promise((resolve, reject) => {
    new TextureLoader().load(
      url,
      (tex) => resolve(tex),
      undefined,
      (err) => reject(err),
    );
  });
}

function buildWireframeMesh(brain, normVerts, themeIsDark) {
  // brain.lh.faces and brain.rh.faces index into per-hemisphere vertex arrays.
  // We've combined hemispheres into a single normalized array (lh first, rh
  // second) so rh face indices need to be offset by lh.vertices.length.
  const lhCount = brain.lh.vertices.length;
  const lhFaces = brain.lh.faces;
  const rhFaces = brain.rh.faces;
  const totalFaces = lhFaces.length + rhFaces.length;
  const indices = new Uint32Array(totalFaces * 3);
  for (let i = 0; i < lhFaces.length; i++) {
    indices[i * 3] = lhFaces[i][0];
    indices[i * 3 + 1] = lhFaces[i][1];
    indices[i * 3 + 2] = lhFaces[i][2];
  }
  for (let i = 0; i < rhFaces.length; i++) {
    const o = (lhFaces.length + i) * 3;
    indices[o] = rhFaces[i][0] + lhCount;
    indices[o + 1] = rhFaces[i][1] + lhCount;
    indices[o + 2] = rhFaces[i][2] + lhCount;
  }
  const triGeo = new BufferGeometry();
  triGeo.setAttribute("position", new BufferAttribute(normVerts, 3));
  triGeo.setIndex(new BufferAttribute(indices, 1));
  const wireGeo = new WireframeGeometry(triGeo);
  const wireMat = new LineBasicMaterial({
    color: themeIsDark ? 0x6cdcff : 0x0078a0,
    transparent: true,
    opacity: themeIsDark ? 0.32 : 0.42,
    depthWrite: false,
  });
  return new LineSegments(wireGeo, wireMat);
}

async function setupScene(canvas, atlasUrl, brainUrl, manifest, themeIsDark) {
  const [brain, atlasTex] = await Promise.all([
    loadJson(brainUrl),
    loadTexture(atlasUrl),
  ]);

  atlasTex.flipY = false;
  atlasTex.generateMipmaps = true;
  atlasTex.anisotropy = 4;

  const verts = normalizeAndCenter(combineHemispheres(brain));
  const totalVerts = verts.length / 3;
  const SPRITE_COUNT = Math.min(1600, totalVerts);

  const rng = mulberry32(20260511);
  const sampled = sampleIndices(totalVerts, SPRITE_COUNT, rng);

  const instPos = new Float32Array(SPRITE_COUNT * 3);
  const tileIdx = new Float32Array(SPRITE_COUNT);
  const jitter = new Float32Array(SPRITE_COUNT);
  for (let i = 0; i < SPRITE_COUNT; i++) {
    const v = sampled[i];
    instPos[i * 3] = verts[v * 3];
    instPos[i * 3 + 1] = verts[v * 3 + 1];
    instPos[i * 3 + 2] = verts[v * 3 + 2];
    tileIdx[i] = Math.floor(rng() * manifest.tile_count);
    jitter[i] = rng();
  }

  const baseGeo = new PlaneGeometry(1, 1);
  const geo = new InstancedBufferGeometry();
  geo.setAttribute("position", baseGeo.getAttribute("position"));
  geo.setAttribute("uv", baseGeo.getAttribute("uv"));
  geo.setIndex(baseGeo.getIndex());
  geo.setAttribute("aInstancePos", new InstancedBufferAttribute(instPos, 3));
  geo.setAttribute("aTileIndex", new InstancedBufferAttribute(tileIdx, 1));
  geo.setAttribute("aJitter", new InstancedBufferAttribute(jitter, 1));
  geo.instanceCount = SPRITE_COUNT;

  const tintCool = themeIsDark
    ? new Color(0.55, 0.75, 1.00)
    : new Color(0.70, 0.88, 1.05);
  const tintWarm = themeIsDark
    ? new Color(1.20, 1.00, 0.85)
    : new Color(1.10, 1.00, 0.90);

  const material = new ShaderMaterial({
    vertexShader: VERTEX_SHADER,
    fragmentShader: FRAGMENT_SHADER,
    uniforms: {
      uAtlas: { value: atlasTex },
      uGrid: { value: manifest.grid },
      uSpriteSize: { value: 0.024 },
      uNear: { value: 0.4 },
      uFar: { value: 2.6 },
      uTintCool: { value: tintCool },
      uTintWarm: { value: tintWarm },
      uOpacity: { value: 1.0 },
      uMouseWorld: { value: new Vector3(999, 999, 999) },
      uMouseRadius: { value: 0.22 },
      uMouseStrength: { value: 0.0 },
    },
    transparent: true,
    depthWrite: false,
    side: DoubleSide,
  });

  const sprites = new Mesh(geo, material);
  const wireframe = buildWireframeMesh(brain, verts, themeIsDark);

  const group = new Group();
  group.add(wireframe);
  group.add(sprites);

  return { group, material, atlasTex, wireframe };
}

function createRenderer(canvas, isDark) {
  const renderer = new WebGLRenderer({
    canvas,
    antialias: true,
    alpha: true,
    powerPreference: "high-performance",
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setClearColor(0x000000, 0);
  return renderer;
}

function detectThemeIsDark() {
  const t = document.body.dataset.theme;
  if (t === "dark") return true;
  if (t === "light") return false;
  return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function clampNumber(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function getStackedLayout() {
  const aspect = window.innerWidth / Math.max(1, window.innerHeight);
  return {
    aspect,
    isStacked: window.innerWidth <= 820 || aspect < 1,
    isTabletPortrait: window.innerWidth >= 600,
  };
}

export async function init(options = {}) {
  const root =
    options.root ||
    document.getElementById(options.rootId || "lf-hero-root");
  if (!root) {
    console.warn("[lf-hero] no root element found");
    return;
  }

  const cfg = {
    logoSrc: options.logoSrc || "_static/laion_fmri_logo_mosaic.png",
    title: options.title || "An open fMRI dataset for vision research",
    lede:
      options.lede ||
      "10,000+ natural-image stimuli viewed by humans in 7T MRI. " +
        "Preprocessed BOLD, GLMsingle betas, and ready-to-use splits.",
    primaryHref: options.primaryHref || "quickstart.html",
    primaryLabel: options.primaryLabel || "Quickstart",
    // Secondary button is opt-in: leave both unset to render only the primary CTA.
    secondaryHref: options.secondaryHref || null,
    secondaryLabel: options.secondaryLabel || null,
    secondaryExternal: options.secondaryExternal !== false,
    meta:
      options.meta || [
        "8 subjects",
        "10K+ stimuli",
        "7T BOLD",
        "Open access",
      ],
    atlasJson: options.atlasJson || "_static/hero/stimuli_atlas.json",
    atlasJpg: options.atlasJpg || "_static/hero/stimuli_atlas.jpg",
    brainJson: options.brainJson || "_static/hero/brain-data.json",
  };

  // Lift root out of the Sphinx article column up to body.firstChild so the
  // hero can occupy the full viewport without fighting Furo's max-width.
  if (root.parentNode !== document.body || document.body.firstElementChild !== root) {
    document.body.insertBefore(root, document.body.firstElementChild);
  }

  const { canvas, canvasWrap, text, logo, scrollBtn } = buildHeroDom({ root, ...cfg });

  scrollBtn.addEventListener("click", () => {
    window.scrollTo({
      top: root.getBoundingClientRect().bottom + window.scrollY - 8,
      behavior: "smooth",
    });
  });

  let manifest;
  try {
    manifest = await loadJson(cfg.atlasJson);
  } catch (e) {
    console.warn("[lf-hero] atlas manifest missing, hero disabled:", e);
    return;
  }

  const isDark = detectThemeIsDark();
  const renderer = createRenderer(canvas, isDark);

  const scene = new Scene();
  const camera = new PerspectiveCamera(45, 1, 0.1, 100);
  camera.position.set(0, 0.05, 2.4);
  camera.lookAt(0, 0, 0);

  let setup;
  try {
    setup = await setupScene(
      canvas,
      cfg.atlasJpg,
      cfg.brainJson,
      manifest,
      isDark,
    );
  } catch (e) {
    console.warn("[lf-hero] setup failed:", e);
    return;
  }
  scene.add(setup.group);

  // The brain coords come in with the back of the head along +z. Rotate so
  // the lateral profile faces the camera initially — more recognizable.
  setup.group.rotation.y = -Math.PI * 0.35;

  const reduceMotion =
    window.matchMedia &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  let width = 1;
  let height = 1;
  const mobileBand = {
    isStacked: false,
    isTabletPortrait: false,
    aspect: 1,
    brainHeight: 1,
  };

  function layoutMobileBrainBand() {
    const layout = getStackedLayout();
    mobileBand.isStacked = layout.isStacked;
    mobileBand.isTabletPortrait = layout.isTabletPortrait;
    mobileBand.aspect = layout.aspect;

    if (!layout.isStacked) {
      root.style.removeProperty("--lf-hero-brain-top");
      root.style.removeProperty("--lf-hero-brain-height");
      return mobileBand;
    }

    const heroRect = root.getBoundingClientRect();
    const logoRect = logo.getBoundingClientRect();
    const textRect = text.getBoundingClientRect();
    const vh = Math.max(1, window.innerHeight);
    const logoTop = logoRect.top - heroRect.top;
    const textTop = textRect.top - heroRect.top;
    const anchorY = Number.isFinite(logoTop) && logoTop > 0 ? logoTop : textTop;
    const gap = clampNumber(vh * 0.055, 42, layout.isTabletPortrait ? 72 : 56);
    const bottom = Math.max(0, anchorY - gap);
    const topLimit = clampNumber(vh * 0.075, 42, layout.isTabletPortrait ? 96 : 66);
    const targetHeight = clampNumber(
      vh * (layout.isTabletPortrait ? 0.39 : 0.36),
      layout.isTabletPortrait ? 260 : 210,
      layout.isTabletPortrait ? 460 : 330,
    );
    const available = Math.max(0, bottom - topLimit);
    const minVisible = layout.isTabletPortrait ? 190 : 140;

    let brainHeight = Math.min(targetHeight, available);
    if (available >= minVisible) {
      brainHeight = Math.max(brainHeight, minVisible);
    }
    brainHeight = Math.max(1, brainHeight);
    const top = Math.max(topLimit, bottom - brainHeight);

    root.style.setProperty("--lf-hero-brain-top", `${Math.round(top)}px`);
    root.style.setProperty("--lf-hero-brain-height", `${Math.round(brainHeight)}px`);
    mobileBand.brainHeight = brainHeight;
    return mobileBand;
  }

  function resize() {
    const layout = layoutMobileBrainBand();
    const rect = canvasWrap.getBoundingClientRect();
    width = Math.max(1, Math.floor(rect.width));
    height = Math.max(1, Math.floor(rect.height));
    renderer.setSize(width, height, false);
    camera.aspect = width / height;

    // Stack triggers in CSS (max-width 820px OR portrait orientation) —
    // mirror that here so the brain sits centered above the text on
    // phones AND iPad portrait. In landscape, shift the brain to the
    // right; the shift scales with aspect so iPad landscape (1.33)
    // doesn't push the brain off-screen the way wide desktop (1.78+)
    // can absorb.
    const aspect = layout.aspect;
    if (layout.isStacked) {
      const scaleFactor = clampNumber(
        layout.brainHeight / (layout.isTabletPortrait ? 360 : 260),
        0.84,
        1.12,
      );
      setup.group.position.x = 0;
      setup.group.position.y = layout.isTabletPortrait ? 0.02 : 0.01;
      if (layout.isTabletPortrait) {
        setup.group.scale.setScalar(0.98 * scaleFactor);
        camera.position.z = 2.24;
      } else {
        setup.group.scale.setScalar(0.70 * scaleFactor);
        camera.position.z = aspect < 0.68 ? 2.54 : 2.42;
      }
    } else {
      const shiftX = Math.max(0.35, Math.min(0.70, 0.40 + (aspect - 1.33) * 0.55));
      setup.group.position.x = shiftX;
      setup.group.position.y = 0;
      // Narrower landscape (iPad-ish) gets a bigger brain too.
      setup.group.scale.setScalar(aspect < 1.5 ? 0.75 : 0.62);
      camera.position.z = 2.4;
    }
    camera.updateProjectionMatrix();
  }
  resize();
  const ro = new ResizeObserver(resize);
  ro.observe(canvasWrap);
  window.addEventListener("resize", resize);

  // ── Hover bulge: ray-cast the pointer onto the brain's focal plane and
  // expose the world-space hit point as a uniform. Vertex shader scales up
  // sprites within radius. Strength fades in/out so it never feels twitchy.
  const raycaster = new Raycaster();
  const ndc = new Vector2();
  const focalPlane = new Plane(new Vector3(0, 0, 1), 0);
  const tmpHit = new Vector3();
  const mouseWorld = new Vector3(999, 999, 999);
  const targetMouseWorld = new Vector3(999, 999, 999);
  let mouseStrength = 0;
  let targetMouseStrength = 0;
  let tiltX = 0;
  let tiltZ = 0;
  let targetTiltX = 0;
  let targetTiltZ = 0;

  function resetTilt() {
    targetTiltX = 0;
    targetTiltZ = 0;
  }

  function tiltEnabled() {
    return !reduceMotion && getStackedLayout().isStacked;
  }

  function updatePointerTilt(e) {
    if (!tiltEnabled()) {
      resetTilt();
      return;
    }
    const rect = root.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / Math.max(1, rect.width) - 0.5) * 2;
    const y = ((e.clientY - rect.top) / Math.max(1, rect.height) - 0.5) * 2;
    targetTiltZ = clampNumber(x * 0.06, -0.06, 0.06);
    targetTiltX = clampNumber(y * 0.05, -0.05, 0.05);
  }

  function onDeviceOrientation(e) {
    if (!tiltEnabled() || e.beta == null || e.gamma == null) return;
    targetTiltZ = clampNumber(e.gamma / 55, -1, 1) * 0.08;
    targetTiltX = clampNumber((e.beta - 45) / 60, -1, 1) * 0.06;
  }

  function onPointerMove(e) {
    updatePointerTilt(e);
    const rect = canvas.getBoundingClientRect();
    ndc.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    ndc.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
    raycaster.setFromCamera(ndc, camera);
    if (raycaster.ray.intersectPlane(focalPlane, tmpHit)) {
      targetMouseWorld.copy(tmpHit);
      targetMouseStrength = 1.0;
    }
  }
  function onPointerLeave() {
    targetMouseStrength = 0.0;
    resetTilt();
  }
  root.addEventListener("pointermove", onPointerMove);
  root.addEventListener("pointerleave", onPointerLeave);
  root.addEventListener("pointerdown", () => {
    if (
      typeof DeviceOrientationEvent !== "undefined" &&
      typeof DeviceOrientationEvent.requestPermission === "function"
    ) {
      DeviceOrientationEvent.requestPermission().catch(() => {});
    }
  }, { once: true, passive: true });
  window.addEventListener("deviceorientation", onDeviceOrientation, { passive: true });

  // Theme switch: re-derive tints when Furo's data-theme attribute changes
  const themeObserver = new MutationObserver(() => {
    const dark = detectThemeIsDark();
    if (dark) {
      setup.material.uniforms.uTintCool.value.setRGB(0.55, 0.75, 1.00);
      setup.material.uniforms.uTintWarm.value.setRGB(1.20, 1.00, 0.85);
      setup.wireframe.material.color.setHex(0x6cdcff);
      setup.wireframe.material.opacity = 0.32;
    } else {
      setup.material.uniforms.uTintCool.value.setRGB(0.70, 0.88, 1.05);
      setup.material.uniforms.uTintWarm.value.setRGB(1.10, 1.00, 0.90);
      setup.wireframe.material.color.setHex(0x0078a0);
      setup.wireframe.material.opacity = 0.42;
    }
  });
  themeObserver.observe(document.body, {
    attributes: true,
    attributeFilter: ["data-theme"],
  });

  root.classList.add("is-ready");

  let visible = true;
  const io = new IntersectionObserver((entries) => {
    visible = entries[0].isIntersecting;
  }, { threshold: 0.05 });
  io.observe(root);

  let lastT = performance.now();
  const ROT_SPEED = reduceMotion ? 0.0 : 0.06; // rad/sec

  function frame(now) {
    const dt = Math.min(0.05, (now - lastT) / 1000);
    lastT = now;
    if (visible) {
      if (!getStackedLayout().isStacked) resetTilt();
      setup.group.rotation.y += ROT_SPEED * dt;
      tiltX += (targetTiltX - tiltX) * Math.min(1, dt * 7);
      tiltZ += (targetTiltZ - tiltZ) * Math.min(1, dt * 7);
      setup.group.rotation.x = tiltX;
      setup.group.rotation.z = tiltZ;
      mouseStrength += (targetMouseStrength - mouseStrength) * Math.min(1, dt * 18);
      mouseWorld.lerp(targetMouseWorld, Math.min(1, dt * 28));
      setup.material.uniforms.uMouseWorld.value.copy(mouseWorld);
      setup.material.uniforms.uMouseStrength.value = mouseStrength;
      renderer.render(scene, camera);
    }
    requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}
