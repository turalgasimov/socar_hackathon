// 2D drawings for the deck (SVG, no WebGL): the field map and the gas-lifted well, flowing or shut in.
// Motion is CSS (deck.css), and only on the slide being shown; the static drawing is the final state,
// so print and PDF show it complete.
(() => {
  const NS = 'http://www.w3.org/2000/svg';
  const mk = (tag, attrs, parent, text) => {
    const e = document.createElementNS(NS, tag);
    for (const k in attrs) e.setAttribute(k, attrs[k]);
    if (text !== undefined) e.textContent = text;
    parent.appendChild(e); return e;
  };
  const C = { ink: '#ece7dc', ink2: '#a9aca3', ink3: '#737a7c', oil: '#3987e5', water: '#d95926', gas: '#199e70',
              sand: '#e2c27f', steel: '#8f99a3', hole: '#0d141b' };

  // ---- field map: the ten wells from above, GL-04 marked -----------------------------------------
  const WELLS = { 'GL-01': [-15, -7], 'GL-02': [-6, -9], 'GL-03': [3, -6], 'GL-04': [8, 12.3], 'GL-05': [-17, 3],
                  'GL-06': [-8, 2], 'GL-07': [-1, 7], 'GL-08': [15, -2], 'GL-09': [17, 6], 'GL-10': [-12, 9.5] };
  for (const svg of document.querySelectorAll('svg.field-map')) {
    mk('rect', { x: 8, y: 8, width: 464, height: 330, rx: 18, class: 'outline' }, svg);
    Object.entries(WELLS).forEach(([name, [x, z]], i) => {
      const px = 50 + (x + 17) / 34 * 380, py = 52 + (z + 9) / 21.3 * 250, key = name === 'GL-04';
      const g = mk('g', { class: 'w' + (key ? ' key' : ''), style: `--i:${i}` }, svg);
      if (key) mk('circle', { cx: px, cy: py, r: 10, class: 'ping' }, g);
      mk('circle', { cx: px, cy: py, r: key ? 9 : 6.5, fill: key ? C.oil : C.ink3 }, g);
      mk('text', { x: px + 15, y: py + 6, class: key ? 'lbl key' : 'lbl' }, g, name);
    });
    mk('text', { x: 8, y: 370, class: 'cap' }, svg, '10 gas-lifted wells, 1 Jan to 30 Sep 2025');
  }

  // ---- the well: casing, tubing, gas-lift valves, gauge, perforations, choke --------------------
  const STRATA = [[150, 250, '#2b3843'], [250, 320, '#344250'], [320, 430, '#29353f'], [430, 490, '#3b4754'],
                  [490, 560, '#4a535c'], [560, 660, '#9b7544'], [660, 760, '#284658']];
  const X = 180, RES = [560, 660];
  for (const svg of document.querySelectorAll('svg.well')) {
    const shut = svg.dataset.state === 'shut';
    for (const [y0, y1, col] of STRATA) {
      mk('rect', { x: 0, y: y0, width: 560, height: y1 - y0, fill: col }, svg);
      for (let k = 1; k < 3; k++) {
        const y = y0 + (y1 - y0) * k / 3;
        mk('path', { d: `M0 ${y} C140 ${y - 5} 280 ${y + 6} 560 ${y - 2}`, class: 'bed' }, svg);
      }
    }
    mk('line', { x1: 0, x2: 560, y1: 150, y2: 150, stroke: C.ink3, 'stroke-width': 2 }, svg);       // surface
    mk('rect', { x: X - 14, y: 150, width: 28, height: 540, fill: C.hole }, svg);                      // borehole
    for (const dx of [-10, 10]) mk('line', { x1: X + dx, x2: X + dx, y1: 150, y2: 680, stroke: C.steel, 'stroke-width': 3 }, svg);
    for (let y = RES[0] + 14; y < RES[1] - 8; y += 11)                                                 // perforations
      mk('line', { x1: X - 32, x2: X + 32, y1: y, y2: y, stroke: C.sand, 'stroke-width': 2 }, svg);
    mk('rect', { x: X - 4, y: 110, width: 8, height: 495, fill: '#d7dde2', opacity: 0.25 }, svg);      // tubing
    // wellhead and flowline
    mk('rect', { x: X - 12, y: 86, width: 24, height: 64, fill: C.steel }, svg);
    mk('rect', { x: X - 18, y: 78, width: 36, height: 10, fill: C.steel }, svg);
    mk('line', { x1: X + 12, x2: 556, y1: 110, y2: 110, stroke: C.steel, 'stroke-width': 7 }, svg);
    mk('line', { x1: 40, x2: X - 12, y1: 132, y2: 132, stroke: C.gas, 'stroke-width': 5, opacity: 0.8 }, svg);   // lift gas in
    mk('polygon', { points: `${X + 34},98 ${X + 34},122 ${X + 54},110`, fill: C.ink }, svg);           // choke
    mk('polygon', { points: `${X + 74},98 ${X + 74},122 ${X + 54},110`, fill: C.ink }, svg);
    if (shut) mk('rect', { x: X + 50, y: 90, width: 8, height: 40, rx: 2, fill: C.water }, svg);       // closed
    // produced fluid up the tubing and out of the flowline; lift gas down the annulus; inflow from the rock
    const up = `M${X} 600 V110 H556`;
    [['oil', 0], ['water', 6], ['gas', 12]].forEach(([ph, off]) =>
      mk('path', { d: up, class: `flow ${ph}`, style: `stroke-dashoffset:${off}` }, svg));
    mk('path', { d: `M40 132 H${X - 14} V470`, class: 'flow gas lift' }, svg);
    for (const [x0, x1] of [[40, X - 34], [540, X + 34]])
      mk('path', { d: `M${x0} 644 H${x1}`, class: 'flow oil inflow' }, svg);
    for (const y of [300, 390, 470]) mk('rect', { x: X + 4, y: y - 7, width: 9, height: 14, rx: 2, fill: C.gas }, svg);   // valves
    mk('rect', { x: X + 4, y: 516, width: 10, height: 16, rx: 2, fill: C.ink }, svg);                  // gauge
    if (shut) {
      for (let k = 0; k < 3; k++) mk('circle', { cx: X, cy: 610, r: 38, class: 'ring', style: `--k:${k}` }, svg);
      // build-up inset: downhole pressure climbing after the choke closes
      const g = mk('g', { class: 'inset', transform: 'translate(300 214)' }, svg);
      mk('rect', { width: 240, height: 150, rx: 10, class: 'panel' }, g);
      mk('text', { x: 16, y: 28, class: 'lbl' }, g, 'Downhole pressure');
      mk('line', { x1: 16, x2: 224, y1: 128, y2: 128, stroke: C.ink3 }, g);
      mk('path', { d: 'M16 124 H70 C76 60 96 52 130 48 S200 44 224 43', class: 'buildup' }, g);
      mk('text', { x: 70, y: 146, class: 'tick' }, g, 'shut-in');
    }
    // labels with a dark halo so they read on any layer
    const label = (x, y, text, key) => {
      mk('circle', { cx: x - 12, cy: y - 6, r: 4, fill: key ? C.oil : C.ink }, svg);
      mk('text', { x, y, class: key ? 'lbl key' : 'lbl' }, svg, text);
    };
    if (!shut) {
      label(X + 92, 96, 'Choke and wellhead pressure');
      label(X + 36, 396, 'Gas-lift valves');
    } else label(X + 92, 96, 'Choke closed');
    label(X + 36, 530, 'Downhole pressure gauge');
    label(X + 56, 616, 'Reservoir', true);
  }
})();
