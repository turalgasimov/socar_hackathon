// The field as a geologist would sketch it: a block diagram, ten wellheads on top,
// GL-04 drilled down the front face. The camera moves when the slide changes.
import * as THREE from 'three';

const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const C = { basin: 0x15202b, ink: 0xece7dc, ink3: 0x737a7c, oil: 0x3987e5, water: 0xd95926, gas: 0x199e70, sand: 0xe2c27f };

const canvas = document.getElementById('scene');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.setClearColor(C.basin);
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(C.basin, 75, 160);
const camera = new THREE.PerspectiveCamera(30, 1, 0.1, 500);
scene.add(new THREE.HemisphereLight(0xe8eef5, 0x10171e, 1.7));
const sun = new THREE.DirectionalLight(0xffffff, 1.5); sun.position.set(30, 50, 40); scene.add(sun);

// ---- block diagram -------------------------------------------------------
const W = 44, D = 26, H = 16;
const STRATA = [[3.2, '#2b3843'], [1.4, '#344250'], [2.6, '#29353f'], [1.2, '#3b4754'],
                [1.6, '#4a535c'],    // cap shale
                [2.4, '#9b7544'],    // reservoir sandstone
                [3.6, '#284658']];   // water-bearing sand
const RES_TOP = -10, RES_BOT = -12.4;

function strataTexture() {
  const c = Object.assign(document.createElement('canvas'), { width: 1024, height: 512 });
  const g = c.getContext('2d'); let y = 0;
  for (const [t, col] of STRATA) {
    const h = t / H * c.height;
    g.fillStyle = col; g.fillRect(0, y, c.width, h + 1);
    g.strokeStyle = 'rgba(255,255,255,0.05)'; g.lineWidth = 1;
    for (let k = 1; k < 4; k++) { const yy = y + h * k / 4; g.beginPath(); g.moveTo(0, yy); g.lineTo(c.width, yy + 4 * Math.sin(k * 1.7)); g.stroke(); }
    g.fillStyle = 'rgba(0,0,0,0.28)'; g.fillRect(0, y, c.width, 2);
    y += h;
  }
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace; tex.anisotropy = 4; return tex;
}
function gridTexture() {
  const c = Object.assign(document.createElement('canvas'), { width: 1024, height: 1024 });
  const g = c.getContext('2d'); g.fillStyle = '#1e2b36'; g.fillRect(0, 0, 1024, 1024);
  g.strokeStyle = 'rgba(236,231,220,0.07)'; g.lineWidth = 2;
  for (let i = 0; i <= 1024; i += 64) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i, 1024); g.moveTo(0, i); g.lineTo(1024, i); g.stroke(); }
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace; return tex;
}
const hidden = new THREE.MeshLambertMaterial({ color: 0x111a22 });
const block = new THREE.Mesh(new THREE.BoxGeometry(W, H, D), [
  new THREE.MeshLambertMaterial({ map: strataTexture() }), hidden,
  new THREE.MeshLambertMaterial({ map: gridTexture() }), hidden,
  new THREE.MeshLambertMaterial({ map: strataTexture() }), hidden]);
block.position.y = -H / 2; scene.add(block);

// ---- wellheads -------------------------------------------------------------
const WELLS = { 'GL-01': [-15, -7], 'GL-02': [-6, -9], 'GL-03': [3, -6], 'GL-04': [8, 12.3], 'GL-05': [-17, 3],
                'GL-06': [-8, 2], 'GL-07': [-1, 7], 'GL-08': [15, -2], 'GL-09': [17, 6], 'GL-10': [-12, 9.5] };
const headGeo = new THREE.CylinderGeometry(0.22, 0.28, 1, 12), ringGeo = new THREE.RingGeometry(0.62, 0.8, 48);
for (const [name, [x, z]] of Object.entries(WELLS)) {
  const head = new THREE.Mesh(headGeo, new THREE.MeshLambertMaterial({ color: 0x9aa3ab }));
  head.position.set(x, 0.5, z); scene.add(head);
  const ring = new THREE.Mesh(ringGeo, new THREE.MeshBasicMaterial({ color: name === 'GL-04' ? C.oil : C.ink3, side: THREE.DoubleSide }));
  ring.rotation.x = -Math.PI / 2; ring.position.set(x, 0.03, z); scene.add(ring);
}

