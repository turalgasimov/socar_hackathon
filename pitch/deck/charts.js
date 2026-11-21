// GL-04 oil rate: measured well tests (dots) and, on the solution slide, our daily estimate (line).
// Real data: ml/outputs/vfm_submission.csv and data/well_tests.csv, extracted to data/gl04.json.
const NS = 'http://www.w3.org/2000/svg';
const mk = (tag, attrs, parent, text) => {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) e.setAttribute(k, attrs[k]);
  if (text !== undefined) e.textContent = text;
  parent.appendChild(e); return e;
};
// The single-file build inlines the data as window.GL04; served from the folder, it is fetched.
const d = window.GL04 ?? await (await fetch('data/gl04.json')).json();
const ms = s => Date.parse(s + 'T00:00:00Z');
const x0 = ms('2025-01-01'), x1 = ms('2025-09-30');
const vals = [...d.days.map(r => r[1]).filter(q => q >= 50), ...d.tests.map(r => r[1])];
const lo = Math.floor((Math.min(...vals) - 50) / 100) * 100, hi = Math.ceil((Math.max(...vals) + 30) / 100) * 100;
const fmt = s => new Date(ms(s)).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' });

for (const svg of document.querySelectorAll('svg.trace')) {
  const [, , W, H] = svg.getAttribute('viewBox').split(' ').map(Number);
  const both = svg.dataset.mode === 'both';
  const M = { l: 62, r: both ? 150 : 210, t: 44, b: 34 };
  const X = s => M.l + (ms(s) - x0) / (x1 - x0) * (W - M.l - M.r);
  const Y = q => M.t + (hi - q) / (hi - lo) * (H - M.t - M.b);
  mk('rect', { width: W, height: H, fill: '#15202b', opacity: 0.86 }, svg);
  for (let q = lo + 200; q < hi; q += 200) {
    mk('line', { x1: M.l, x2: W - M.r, y1: Y(q), y2: Y(q), stroke: 'rgba(236,231,220,0.10)' }, svg);
    mk('text', { x: M.l - 12, y: Y(q) + 6, 'text-anchor': 'end', class: 'axis' }, svg, q);
  }
  ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep'].forEach((m, i) =>
    mk('text', { x: X(`2025-0${i + 1}-01`), y: H - 8, class: 'axis' }, svg, m));
  if (both) {   // two series: legend + direct labels
    mk('circle', { cx: M.l + 8, cy: 16, r: 6, fill: '#ece7dc' }, svg);
    mk('text', { x: M.l + 22, y: 22, class: 'key' }, svg, 'Measured well tests');
    mk('line', { x1: M.l + 224, x2: M.l + 252, y1: 16, y2: 16, stroke: '#3987e5', 'stroke-width': 3 }, svg);
    mk('text', { x: M.l + 262, y: 22, class: 'key' }, svg, 'Our daily estimate, barrels a day');
    const s0 = d.shutin[0];
    mk('line', { x1: X(s0), x2: X(s0), y1: M.t, y2: H - M.b, stroke: '#737a7c', 'stroke-dasharray': '4 5' }, svg);
    mk('text', { x: X(s0) + 8, y: M.t + 16, class: 'axis' }, svg, 'shut-in');
    let path = '', len = 0, prev = null, last = null;
    for (const [day, q] of d.days) {
      if (q < 50) { prev = null; continue; }
      const p = [X(day), Y(q)];
      path += (prev ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1);
      if (prev) len += Math.hypot(p[0] - prev[0], p[1] - prev[1]);
      prev = last = p;
    }
    mk('path', { d: path, class: 'estimate', style: `stroke-dasharray:${len};stroke-dashoffset:${len}` }, svg);
    mk('text', { x: last[0] + 14, y: last[1] + 26, class: 'end' }, svg, 'Daily estimate');
  } else {
    mk('text', { x: M.l, y: 22, class: 'key' }, svg, 'GL-04 oil rate in 2025, barrels a day');
  }
  d.tests.forEach(([day, q], i) => {
    const c = mk('circle', { cx: X(day), cy: Y(q), r: 7.5, fill: '#ece7dc', stroke: '#15202b', 'stroke-width': 3 }, svg);
    mk('title', {}, c, `Well test, ${fmt(day)}: ${Math.round(q)} barrels a day`);
    const next = d.tests[i + 1];
    if (!both && next) mk('text', { x: (X(day) + X(next[0])) / 2, y: (Y(q) + Y(next[1])) / 2 + 8,
      'text-anchor': 'middle', class: 'gap' }, svg, '?');
  });
  const [lday, lq] = d.tests[d.tests.length - 1];
  mk('text', { x: X(lday) + 16, y: Y(lq) + (both ? -12 : 7), class: 'end' }, svg, both ? 'Tests' : '9 measured tests');
}

// One month of GL-04 as a calendar: the single measured day lit, every other day unknown.
for (const svg of document.querySelectorAll('svg.month')) {
  const [year, month] = svg.dataset.month.split('-').map(Number);
  const tested = new Set(d.tests.map(r => r[0]));
  const first = new Date(Date.UTC(year, month - 1, 1)), days = new Date(Date.UTC(year, month, 0)).getUTCDate();
  const lead = (first.getUTCDay() + 6) % 7, CW = 64, CH = 54, G = 8, top = 76;
  const name = first.toLocaleDateString('en-GB', { month: 'long', year: 'numeric', timeZone: 'UTC' });
  mk('text', { x: 0, y: 24, class: 'key' }, svg, `GL-04, ${name}`);
  ['M', 'T', 'W', 'T', 'F', 'S', 'S'].forEach((w, i) => mk('text', { x: i * (CW + G) + CW / 2, y: 58, 'text-anchor': 'middle', class: 'axis' }, svg, w));
  let measured = 0;
  for (let n = 1; n <= days; n++) {
    const k = lead + n - 1, x = (k % 7) * (CW + G), y = top + Math.floor(k / 7) * (CH + G);
    const iso = `${year}-${String(month).padStart(2, '0')}-${String(n).padStart(2, '0')}`, hit = tested.has(iso);
    measured += hit;
    const g = mk('g', { class: 'day' + (hit ? ' hit' : ''), style: `--i:${n}` }, svg);
    mk('rect', { x, y, width: CW, height: CH, rx: 6 }, g);
    mk('text', { x: x + 8, y: y + 20, class: 'n' }, g, n);
    mk('text', { x: x + CW / 2, y: y + 42, 'text-anchor': 'middle', class: 'q' }, g, hit ? 'test' : '?');
  }
  const rows = Math.ceil((lead + days) / 7), yb = top + rows * (CH + G) + 30;
  mk('text', { x: 0, y: yb, class: 'end' }, svg, `${measured} measured day, ${days - measured} unknown`);
}