// ---- GL-04 drawn on the front face --------------------------------------
const WX = 8, FZ = D / 2 + 0.04;
const flat = (w, h, color, x, y, dz = 0, opacity = 1) => {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ color, transparent: opacity < 1, opacity }));
  m.position.set(x, y, FZ + dz); scene.add(m); return m;
};
flat(0.95, -RES_BOT + 0.3, 0x0d141b, WX, (RES_BOT - 0.3) / 2, 0, 0.9);       // borehole
flat(0.62, -RES_TOP + 0.2, 0x8f99a3, WX, (RES_TOP - 0.2) / 2, 0.01);         // casing
flat(0.2, 0.6 - RES_TOP, 0xd7dde2, WX, (RES_TOP - 0.6) / 2, 0.02);          // tubing to just above the perforations
for (const y of [-3, -5.6, -7.9]) flat(0.46, 0.3, C.gas, WX, y, 0.03);       // gas-lift valves
flat(0.5, 0.36, C.ink, WX, -9.3, 0.03);                                       // downhole gauge
const datum = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(WX - 6, -10.7, FZ + 0.03), new THREE.Vector3(WX + 7, -10.7, FZ + 0.03)]),
  new THREE.LineDashedMaterial({ color: C.ink, dashSize: 0.35, gapSize: 0.25, transparent: true, opacity: 0.6 }));
datum.computeLineDistances(); scene.add(datum);
const perf = [];
for (let y = RES_TOP - 0.25; y > RES_BOT + 0.2; y -= 0.32) perf.push(new THREE.Vector3(WX - 0.9, y, FZ + 0.03), new THREE.Vector3(WX + 0.9, y, FZ + 0.03));
scene.add(new THREE.LineSegments(new THREE.BufferGeometry().setFromPoints(perf), new THREE.LineBasicMaterial({ color: C.sand })));
const choke = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.42, 0.42), new THREE.MeshLambertMaterial({ color: C.ink }));
choke.position.set(WX + 0.75, 0.55, 12.3); scene.add(choke);
const flowline = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 9, 8), new THREE.MeshLambertMaterial({ color: 0x8f99a3 }));
flowline.rotation.z = Math.PI / 2; flowline.position.set(WX + 5.5, 0.55, 12.3); scene.add(flowline);

// ---- produced fluid: oil, water and gas moving up the tubing -------------
const N = 70, tpos = new Float32Array(N), m4 = new THREE.Matrix4(), v = new THREE.Vector3();
const pMat = new THREE.MeshBasicMaterial({ transparent: true });
const parts = new THREE.InstancedMesh(new THREE.SphereGeometry(0.1, 8, 6), pMat, N);
for (let i = 0; i < N; i++) {
  tpos[i] = i / N; const r = (i * 37) % 100;          // 60% oil, 25% water, 15% gas
  parts.setColorAt(i, new THREE.Color(r < 60 ? C.oil : r < 85 ? C.water : C.gas));
}
scene.add(parts);
const along = (t, out) => t < 0.8
  ? out.set(WX, RES_TOP - 0.6 + (t / 0.8) * (0.6 - RES_TOP), FZ + 0.06)
  : out.set(WX + 1 + (t - 0.8) / 0.2 * 9, 0.55, 12.3);
// pressure building up after a shut-in
const pulses = [0, 1, 2].map(() => {
  const m = new THREE.Mesh(new THREE.RingGeometry(0.95, 1, 64), new THREE.MeshBasicMaterial({ color: C.sand, transparent: true, opacity: 0 }));
  m.position.set(WX, (RES_TOP + RES_BOT) / 2, FZ + 0.05); scene.add(m); return m;
});

// ---- labels (HTML, projected from 3D) -------------------------------------
const LBL = {
  gl04: [[WX, 1.7, 12.3], 'GL-04', true], choke: [[WX + 1.2, 1.6, 12.3], 'Choke and wellhead pressure'],
  valves: [[WX + 0.5, -5.6, FZ], 'Gas-lift valves'], gauge: [[WX + 0.5, -9.3, FZ], 'Downhole pressure gauge'],
  reservoir: [[WX + 1.3, (RES_TOP + RES_BOT) / 2, FZ], 'Reservoir', true],
};
for (const [n, [x, z]] of Object.entries(WELLS)) LBL['wells:' + n] = [[x, 1.6, z], n, n === 'GL-04'];
const layer = document.getElementById('labels');
const labels = Object.entries(LBL).map(([key, [at, text, isKey]]) => {
  const el = Object.assign(document.createElement('div'), { className: 'lbl' + (isKey ? ' key' : ''), textContent: text });
  layer.appendChild(el); return { key, group: key.split(':')[0], at: new THREE.Vector3(...at), el };
});

// ---- camera presets and slide wiring --------------------------------------
// Looks are centred on the subject; the view offset in resize() pushes it right of the text column.
const CAMS = { field: [[34, 27, 42], [0, -5, 0]], well: [[26, 8, 38], [8, -3, 12]],
               cutaway: [[8, -4.6, 54], [7, -5.6, 13]], wide: [[46, 36, 56], [-2, -6, 0]] };
const cur = { pos: new THREE.Vector3(...CAMS.field[0]), look: new THREE.Vector3(...CAMS.field[1]) };
let tween = null, shut = false, flowAmt = 1;
const ease = t => t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2;
function go(name) {
  const p = CAMS[name]; if (!p) return;
  const to = { pos: new THREE.Vector3(...p[0]), look: new THREE.Vector3(...p[1]) };
  if (reduce) { cur.pos.copy(to.pos); cur.look.copy(to.look); tween = null; return; }
  tween = { from: { pos: cur.pos.clone(), look: cur.look.clone() }, to, t: 0 };
}
function apply(slide) {
  if (!slide) return;
  const d = slide.dataset;
  document.body.classList.toggle('dim', d.scene === 'dim');
  document.body.classList.toggle('hide-scene', d.scene === 'hide');
  document.body.classList.toggle('soft', d.scene === 'soft');
  if (d.cam) go(d.cam);
  shut = d.state === 'shut';
  const want = new Set((d.labels || '').split(/\s+/).filter(Boolean));
  for (const l of labels) l.el.classList.toggle('on', want.has(l.key) || want.has(l.group));
}
const R = window.Reveal;
if (R.isReady()) apply(R.getCurrentSlide()); else R.on('ready', e => apply(e.currentSlide));
R.on('slidechanged', e => apply(e.currentSlide));

const SHIFT = 1.4;   // render the left 1/1.4 of a wider frame: the subject lands at ~70% of the width
function resize() {
  renderer.setSize(innerWidth, innerHeight, false);
  camera.aspect = innerWidth * SHIFT / innerHeight;
  camera.setViewOffset(innerWidth * SHIFT, innerHeight, 0, 0, innerWidth, innerHeight);
}
addEventListener('resize', resize); resize();

const clock = new THREE.Clock();
renderer.setAnimationLoop(() => {
  const dt = Math.min(clock.getDelta(), 0.1), time = clock.elapsedTime;   // dt capped: no slow motion above 10 fps
  if (tween) {
    tween.t = Math.min(1, tween.t + dt / 1.8); const k = ease(tween.t);
    cur.pos.lerpVectors(tween.from.pos, tween.to.pos, k); cur.look.lerpVectors(tween.from.look, tween.to.look, k);
    if (tween.t >= 1) tween = null;
  }
  camera.position.copy(cur.pos); camera.lookAt(cur.look);
  flowAmt += ((shut ? 0 : 1) - flowAmt) * Math.min(1, dt * 2.5);
  for (let i = 0; i < N; i++) {
    if (!reduce) tpos[i] = (tpos[i] + dt * 0.07 * flowAmt) % 1;
    along(tpos[i], v); parts.setMatrixAt(i, m4.makeTranslation(v.x, v.y, v.z));
  }
  parts.instanceMatrix.needsUpdate = true;
  pMat.opacity = 0.2 + 0.8 * flowAmt;
  pulses.forEach((p, k) => {
    const ph = reduce ? 0.35 : (time * 0.35 + k / 3) % 1, s = 1 + ph * 7;
    p.scale.set(s, Math.min(s, 1.15), 1); p.material.opacity = (1 - flowAmt) * (1 - ph) * 0.85;
  });
  for (const l of labels) {
    v.copy(l.at).project(camera);
    l.el.style.left = ((v.x + 1) / 2 * innerWidth) + 'px';
    l.el.style.top = ((1 - v.y) / 2 * innerHeight) + 'px';
  }
  renderer.render(scene, camera);
});
