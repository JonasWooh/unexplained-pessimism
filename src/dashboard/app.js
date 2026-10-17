/* Perception Gap Monitor. Renders window.PGM_DATA (built by src/dashboard/build.py) with D3 v7.
   The page derives only presentation quantities from the payload: 3-month trailing means, z-scores,
   means and counts over the period on screen. Every estimate comes from the frozen result files. */
(function () {
  'use strict';
  const D = window.PGM_DATA;
  const M = D.months;
  const N = M.length;
  const parseM = d3.timeParse('%Y-%m');
  const parseD = d3.timeParse('%Y-%m-%d');
  const T = M.map(parseM);
  const TMS = T.map(d => +d);
  const idx = m => M.indexOf(m);
  const REDUCE = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const MINUS = '−';

  // ------------------------------------------------------------------ easing (motion tokens)
  function bezier(p1x, p1y, p2x, p2y) {
    const cx = 3 * p1x, bx = 3 * (p2x - p1x) - cx, ax = 1 - cx - bx;
    const cy = 3 * p1y, by = 3 * (p2y - p1y) - cy, ay = 1 - cy - by;
    const sx = t => ((ax * t + bx) * t + cx) * t, sy = t => ((ay * t + by) * t + cy) * t;
    const dsx = t => (3 * ax * t + 2 * bx) * t + cx;
    return x => {
      if (x <= 0) return 0;
      if (x >= 1) return 1;
      let t = x;
      for (let k = 0; k < 8; k++) {
        const e = sx(t) - x;
        if (Math.abs(e) < 1e-5) break;
        const d = dsx(t);
        if (Math.abs(d) < 1e-6) break;
        t -= e / d;
      }
      return sy(Math.min(1, Math.max(0, t)));
    };
  }
  const EASE_DATA = bezier(0.16, 1, 0.3, 1);
  const DUR_DATA = 320;

  // ------------------------------------------------------------------ formatting
  const isNum = v => v !== null && v !== undefined && isFinite(v);
  function f(v, k = 1, sign = false) {
    if (!isNum(v)) return '–';
    const s = Math.abs(v).toFixed(k);
    const zero = Number(s) === 0;
    const pre = zero ? '' : v < 0 ? MINUS : sign ? '+' : '';
    return pre + s;
  }
  const fInt = d3.format(',');
  const fP = p => !isNum(p) ? '–' : p < 0.001 ? '< 0.001' : p < 0.1 ? p.toFixed(3) : p.toFixed(2);
  const fPeq = p => !isNum(p) ? 'p = –' : p < 0.001 ? 'p < 0.001' : 'p = ' + fP(p);
  const fPct = (v, k = 0) => !isNum(v) ? '–' : (v * 100).toFixed(k) + '%';
  const mLab = m => d3.timeFormat('%b %Y')(parseM(m));
  const mLong = m => d3.timeFormat('%B %Y')(parseM(m));
  const dLab = s => { const d = parseD(String(s).slice(0, 10)); return d ? d3.timeFormat('%b %-d, %Y')(d) : String(s); };
  const dShort = s => { const d = parseD(String(s).slice(0, 10)); return d ? d3.timeFormat('%b %-d')(d) : String(s); };
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const css = name => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  const period = s => s.replace('..', ' to ');
  const periodShort = s => { const [a, b] = s.split('..'); return mLab(a) + '–' + mLab(b); };

  // ------------------------------------------------------------------ series helpers
  const pand0 = idx(D.meta.pandemic[0]), pand1 = idx(D.meta.pandemic[1]);
  const isPand = i => i >= pand0 && i <= pand1;
  const mixed0 = idx(D.meta.mode.first_mixed), web0 = idx(D.meta.mode.first_web);
  const mean = a => { const v = a.filter(isNum); return v.length ? d3.mean(v) : null; };
  function trailing(a, w = 3, minN = 2) {
    return a.map((_, i) => {
      const v = [];
      for (let k = Math.max(0, i - w + 1); k <= i; k++) if (isNum(a[k])) v.push(a[k]);
      return isNum(a[i]) && v.length >= minN ? d3.mean(v) : null;
    });
  }
  function zscore(a, ref = a) {
    const v = ref.filter(isNum);
    const mu = d3.mean(v), sd = d3.deviation(v);
    return a.map(x => isNum(x) ? (x - mu) / sd : null);
  }
  const smoothOn = () => S.smooth === '3';
  const sm = a => smoothOn() ? trailing(a) : a;

  // The model is not applied in pandemic months (frozen design): model, interval and gap are left empty there and the
  // months are shaded and labelled instead. The 2010-19 fit includes the first out-of-sample month so the two lines join.
  function confSeries(dv) {
    const c = D.conf[dv];
    const oos = i => !c.in_sample[i] && !isPand(i);
    const first = c.in_sample.indexOf(false);
    const lo = c['pi' + S.pi + 'lo'], hi = c['pi' + S.pi + 'hi'];
    const keep = (arr, ok) => arr.map((v, i) => (ok(i) ? v : null));
    return {
      actual: c.actual.slice(),
      fit: keep(c.pred, i => c.in_sample[i] || i === first),
      pred: keep(c.pred, oos),
      lo: keep(lo, oos), hi: keep(hi, oos),
      gap: keep(c.gap, oos),
      resid: keep(c.gap, i => c.in_sample[i] || i === first),
    };
  }
  // interval layer, out of sample; centred subtracts the model so the band sits on zero
  function bandLayers(c, centred, focus) {
    const ctr = (a, ref) => a.map((v, i) => (isNum(v) ? v - (centred ? ref[i] : 0) : null));
    return [{ key: 'band', kind: 'band', lo: ctr(c.lo, c.pred), hi: ctr(c.hi, c.pred), color: 'var(--c-model-band)', focus }];
  }
  const DV_NAME = { ics: 'Sentiment index (ICS)', icc: 'Current conditions (ICC)', ice: 'Expectations (ICE)' };
  const DV_SHORT = { ics: 'ICS', icc: 'ICC', ice: 'ICE' };
  const GROUP_ORDER = ['national', 'mc_national', 'local', 'reddit', 'youtube'];
  const gcol = g => `var(--c-${g})`;

  // ------------------------------------------------------------------ state
  const S = {
    dv: 'ics', pi: '95', smooth: '3',
    groups: new Set(['national', 'local', 'youtube']),
    framing: 'national',
    layers: new Set(['shutdown', 'trade', 'election', 'mode']),
    range: [idx('2017-01'), N - 1],
    hover: null, pin: null,
  };
  const linked = [];     // time charts that share the monitor's range and crosshair
  let uid = 0;

  // ------------------------------------------------------------------ tooltip
  const tip = document.getElementById('tip');
  function showTip(html, ev) {
    tip.innerHTML = html;
    tip.classList.add('on');
    const pad = 14, w = tip.offsetWidth, h = tip.offsetHeight;
    let x = ev.clientX + pad, y = ev.clientY + pad;
    if (x + w > window.innerWidth - 8) x = ev.clientX - w - pad;
    if (y + h > window.innerHeight - 8) y = ev.clientY - h - pad;
    tip.style.left = Math.max(8, x) + 'px';
    tip.style.top = Math.max(8, y) + 'px';
  }
  const hideTip = () => tip.classList.remove('on');

  // ------------------------------------------------------------------ time chart
  /* A chart is a pure function of a frame: {x:[ms0, ms1], y:[lo, hi], layers:[...]}. Updates interpolate
     the previous frame into the next one (domain and values together), so axis changes, index switches
     and interval changes morph instead of jumping. */
  class TimeChart {
    constructor(el, o) {
      this.el = el;
      this.o = Object.assign({ height: 200, m: { t: 10, r: 14, b: 22, l: 38 }, lane: 0, linked: false, yTicks: 5,
        yFmt: v => f(v, 0) }, o);
      this.id = 'tc' + (++uid);
      this.svg = d3.select(el).append('svg').attr('role', 'img').attr('aria-label', o.aria || '');
      const defs = this.svg.append('defs');
      this.clip = defs.append('clipPath').attr('id', this.id + 'c').append('rect');
      this.gGrid = this.svg.append('g').attr('class', 'grid');
      this.gShade = this.svg.append('g');
      this.gPlot = this.svg.append('g').attr('clip-path', `url(#${this.id}c)`);
      this.gBand = this.gPlot.append('g');
      this.gLine = this.gPlot.append('g');
      this.gPts = this.gPlot.append('g');
      this.gAnn = this.svg.append('g');
      this.gX = this.svg.append('g').attr('class', 'axis x');
      this.gY = this.svg.append('g').attr('class', 'axis y');
      this.gLane = this.svg.append('g');
      this.gEnd = this.svg.append('g');
      this.gPin = this.svg.append('g').attr('class', 'pin');
      this.gHair = this.svg.append('g').attr('class', 'xhair').style('display', 'none');
      this.hit = this.svg.append('rect').attr('class', 'hit');
      this.cur = null;
      this.focusKey = null;
      this.width = el.clientWidth || 600;
      this.hgt = el.clientHeight;
      if (this.o.fill) { el.classList.add('fill'); el.style.setProperty('--minh', this.o.fill + 'px'); this.o.height = () => Math.max(this.o.fill, el.clientHeight); }
      this.hit.on('pointermove', ev => this.onMove(ev)).on('pointerleave', () => this.onLeave())
        .on('click', ev => this.onClick(ev));
      new ResizeObserver(() => {
        const w = el.clientWidth, h = el.clientHeight;
        if (!w) return;  // hidden tab
        if ((Math.abs(w - this.width) > 1) || (this.o.fill && Math.abs(h - this.hgt) > 1)) { this.width = w; this.hgt = h; this.render(); }
      }).observe(el);
    }
    dims() {
      const m = this.o.m, H = typeof this.o.height === 'function' ? this.o.height() : this.o.height;
      return { m, W: this.width, H, iw: this.width - m.l - m.r, ih: H - m.t - m.b - this.o.lane };
    }
    update(anim = true) {
      const next = this.o.frame();
      if (!this.cur || !anim || REDUCE) { this.cur = next; this.render(); return; }
      const from = this.cur;
      if (this.timer) this.timer.stop();
      this.target = next;
      this.timer = d3.timer(el => {
        const t = Math.min(1, el / DUR_DATA), e = EASE_DATA(t);
        this.cur = lerpFrame(from, next, e);
        this.render();
        if (t >= 1) { this.timer.stop(); this.timer = null; this.cur = next; this.render(); }
      });
    }
    scales() {
      const { m, iw, ih } = this.dims();
      const c = this.cur;
      this.x = d3.scaleTime().domain([new Date(c.x[0]), new Date(c.x[1])]).range([m.l, m.l + iw]);
      this.y = d3.scaleLinear().domain(c.y).range([m.t + ih, m.t]);
      return { x: this.x, y: this.y };
    }
    render() {
      if (!this.cur) return;
      const { m, W, H, iw, ih } = this.dims();
      const c = this.cur;
      this.svg.attr('width', W).attr('height', H).attr('viewBox', `0 0 ${W} ${H}`);
      this.clip.attr('x', m.l).attr('y', m.t - 4).attr('width', Math.max(0, iw + 1)).attr('height', ih + 8);
      const { x, y } = this.scales();
      // grid + y axis
      const yt = y.ticks(this.o.yTicks);
      this.gGrid.selectAll('line').data(yt).join('line')
        .attr('x1', m.l).attr('x2', m.l + iw).attr('y1', d => Math.round(y(d)) + 0.5).attr('y2', d => Math.round(y(d)) + 0.5);
      this.gY.attr('transform', `translate(${m.l - 6},0)`)
        .call(d3.axisLeft(y).tickValues(yt).tickSize(0).tickFormat(v => (!this.o.lane && y(v) > m.t + ih - 4 ? '' : this.o.yFmt(v))));
      const nt = Math.max(2, Math.floor(iw / 78));
      const span = (c.x[1] - c.x[0]) / (365.25 * 864e5);
      const xf = d => (d.getMonth() === 0 ? d3.timeFormat('%Y')(d) : d3.timeFormat(span > 2.5 ? '%Y' : '%b')(d));
      let ticks = x.ticks(nt);
      if (span > 2.5) ticks = ticks.filter(d => d.getMonth() === 0);
      this.gX.attr('transform', `translate(0,${m.t + ih + this.o.lane})`)
        .call(d3.axisBottom(x).tickValues(ticks).tickSize(4).tickFormat(xf));
      // shaded spans
      this.gShade.selectAll('g').data(c.shades || [], d => d.key).join(en => {
        const g = en.append('g');
        g.append('rect').attr('class', 'shade-rect');
        g.append('text').attr('class', 'shade-label');
        return g;
      }).each(function (d) {
        const x0 = Math.max(m.l, x(new Date(d.x0))), x1 = Math.min(m.l + iw, x(new Date(d.x1)));
        const g = d3.select(this).style('display', x1 > x0 ? null : 'none');
        g.select('rect').attr('x', x0).attr('y', m.t).attr('width', Math.max(0, x1 - x0)).attr('height', ih)
          .style('fill', d.fill || null);
        g.select('text').attr('x', d.anchor === 'end' ? x1 - 4 : x0 + 4).attr('y', m.t + 11)
          .attr('text-anchor', d.anchor === 'end' ? 'end' : 'start')
          .text(x1 - x0 > (d.label || '').length * 5.2 ? d.label || '' : '');
      });
      // bands
      const bands = c.layers.filter(l => l.kind === 'band');
      this.gBand.selectAll('path').data(bands, d => d.key).join(en => en.append('path').attr('class', 'band').style('opacity', 0)
        .call(p => p.transition().duration(REDUCE ? 0 : 250).style('opacity', 1)))
        .attr('class', d => 'band' + (this.focusKey && d.focus === this.focusKey ? ' focus' : ''))
        .style('fill', d => d.color)
        .attr('d', d => d3.area().defined(i => isNum(d.lo[i]) && isNum(d.hi[i]))
          .x(i => x(T[i])).y0(i => y(d.lo[i])).y1(i => y(d.hi[i])).curve(d3.curveLinear)(d3.range(N)));
      // lines
      const lines = c.layers.filter(l => l.kind === 'line');
      this.gLine.selectAll('path').data(lines, d => d.key).join(en => en.append('path').style('opacity', 0)
        .call(p => p.transition().duration(REDUCE ? 0 : 250).style('opacity', null)))
        .attr('class', d => 'series ' + (d.cls || '') + (this.focusKey && (d.focus || d.key) === this.focusKey ? ' focus' : ''))
        .style('stroke', d => d.color).style('color', d => d.color)
        .attr('d', d => d3.line().defined(i => isNum(d.v[i])).x(i => x(T[i])).y(i => y(d.v[i]))(d3.range(N)));
      this.svg.classed('dim', !!this.focusKey);
      // point layers (low-count markers, claims)
      const pts = c.layers.filter(l => l.kind === 'points');
      this.gPts.selectAll('g').data(pts, d => d.key).join('g').each(function (d) {
        d3.select(this).selectAll('circle').data(d.pts).join('circle')
          .attr('cx', p => x(new Date(p.t))).attr('cy', p => y(p.y)).attr('r', p => p.r || 3)
          .style('fill', p => p.fill || 'none').style('stroke', p => p.stroke || 'none').style('stroke-width', 1.2);
      });
      // annotations: horizontal segments, vertical markers, free labels
      const ann = c.ann || [];
      this.gAnn.selectAll('g.a').data(ann, d => d.key).join(en => {
        const g = en.append('g').attr('class', 'a').style('opacity', 0);
        g.transition().duration(REDUCE ? 0 : 300).style('opacity', 1);
        g.append('line');
        g.append('text');
        return g;
      }).each(function (d) {
        const g = d3.select(this);
        if (d.type === 'seg') {
          const x0 = Math.max(m.l, x(new Date(d.x0))), x1 = Math.min(m.l + iw, x(new Date(d.x1)));
          const vis = x1 > x0 + 2;
          g.style('display', vis ? null : 'none');
          g.select('line').attr('class', 'periodseg').attr('x1', x0).attr('x2', x1).attr('y1', y(d.y)).attr('y2', y(d.y));
          g.select('text').attr('class', 'periodlab').attr('x', (x0 + x1) / 2).attr('y', y(d.y) + (d.below ? 13 : -5))
            .attr('text-anchor', 'middle').text(x1 - x0 > 22 ? d.label : '');
        } else if (d.type === 'vline') {
          const xx = x(new Date(d.x0));
          const vis = xx >= m.l && xx <= m.l + iw;
          g.style('display', vis ? null : 'none');
          g.select('line').attr('x1', xx).attr('x2', xx).attr('y1', m.t).attr('y2', m.t + ih)
            .style('stroke', d.color || 'var(--axis)').style('stroke-dasharray', '2 3');
          g.select('text').attr('class', 'ann').attr('x', xx + 4).attr('y', m.t + (d.dy || 11)).text(d.label || '');
        } else if (d.type === 'hline') {
          g.select('line').attr('class', 'zero').attr('x1', m.l).attr('x2', m.l + iw).attr('y1', Math.round(y(d.y)) + 0.5)
            .attr('y2', Math.round(y(d.y)) + 0.5);
          g.select('text').attr('class', 'ann').attr('x', m.l + 4).attr('y', y(d.y) - 4).text(d.label || '');
        }
      });
      // end labels at the last visible point of labelled lines
      const lab = lines.filter(l => l.end);
      const pos = lab.map(l => {
        const last = lastVisible(l.v, c.x);
        return last == null ? null : { l, x: x(T[last]), y: y(l.v[last]) };
      }).filter(Boolean);
      dodge(pos, 11);
      this.gEnd.selectAll('text').data(pos, d => d.l.key).join('text').attr('class', 'endlab')
        .attr('x', d => d.x + 6).attr('y', d => d.yy + 3.5).style('fill', d => d.l.labelColor || d.l.color).text(d => d.l.end);
      // events lane
      if (this.o.lane) {
        const ev = (this.o.events ? this.o.events() : []).filter(e => e.t >= c.x[0] && e.t <= c.x[1]);
        const ly = m.t + ih + 4;
        this.gLane.selectAll('line').data(ev, d => d.key).join('line')
          .attr('class', d => 'ev-tick ev-' + d.kind).attr('x1', d => x(new Date(d.t))).attr('x2', d => x(new Date(d.t)))
          .attr('y1', ly).attr('y2', ly + this.o.lane - 6)
          .on('pointerenter', (e, d) => showTip(`<b>${esc(dLab(d.date))}</b><br>${esc(d.label)}`, e)).on('pointerleave', hideTip);
      }
      this.hit.attr('x', m.l).attr('y', m.t).attr('width', Math.max(0, iw)).attr('height', ih);
      if (this.o.after) this.o.after(this, { x, y, m, iw, ih });
      this.drawHover(this.o.linked ? S.hover : this.localHover);
      this.drawPin();
    }
    indexAt(px) {
      const t = +this.x.invert(px);
      let i = d3.bisectLeft(TMS, t);
      if (i > 0 && (i >= N || t - TMS[i - 1] < TMS[i] - t)) i--;
      return Math.max(0, Math.min(N - 1, i));
    }
    onMove(ev) {
      const [px] = d3.pointer(ev, this.svg.node());
      let i = this.indexAt(px);
      if (this.o.linked) { if (i < S.range[0]) i = S.range[0]; if (i > S.range[1]) i = S.range[1]; setHover(i); }
      else { this.localHover = i; this.drawHover(i); }
    }
    onLeave() {
      if (this.o.linked) setHover(null); else { this.localHover = null; this.drawHover(null); }
    }
    onClick(ev) {
      const [px] = d3.pointer(ev, this.svg.node());
      openInspector(this.indexAt(px));
    }
    drawHover(i) {
      const ro = this.o.readout;
      if (ro) ro(i == null ? this.defaultIndex() : i, i == null);
      if (i == null || !this.cur) { this.gHair.style('display', 'none'); return; }
      const { m, ih } = this.dims();
      const xx = this.x(T[i]);
      if (xx < m.l - 1 || xx > m.l + this.dims().iw + 1) { this.gHair.style('display', 'none'); return; }
      this.gHair.style('display', null);
      this.gHair.selectAll('line').data([0]).join('line').attr('x1', xx).attr('x2', xx).attr('y1', m.t).attr('y2', m.t + ih);
      const dots = this.cur.layers.filter(l => l.kind === 'line' && !l.nodot && isNum(l.v[i]));
      this.gHair.selectAll('circle').data(dots, d => d.key).join('circle').attr('r', 3.5)
        .attr('cx', xx).attr('cy', d => this.y(d.v[i])).style('fill', d => d.color);
    }
    drawPin() {
      const i = S.pin;
      if (i == null || !this.cur || !this.o.linked) { this.gPin.selectAll('*').remove(); return; }
      const { m, ih, iw } = this.dims();
      const xx = this.x(T[i]);
      const vis = xx >= m.l && xx <= m.l + iw;
      this.gPin.selectAll('line').data(vis ? [0] : []).join('line').attr('x1', xx).attr('x2', xx).attr('y1', m.t).attr('y2', m.t + ih);
    }
    defaultIndex() {
      if (!this.cur) return N - 1;
      return Math.min(N - 1, this.indexAt(this.x ? this.x(new Date(this.cur.x[1])) : 0));
    }
    focus(key) { this.focusKey = key; this.render(); }
  }
  function lastVisible(v, xd) {
    for (let i = N - 1; i >= 0; i--) if (TMS[i] <= xd[1] + 1 && TMS[i] >= xd[0] - 1 && isNum(v[i])) return i;
    return null;
  }
  function dodge(pos, gap) {
    pos.sort((a, b) => a.y - b.y);
    pos.forEach((p, k) => { p.yy = k ? Math.max(p.y, pos[k - 1].yy + gap) : p.y; });
  }
  function lerpArr(a, b, e) {
    if (!a) return b;
    const out = new Array(N);
    for (let i = 0; i < N; i++) {
      const p = a[i], q = b[i];
      out[i] = isNum(q) ? (isNum(p) ? p + (q - p) * e : q) : null;
    }
    return out;
  }
  function lerpFrame(A, B, e) {
    const L = n => n + (0) * e;
    const byKey = {};
    A.layers.forEach(l => { byKey[l.key] = l; });
    const layers = B.layers.map(l => {
      const p = byKey[l.key];
      if (l.kind === 'line') return Object.assign({}, l, { v: lerpArr(p && p.v, l.v, e) });
      if (l.kind === 'band') return Object.assign({}, l, { lo: lerpArr(p && p.lo, l.lo, e), hi: lerpArr(p && p.hi, l.hi, e) });
      return l;
    });
    return Object.assign({}, B, {
      x: [A.x[0] + (B.x[0] - A.x[0]) * e, A.x[1] + (B.x[1] - A.x[1]) * e],
      y: [A.y[0] + (B.y[0] - A.y[0]) * e, A.y[1] + (B.y[1] - A.y[1]) * e].map(L),
      layers,
    });
  }

  // ------------------------------------------------------------------ shared range helpers
  const rangeX = () => [TMS[S.range[0]], TMS[S.range[1]]];
  function inRange(i) { return i >= S.range[0] && i <= S.range[1]; }
  function yExtent(arrs, pad = 0.08, floor = null) {
    let lo = Infinity, hi = -Infinity;
    arrs.forEach(a => a.forEach((v, i) => { if (isNum(v) && inRange(i)) { lo = Math.min(lo, v); hi = Math.max(hi, v); } }));
    if (!isFinite(lo)) return floor ? floor.slice() : [0, 1];
    if (floor) { lo = Math.min(lo, floor[0]); hi = Math.max(hi, floor[1]); }
    const p = (hi - lo) * pad || 1;
    return d3.scaleLinear().domain([lo - p, hi + p]).nice(5).domain();
  }
  const PAND_NOTE = 'Pandemic months: model not applied';
  const PAND_SHADE = { key: 'pand', x0: TMS[pand0], x1: TMS[pand1] + 30 * 864e5, label: 'Pandemic' };
  function shadesBase() {
    const out = [];
    out.push(PAND_SHADE);
    if (S.layers.has('mode')) {
      out.push({ key: 'mixed', x0: TMS[mixed0], x1: TMS[web0], label: '', fill: 'var(--shade-2)' });
      out.push({ key: 'web', x0: TMS[web0], x1: TMS[N - 1] + 30 * 864e5, label: 'Web interviews', fill: 'var(--shade)', anchor: 'end' });
    }
    return out;
  }
  const EVENTS = D.events.map((e, k) => ({ ...e, key: 'e' + k, t: +parseD(e.date) }));
  const eventsOn = () => EVENTS.filter(e => S.layers.has(e.kind)).concat(S.layers.has('mode') ? [
    { key: 'mx', kind: 'mode', t: TMS[mixed0], date: M[mixed0] + '-01', label: 'Michigan begins mixing web and phone interviews' },
    { key: 'mw', kind: 'mode', t: TMS[web0], date: M[web0] + '-01', label: 'Michigan interviews entirely on the web' }] : []);

  // ------------------------------------------------------------------ odometer numbers
  function odo(el, text) {
    el.classList.add('odo');
    el.setAttribute('aria-label', text);
    const sig = [...text].map(ch => (/\d/.test(ch) ? 'd' : ch)).join('');
    if (el.dataset.sig !== sig || REDUCE) {
      el.dataset.sig = sig;
      el.innerHTML = [...text].map(ch => /\d/.test(ch)
        ? `<span class="odo-col" aria-hidden="true"><span class="odo-strip" style="transform:translateY(-${Number(ch) * 1.2}em)">${'0123456789'.split('').map(d => `<span>${d}</span>`).join('')}</span></span>`
        : `<span aria-hidden="true">${esc(ch)}</span>`).join('');
      return;
    }
    [...text].forEach((ch, k) => {
      const c = el.children[k];
      if (/\d/.test(ch)) c.firstChild.style.transform = `translateY(-${Number(ch) * 1.2}em)`;
    });
  }

  // ------------------------------------------------------------------ header, intro, status
  const P = D.periods.ics;
  const per = key => P.find(p => p.period === key);
  const P25 = P.find(p => p.start === '2025-01'), P26 = P.find(p => p.start === '2026-01');
  const P2122 = P.find(p => p.start === '2021-07');
  const meta = D.meta;
  function buildIntro() {
    document.getElementById('introTitle').textContent =
      `Consumers are about ${Math.round(-P25.gap)} to ${Math.round(-P26.gap)} points gloomier than the economy predicts, and the news does not explain why`;
    document.getElementById('introLede').innerHTML =
      `Each month the University of Michigan sentiment index is compared with a model that uses only unemployment, inflation and GDP growth as published at the time. ` +
      `AI-coded economic news (${fInt(D.coverage.total_coded)} sampled items) measures tone, framing and blame. The tabs above go from the gap itself to what was ruled out and what to watch around Election Day.`;
    const ics = meta.michigan;
    const i = idx(ics.month);
    const c = D.conf.ics;
    const today = new Date();
    const el = parseD(meta.election), cut = parseD(meta.cutoff);
    const dToEl = Math.round((el - d3.timeDay.floor(today)) / 864e5);
    const afterCut = Math.round((el - cut) / 864e5);
    const elTxt = dToEl > 0 ? `in ${dToEl} day${dToEl === 1 ? '' : 's'}` : dToEl === 0 ? 'today' : `${-dToEl} days ago`;
    document.getElementById('statusBoard').innerHTML = `
      <div><div class="lab"><span>Michigan ICS, ${esc(mLab(ics.month))}</span><span class="tag">${ics.status === 'prelim' ? 'Preliminary' : 'Final'}</span></div>
        <div class="val">${f(ics.value, 1)}</div><div class="sub">Released ${esc(dShort(ics.released))}${ics.status === 'prelim' ? `; final due ${esc(dShort(ics.final_due))}` : ''}</div></div>
      <div><div class="lab"><span><span class="swatch" style="background:var(--c-model)"></span>Fundamentals model</span></div>
        <div class="val">${f(c.pred[i], 1)}</div><div class="sub">95% interval ${f(c.pi95lo[i], 1)} to ${f(c.pi95hi[i], 1)}</div></div>
      <div><div class="lab"><span><span class="swatch" style="background:var(--c-gap)"></span>Gap this month</span></div>
        <div class="val">${f(c.gap[i], 1)}</div><div class="sub">2025 average ${f(P25.gap, 1)}; 2026 so far ${f(P26.gap, 1)}</div></div>
      <div><div class="lab"><span>Share of the fall since 2019 explained</span></div>
        <div class="val">${fPct(Math.min(P25.explained, P26.explained))}–${fPct(Math.max(P25.explained, P26.explained))}</div><div class="sub">by the three fundamentals, 2025 and 2026</div></div>
      <div class="wide"><span class="lab" style="display:block">Election Day, ${esc(dLab(meta.election))}</span><span class="val">${elTxt}</span><span class="sub">${afterCut} days after the data cutoff</span></div>`;
    const sha = meta.prompt_sha256 ? meta.prompt_sha256.slice(0, 8) : 'not recorded';
    const nNote = meta.media_note ? 'warn' : '';
    document.getElementById('buildInfo').innerHTML = [
      `<span class="chip"><span class="dot"></span>Data cutoff <b>${esc(dLab(meta.cutoff))}</b></span>`,
      `<span class="chip">Michigan <b>${esc(mLab(ics.month))}</b> ${ics.status === 'prelim' ? 'preliminary' : 'final'}, released ${esc(dShort(ics.released))}</span>`,
      `<span class="chip">Unemployment <b>${esc(mLab(meta.unemployment.ref.slice(0, 7)))}</b>, released ${esc(dShort(meta.unemployment.released))}</span>`,
      `<span class="chip">PCE prices <b>${esc(mLab(meta.pce.ref.slice(0, 7)))}</b>, released ${esc(dShort(meta.pce.released))}</span>`,
      `<span class="chip">GDP <b>${esc(meta.gdp.ref)}</b>, released ${esc(dShort(meta.gdp.released))}</span>`,
      `<span class="chip ${nNote}" title="${esc(meta.media_note || '')}"><span class="dot"></span>News coded through <b>${esc(mLab(meta.media_last))}</b> (partial month)</span>`,
      `<span class="chip">Prompt <b>${esc(meta.prompt.replace('.md', ''))}</b> <span class="mono">${esc(sha)}</span></span>`,
      `<span class="chip">Coder <b>${esc(meta.model)}</b>, reasoning ${esc(meta.effort.replace(' (default)', ''))}</span>`,
    ].join('');
  }

  // ------------------------------------------------------------------ findings (stepper)
  const natRel = D.media.national.n_relevant.filter(isNum);
  const natRelMed = d3.median(natRel);
  const fc = D.forecast;
  const mainSpec = fc.specs.find(s => s.key === 'main');
  const nSig3 = fc.specs.filter(s => s.p_m3 < 0.05).length;
  const party25 = D.party.periods.find(p => p.period.startsWith('2025'));
  const demoP2 = D.demo.rows.map(r => r.p2);
  const W = D.windows;
  const wRange = (k) => [d3.min(W, w => w[k]), d3.max(W, w => w[k])];
  const ME = D.mode_effects;
  // the gap is standardised on non-pandemic months only
  const zGap = zscore(D.conf.ics.gap.map((v, i) => (isPand(i) ? null : v)));
  const zTone = zscore(trailing(D.media.national.net_tone));
  const STEPS = [
    {
      title: 'Sentiment versus a fundamentals model', short: 'Sentiment vs model', head: 'Confidence fell far below what the economy implies',
      body: [`The Michigan sentiment index averaged <b>${f(P25.actual, 1)}</b> in 2025 and <b>${f(P26.actual, 1)}</b> in 2026 so far. A model fit on 2010–2019, using only unemployment, inflation and GDP growth as published before each survey month, predicts <b>${f(P25.pred, 1)}</b> and <b>${f(P26.pred, 1)}</b>.`,
        'The shaded band is the 95% prediction interval from a moving-block bootstrap. Pandemic months are left out because the model is not meant for them.'],
      src: 'results/stage1_m1/m1_gap_monthly.csv',
    },
    {
      title: 'Gap between actual sentiment and the model', short: 'Size of the gap', head: `A gap of ${f(P25.gap, 1)} points in 2025 and ${f(P26.gap, 1)} in 2026`,
      body: [`The three fundamentals account for only ${fPct(P25.explained)} of the fall since 2019 in 2025 and ${fPct(P26.explained)} in 2026. The 95% band for a period mean is about ±${f((P25.hi95 - P25.lo95) / 2, 0)} points, so the gap is far outside model error.`,
        `Across ${W.length} estimation windows the 2025 gap ranges from ${f(wRange('gap2025')[1], 1)} to ${f(wRange('gap2025')[0], 1)} and the 2026 gap from ${f(wRange('gap2026')[1], 1)} to ${f(wRange('gap2026')[0], 1)}. The 2021–22 gap depends on the window (${f(wRange('gap2122')[1], 1)} to ${f(wRange('gap2122')[0], 1)}), so it is reported as a range.`],
      src: 'results/stage1_m1/m1_periods.csv; results/stage1_windows/m1_windows.csv',
    },
    {
      title: 'Gap with the survey-mode change marked', short: 'Survey and party', head: 'Survey mode and party mix explain little of it',
      body: [`Michigan moved from phone to web interviews between ${mLab(meta.mode.first_mixed)} and ${mLab(meta.mode.first_web)}. The switch is associated with a step of ${f(ME.icc.coef, 1)} points in current conditions (${fPeq(ME.icc.p)}) and ${f(ME.ics.coef, 1)} points in the headline index (${fPeq(ME.ics.p)}). The gap kept widening after interviews were entirely on the web.`,
        `A plausible shift in the share of Republican respondents moves the index by at most ${f(D.party.composition_max, 1)} points. Republicans themselves were ${f(-party25.rep, 0)} points below their own 2017–19 level in 2025.`],
      src: 'results/stage1_h3/h3a_mode.csv; h3b_composition_bound.csv; h3b_party_periods.csv',
    },
    {
      title: 'Gap and national news tone, in standard deviations', short: 'News tone', head: 'News tone adds little once household and political conditions are known',
      body: [`LLM-coded tone of national economic news (NYT and Guardian, about ${Math.round(natRelMed)} relevant items a month) improves one-month forecasts of the fundamentals model slightly (${fPeq(mainSpec.p_m2)}). Once household-stress and political controls are in the model, it adds nothing (${fPeq(mainSpec.p_m3)}; ${nSig3} of ${fc.specs.length} specifications significant).`,
        `At most about ${fPct(fc.tone_share_max)} of the 2025–26 gap is associated with tone. Both series are standardised over 2010–2026; tone is a 3-month mean.`],
      src: 'results/stage3_forecast/comparisons.csv; results/stage3_robustness/variants.csv, magnitude.csv',
    },
    {
      title: 'Gap by demographic group, two periods', short: 'By group', head: 'What remains is broad and unexplained',
      body: [`In ${periodShort(D.demo.periods[1])} every income, age, region and education group sits between ${f(d3.max(demoP2), 1)} and ${f(d3.min(demoP2), 1)} points below its own model, a spread of ${f(d3.max(demoP2) - d3.min(demoP2), 1)} points. In 2021–22 the gaps were smaller and more uneven.`,
        'Fundamentals, survey mode, party composition, election timing and news tone each leave most of the 2025–26 gap unexplained. Price levels, policy uncertainty and individual information processing remain hypotheses for further work.'],
      src: 'results/stage5_mechanisms/group_gaps_monthly.csv',
    },
  ];
  let storyStep = -1, storyChart, storyDots;
  function storyFrame() {
    const c = confSeries('ics');
    const s = Math.max(0, storyStep);
    const xs = [TMS[0], TMS[N - 1]];
    const shades = [PAND_SHADE];
    if (s === 0) {
      return { x: xs, y: [30, 120], shades: shades.concat([{ key: 'est', x0: TMS[0], x1: TMS[idx('2019-12')] + 30 * 864e5, label: 'Estimation window 2010–2019', fill: 'transparent' }]),
        layers: bandLayers(c, false).concat([
          { key: 'fit', kind: 'line', v: c.fit, color: 'var(--c-model)', cls: 'dash thin', nodot: true },
          { key: 'pred', kind: 'line', v: c.pred, color: 'var(--c-model)', end: 'Model' },
          { key: 'act', kind: 'line', v: c.actual, color: 'var(--c-actual)', end: 'Actual' }]),
        ann: [] };
    }
    const segs = P.filter(p => p.start !== '2020-01').map(p => ({ key: 'seg' + p.start, type: 'seg', x0: TMS[idx(p.start)],
      x1: TMS[idx(p.end)] + 30 * 864e5, y: p.gap, label: f(p.gap, 1), below: true }));
    const outOfSample = D.conf.ics.in_sample.map(v => (v ? null : 0));
    if (s === 1 || s === 2) {
      const sh = s === 2 ? shades.concat([{ key: 'mixed', x0: TMS[mixed0], x1: TMS[web0], fill: 'var(--shade-2)', label: '' },
        { key: 'web', x0: TMS[web0], x1: TMS[N - 1] + 30 * 864e5, label: 'Web interviews', fill: 'var(--shade-2)', anchor: 'end' }]) : shades;
      return { x: xs, y: [-62, 26], shades: sh, layers: bandLayers(c, true).concat([
        { key: 'fit', kind: 'line', v: c.fit.map(v => (isNum(v) ? 0 : null)), color: 'var(--c-model)', cls: 'dash thin', nodot: true },
        { key: 'pred', kind: 'line', v: outOfSample, color: 'var(--c-model)', cls: 'thin', end: 'Model = 0', nodot: true },
        { key: 'res', kind: 'line', v: c.resid, color: 'var(--c-gap)' },
        { key: 'act', kind: 'line', v: c.gap, color: 'var(--c-gap)', end: 'Gap' }]),
      ann: segs };
    }
    // step 3 (and the time view behind the dot plot)
    const zAll = zTone.concat(zGap).filter(isNum);
    return { x: xs, y: d3.scaleLinear().domain([d3.min(zAll) - 0.3, d3.max(zAll) + 0.3]).nice(6).domain(), shades,
      layers: [
        { key: 'band', kind: 'band', lo: N_NULL, hi: N_NULL, color: 'var(--c-model-band)' },
        { key: 'pred', kind: 'line', v: T.map(() => 0), color: 'var(--axis)', cls: 'thin', nodot: true },
        { key: 'tone', kind: 'line', v: zTone, color: 'var(--c-national)', end: 'News tone' },
        { key: 'act', kind: 'line', v: zGap, color: 'var(--c-gap)', end: 'Gap' }],
      ann: [] };
  }
  const N_NULL = T.map(() => null);
  function buildStory() {
    document.getElementById('stepDots').innerHTML = STEPS.map((st, k) =>
      `<button type="button" class="step-dot" role="tab" data-step="${k}" aria-selected="false">${k + 1}. ${esc(st.short)}</button>`).join('');
    document.querySelectorAll('#stepDots .step-dot').forEach(b => b.addEventListener('click', () => setStep(+b.dataset.step)));
    document.getElementById('stepPrev').addEventListener('click', () => setStep(storyStep - 1));
    document.getElementById('stepNext').addEventListener('click', () => setStep(storyStep + 1));
    const stage = document.getElementById('stageChart');
    const tw = document.createElement('div');
    tw.className = 'chart stage-fade';
    stage.appendChild(tw);
    storyChart = new TimeChart(tw, {
      height: () => stage.clientHeight || 420, m: { t: 14, r: 74, b: 24, l: 36 }, yTicks: 6,
      frame: storyFrame, aria: 'Michigan sentiment and the fundamentals model',
      readout: null,
    });
    storyChart.onClick = () => {};
    const dw = document.createElement('div');
    dw.className = 'chart stage-fade';
    dw.style.cssText = 'position:absolute;inset:0;opacity:0;pointer-events:none';
    stage.appendChild(dw);
    storyDots = dw;
    setStep(0);
    new ResizeObserver(() => { if (storyStep === 4 && stage.clientWidth) drawDemo(); }).observe(stage);
  }
  function setStep(k) {
    if (k < 0 || k >= STEPS.length || k === storyStep) return;
    const prev = storyStep;
    storyStep = k;
    const s = STEPS[k];
    const sc = document.getElementById('stepCard');
    sc.innerHTML = `<div class="step-n">${String(k + 1).padStart(2, '0')} / ${String(STEPS.length).padStart(2, '0')}</div>
      <h3>${esc(s.head)}</h3>${s.body.map(p => `<p>${p}</p>`).join('')}`;
    sc.classList.remove('swap');
    void sc.offsetWidth;
    sc.classList.add('swap');
    document.querySelectorAll('#stepDots .step-dot').forEach(b => b.setAttribute('aria-selected', +b.dataset.step === k));
    document.getElementById('stepPrev').disabled = k === 0;
    document.getElementById('stepNext').disabled = k === STEPS.length - 1;
    document.getElementById('stageTitle').textContent = s.title;
    document.getElementById('stageSrc').innerHTML = 'Source: ' + s.src.split('; ').map(x => `<code>${esc(x)}</code>`).join('; ');
    const pandKey = ['shade', 'var(--shade)', PAND_NOTE];
    const key = {
      0: [['line', 'var(--c-actual)', 'Michigan ICS'], ['line', 'var(--c-model)', 'Model, out of sample'], ['dash', 'var(--c-model)', 'Model, in sample'], ['band', 'var(--c-model-band)', '95% interval'], pandKey],
      1: [['line', 'var(--c-gap)', 'Gap (actual − model)'], ['band', 'var(--c-model-band)', '95% interval'], ['seg', 'var(--ink)', 'Period mean'], pandKey],
      2: [['line', 'var(--c-gap)', 'Gap'], ['shade', 'var(--shade-2)', 'Web interviews'], pandKey],
      3: [['line', 'var(--c-gap)', 'Gap'], ['line', 'var(--c-national)', 'National news tone'], pandKey],
      4: [['dot-o', 'var(--c-model)', periodShort(D.demo.periods[0])], ['dot', 'var(--c-gap)', periodShort(D.demo.periods[1])]],
    }[k];
    document.getElementById('stageKey').innerHTML = key.map(([t, c, l]) => `<span class="keyitem">${keySwatch(t, c)}${esc(l)}</span>`).join('');
    const tw = storyChart.el;
    if (k === 4) {
      tw.style.opacity = 0;
      storyDots.style.opacity = 1;
      storyDots.style.pointerEvents = 'auto';
      drawDemo();
    } else {
      tw.style.opacity = 1;
      storyDots.style.opacity = 0;
      storyDots.style.pointerEvents = 'none';
      storyChart.update(prev !== -1 && prev !== 4);
    }
  }
  function keySwatch(t, c) {
    if (t === 'line') return `<span class="keyline" style="color:${c}"></span>`;
    if (t === 'dash') return `<span class="keyline dash" style="color:${c}"></span>`;
    if (t === 'band') return `<span class="keyband" style="background:${c}"></span>`;
    if (t === 'shade') return `<span class="keyband shade" style="background:${c}"></span>`;
    if (t === 'seg') return `<span class="keyline" style="color:${c};border-top-width:1.5px"></span>`;
    if (t === 'dot') return `<span class="keydot" style="background:${c}"></span>`;
    if (t === 'dot-o') return `<span class="keydot" style="border:1.5px solid ${c}"></span>`;
    if (t === 'ring') return `<span class="keydot" style="border:1.5px solid ${c};background:var(--surface)"></span>`;
    return '';
  }
  function drawDemo() {
    const el = storyDots;
    const W0 = el.clientWidth || 600, H0 = el.clientHeight || 420;
    const rows = D.demo.rows;
    const dims = [...new Set(rows.map(r => r.dim))];
    const m = { t: 10, r: 18, b: 30, l: Math.min(150, W0 * 0.34) };
    const lines = [];
    dims.forEach((d, k) => { if (k) lines.push({ gap: true }); rows.filter(r => r.dim === d).forEach(r => lines.push(r)); });
    const y = d3.scaleBand().domain(d3.range(lines.length)).range([m.t, H0 - m.b]).padding(0.2);
    const x = d3.scaleLinear().domain([-50, 5]).range([m.l, W0 - m.r]);
    const svg = d3.select(el).selectAll('svg').data([0]).join('svg').attr('width', W0).attr('height', H0)
      .attr('role', 'img').attr('aria-label', 'Gap by demographic group in two periods');
    svg.selectAll('g.gx').data([0]).join('g').attr('class', 'axis x gx').attr('transform', `translate(0,${H0 - m.b})`)
      .call(d3.axisBottom(x).ticks(6).tickSize(-(H0 - m.b - m.t)).tickFormat(v => f(v, 0)))
      .call(g => g.selectAll('line').style('stroke', 'var(--grid)'));
    svg.selectAll('text.xl').data([0]).join('text').attr('class', 'ann xl').attr('x', W0 - m.r).attr('y', H0 - 2)
      .attr('text-anchor', 'end').text('Gap relative to the group’s own model, index points');
    svg.selectAll('line.z').data([0]).join('line').attr('class', 'zero z').attr('x1', x(0)).attr('x2', x(0)).attr('y1', m.t).attr('y2', H0 - m.b);
    const g = svg.selectAll('g.rows').data([0]).join('g').attr('class', 'rows');
    const rr = lines.map((r, k) => ({ ...r, k })).filter(r => !r.gap);
    const row = g.selectAll('g.r').data(rr, d => d.key).join(en => {
      const e = en.append('g').attr('class', 'r');
      e.append('line').attr('class', 'conn');
      e.append('text').attr('class', 'ann lab');
      e.append('circle').attr('class', 'p1');
      e.append('circle').attr('class', 'p2');
      return e;
    });
    const cy = d => y(d.k) + y.bandwidth() / 2;
    row.select('text.lab').attr('x', m.l - 8).attr('y', d => cy(d) + 3.5).attr('text-anchor', 'end')
      .text(d => (d.dim === 'Region' || d.dim === 'Education' ? d.label : d.dim + ': ' + d.label.replace(/^[A-Z](?=[a-z])/, c => c.toLowerCase())));
    row.select('line.conn').attr('x1', d => x(d.p1)).attr('x2', d => x(d.p2)).attr('y1', cy).attr('y2', cy).style('stroke', 'var(--axis)').style('stroke-width', 1.5);
    row.select('circle.p1').attr('cx', d => x(d.p1)).attr('cy', cy).attr('r', 4.5).style('fill', 'var(--surface)').style('stroke', 'var(--c-model)').style('stroke-width', 1.6);
    row.select('circle.p2').attr('cx', d => (REDUCE ? x(d.p2) : x(d.p1))).attr('cy', cy).attr('r', 5).style('fill', 'var(--c-gap)')
      .transition().duration(REDUCE ? 0 : 520).delay((d, k) => k * 25).ease(EASE_DATA).attr('cx', d => x(d.p2));
    row.on('pointerenter', (e, d) => showTip(`<b>${esc(d.dim)}: ${esc(d.label)}</b><br>${esc(periodShort(D.demo.periods[0]))}: ${f(d.p1, 1)}<br>${esc(periodShort(D.demo.periods[1]))}: ${f(d.p2, 1)}`, e))
      .on('pointerleave', hideTip);
  }

  // ------------------------------------------------------------------ monitor: dock and overview
  function seg(id, label, opts, get, set) {
    const html = `<div class="ctl"><span class="ctl-lab" id="${id}L">${label}</span><div class="seg" role="group" aria-labelledby="${id}L" id="${id}">
      <span class="thumb"></span>${opts.map(([v, t]) => `<button type="button" data-v="${v}" aria-pressed="${get() === v}">${t}</button>`).join('')}</div></div>`;
    return { html, wire() {
      const root = document.getElementById(id);
      const place = () => {
        const b = root.querySelector('[aria-pressed="true"]');
        const th = root.querySelector('.thumb');
        if (b) { th.style.width = b.offsetWidth + 'px'; th.style.transform = `translateX(${b.offsetLeft}px)`; }
      };
      root.querySelectorAll('button').forEach(b => b.addEventListener('click', () => {
        root.querySelectorAll('button').forEach(x => x.setAttribute('aria-pressed', x === b));
        place();
        set(b.dataset.v);
      }));
      requestAnimationFrame(place);
      if (document.fonts) document.fonts.ready.then(place);
      new ResizeObserver(place).observe(root);
    } };
  }
  const LAYERS = [['mode', 'Survey mode', 'var(--c-model)'], ['election', 'Elections', 'var(--ink)'], ['shutdown', 'Shutdowns', 'var(--c-bad)'],
    ['trade', 'Tariffs and trade', 'var(--c-mc_national)'], ['fomc', 'FOMC statements', 'var(--faint)']];
  function buildDock() {
    const segs = [
      seg('segDv', 'Index', [['ics', 'ICS'], ['icc', 'ICC'], ['ice', 'ICE']], () => S.dv, v => { S.dv = v; refresh(); }),
      seg('segPi', 'Interval', [['80', '80%'], ['95', '95%']], () => S.pi, v => { S.pi = v; refresh(); }),
      seg('segSm', 'News series', [['1', 'Monthly'], ['3', '3-month mean']], () => S.smooth, v => { S.smooth = v; refresh(); }),
    ];
    const presets = [['2010-01', 'All'], ['2017-01', '2017–'], ['2021-01', '2021–'], ['2024-01', '2024–']];
    document.getElementById('dockControls').innerHTML = segs.map(s => s.html).join('') +
      `<div class="ctl"><span class="ctl-lab">Events</span><div class="pills" id="layerPills">${LAYERS.map(([k, t, c]) =>
        `<button type="button" class="pill" data-k="${k}" aria-pressed="${S.layers.has(k)}" style="color:${c}"><span class="sw"></span><span class="txt">${t}</span></button>`).join('')}</div></div>` +
      `<div class="ctl"><span class="ctl-lab">Period</span><div class="presets" id="presets">${presets.map(([m, t]) => `<button type="button" data-m="${m}">${t}</button>`).join('')}</div></div>`;
    segs.forEach(s => s.wire());
    document.querySelectorAll('#layerPills .pill').forEach(b => b.addEventListener('click', () => {
      const k = b.dataset.k;
      if (S.layers.has(k)) S.layers.delete(k); else S.layers.add(k);
      b.setAttribute('aria-pressed', S.layers.has(k));
      refresh();
    }));
    document.querySelectorAll('#presets button').forEach(b => b.addEventListener('click', () => setRange([idx(b.dataset.m), N - 1], true)));
  }
  let ov;
  function buildOverview() {
    const el = document.getElementById('overviewStrip');
    const svg = d3.select(el).append('svg');
    const gArea = svg.append('g'), gAx = svg.append('g').attr('class', 'axis x'), gB = svg.append('g').attr('class', 'brush');
    const brush = d3.brushX().on('brush end', ev => {
      if (!ev.sourceEvent) return;
      if (!ev.selection) return;
      const [a, b] = ev.selection.map(px => ov.x.invert(px));
      let i0 = d3.bisectLeft(TMS, +a), i1 = d3.bisectLeft(TMS, +b);
      i0 = Math.max(0, Math.min(N - 2, i0));
      i1 = Math.max(i0 + 1, Math.min(N - 1, i1));
      setRange([i0, i1], false, ev.type === 'end');
    });
    ov = { el, svg, gArea, gAx, gB, brush, x: null, draw() {
      const w = el.clientWidth, h = 46, m = { l: 8, r: 8, t: 4, b: 16 };
      if (!w) return;
      svg.attr('width', w).attr('height', h);
      const x = d3.scaleTime().domain([T[0], T[N - 1]]).range([m.l, w - m.r]);
      this.x = x;
      const gap = D.conf[S.dv].gap.map((v, i) => (isPand(i) ? null : v));
      const y = d3.scaleLinear().domain([-60, 25]).range([h - m.b, m.t]);
      gArea.selectAll('path.a').data([0]).join('path').attr('class', 'a').style('fill', 'var(--c-gap-band)')
        .attr('d', d3.area().defined(i => isNum(gap[i])).x(i => x(T[i])).y0(y(0)).y1(i => y(gap[i]))(d3.range(N)));
      gArea.selectAll('path.l').data([0]).join('path').attr('class', 'l').style('fill', 'none').style('stroke', 'var(--c-gap)').style('stroke-width', 1)
        .attr('d', d3.line().defined(i => isNum(gap[i])).x(i => x(T[i])).y(i => y(gap[i]))(d3.range(N)));
      gArea.selectAll('line.z').data([0]).join('line').attr('class', 'zero z').attr('x1', m.l).attr('x2', w - m.r).attr('y1', y(0)).attr('y2', y(0));
      gAx.attr('transform', `translate(0,${h - m.b})`).call(d3.axisBottom(x).ticks(d3.timeYear.every(w < 600 ? 4 : 2)).tickSize(3).tickFormat(d3.timeFormat('%Y')));
      brush.extent([[m.l, m.t], [w - m.r, h - m.b]]);
      gB.call(brush);
      gB.call(brush.move, [x(T[S.range[0]]), x(T[S.range[1]])]);
    } };
    ov.draw();
    new ResizeObserver(() => { if (el.clientWidth) ov.draw(); }).observe(el);
  }
  function setRange(r, anim, settle = true) {
    S.range = r;
    if (ov && anim) ov.gB.call(ov.brush.move, [ov.x(T[r[0]]), ov.x(T[r[1]])]);
    linked.forEach(c => c.update(anim));
    if (settle) { updateKpis(); renderEventList(); renderFramingHeat(); updateCardKeys(); }
  }
  function refresh() {
    linked.forEach(c => c.update(true));
    if (ov) ov.draw();
    updateKpis();
    renderEventList();
    renderFramingHeat();
    updateLegends();
    updateCardKeys();
  }
  // card takeaways that depend on the period shown
  function updateCardKeys() {
    const [a, b] = S.range;
    let j = null;
    for (let i = b; i >= a; i--) if (isNum(D.party.dem[i])) { j = i; break; }
    const pk = document.getElementById('mPartyK');
    if (pk) pk.textContent = j == null ? 'No party breakdown in the period shown.'
      : `In ${mLab(M[j])} Democrats were ${f(D.party.dem[j], 0)}, Independents ${f(D.party.ind[j], 0)} and Republicans ${f(D.party.rep[j], 0)} points from their own 2017–19 levels.`;
    const fk = document.getElementById('mFrameK');
    if (fk) {
      const md = D.media[S.framing];
      const top = D.topics.map((name, k) => ({ name, v: mean(md[topicCol(k)].slice(a, b + 1)) }))
        .filter(d => isNum(d.v) && d.name !== 'Other').sort((p, q) => q.v - p.v).slice(0, 3);
      fk.textContent = top.length ? `Most-mentioned topics in ${md.label.toLowerCase()} over the period shown: ${top.map(d => `${d.name.toLowerCase()} (${fPct(d.v)})`).join(', ')}.`
        : `No coded ${md.label.toLowerCase()} in the period shown.`;
    }
  }
  function setHover(i) {
    S.hover = i;
    linked.forEach(c => c.drawHover(i));
    if (heat) heat.hover(i);
  }

  // ------------------------------------------------------------------ monitor: KPI tiles
  function buildKpis() {
    const tiles = [
      ['k1', 'Latest reading'], ['k2', 'Mean gap in view'], ['k3', 'Months below the band'], ['k4', 'National news tone in view'], ['k5', 'News items coded in view'],
    ];
    document.getElementById('kpis').innerHTML = tiles.map(([k, l]) => `<div class="kpi" id="${k}"><div class="kpi-lab" id="${k}l">${l}</div>
      <div class="kpi-row"><span class="kpi-val" id="${k}v"></span><span class="kpi-unit" id="${k}u"></span></div><div class="kpi-sub" id="${k}s"></div></div>`).join('');
  }
  const natTone1019 = mean(D.media.national.net_tone.slice(0, idx('2019-12') + 1));
  function updateKpis() {
    const [a, b] = S.range;
    const c = confSeries(S.dv);
    const status = D.econ.status[b];
    document.getElementById('k1l').textContent = `${DV_SHORT[S.dv]}, ${mLab(M[b])}${status === 'prelim' ? ' (preliminary)' : ''}`;
    odo(document.getElementById('k1v'), f(c.actual[b], 1));
    const pr = D.conf[S.dv].pred[b];
    setDelta('k1s', isNum(c.gap[b]) ? `<span class="delta rise">${f(c.gap[b], 1, true)} vs model</span> model ${f(pr, 1)}` : isPand(b) ? 'Pandemic month, model not applied' : `model ${f(pr, 1)} (in sample)`);
    const gaps = [], below = [];
    let oosN = 0;
    for (let i = a; i <= b; i++) {
      if (isNum(c.gap[i])) { gaps.push(c.gap[i]); oosN++; if (isNum(c.lo[i]) && c.actual[i] < c.lo[i]) below.push(i); }
    }
    document.getElementById('k2l').textContent = `Mean ${DV_SHORT[S.dv]} gap, ${mLab(M[a])}–${mLab(M[b])}`;
    odo(document.getElementById('k2v'), gaps.length ? f(d3.mean(gaps), 1) : '–');
    document.getElementById('k2u').textContent = 'points';
    document.getElementById('k2s').textContent = gaps.length ? `${gaps.length} out-of-sample months (pandemic months excluded)` : 'No out-of-sample months in view';
    document.getElementById('k3l').textContent = `Months below the ${S.pi}% band`;
    odo(document.getElementById('k3v'), oosN ? String(below.length) : '–');
    document.getElementById('k3u').textContent = oosN ? `of ${oosN}` : '';
    document.getElementById('k3s').textContent = below.length ? `First in view: ${mLab(M[below[0]])}` : 'None in view';
    const nt = sm(D.media.national.net_tone).slice(a, b + 1);
    const ntm = mean(nt);
    odo(document.getElementById('k4v'), f(ntm, 2));
    document.getElementById('k4u').textContent = 'net tone';
    setDelta('k4s', isNum(ntm) ? `<span class="delta rise">${f(ntm - natTone1019, 2, true)}</span> vs 2010–19 mean ${f(natTone1019, 2)}` : '');
    let coded = 0, rel = 0;
    GROUP_ORDER.forEach(g => { for (let i = a; i <= b; i++) { coded += D.media[g].n_coded[i] || 0; rel += D.media[g].n_relevant[i] || 0; } });
    odo(document.getElementById('k5v'), fInt(coded));
    document.getElementById('k5u').textContent = 'items';
    document.getElementById('k5s').textContent = `${fInt(rel)} judged relevant by the LLM`;
  }
  function setDelta(id, html) {
    const el = document.getElementById(id);
    if (el.dataset.h === html) return;
    el.dataset.h = html;
    el.innerHTML = html;
  }

  // ------------------------------------------------------------------ monitor: cards
  function card(host, o) {
    const d = document.createElement('div');
    d.className = 'card ' + (o.span || 'span-12');
    d.style.setProperty('--i', o.i || 0);
    d.id = o.id;
    d.innerHTML = `<div class="card-head"><div><div class="card-title">${o.title}</div>${o.key !== undefined ? `<div class="card-key" id="${o.id}K">${o.key}</div>` : ''}${o.desc ? `<div class="card-desc">${o.desc}</div>` : ''}</div>
      ${o.tools ? `<div class="card-tools">${o.tools}</div>` : ''}<div class="readout" id="${o.id}R"></div></div>
      ${o.legend ? `<div class="legend" id="${o.id}L"></div>` : ''}<div class="chart" id="${o.id}C"></div>${o.after || ''}
      ${o.src ? `<p class="src">Source: ${o.src.split('; ').map(x => `<code>${esc(x)}</code>`).join('; ')}</p>` : ''}`;
    host.appendChild(d);
    return d;
  }
  const RO = (id, html) => { const el = document.getElementById(id + 'R'); if (el) el.innerHTML = html; };
  let confC, gapC, partyC, toneC, attrC, salC, factC, heat;
  function buildMonitor() {
    const hostS = document.getElementById('bentoS'), hostN = document.getElementById('bentoN');
    const c95 = D.conf.ics, k0 = idx('2021-07');
    let nOos = 0, nBelow = 0;
    for (let i = k0; i < N; i++) if (isNum(c95.pi95lo[i]) && isNum(c95.actual[i])) { nOos++; if (c95.actual[i] < c95.pi95lo[i]) nBelow++; }
    card(hostS, { id: 'mConf', span: 'span-8', i: 0, title: 'Michigan sentiment against the fundamentals model', legend: true,
      key: `Since July 2021 the headline index has been below the model’s 95% band in ${nBelow} of ${nOos} months.`,
      desc: 'Model: unemployment, PCE inflation and GDP growth as published before each survey month, fit on 2010–2019. Grey band: pandemic months, where the model is not applied. Ticks below the axis mark the events chosen above.',
      src: 'results/stage1_m1/m1_gap_monthly.csv; provenance/events.csv' });
    card(hostS, { id: 'mGap', span: 'span-4', i: 1, title: 'Gap: actual minus model',
      key: `The gap averaged ${f(P2122.gap, 1)} in 2021–22 and ${f(P26.gap, 1)} in 2026 so far (headline index).`,
      desc: 'Band: the prediction interval re-centred on zero. Grey line: 2010–19 fit residuals. Grey area: pandemic months, model not applied.', src: 'results/stage1_m1/m1_gap_monthly.csv; m1_periods.csv' });
    card(hostS, { id: 'mParty', span: 'span-7', i: 2, title: 'Partisans against their own 2017–19 level', legend: true, key: '',
      desc: 'ICS by party identification, change from each group’s 2017–19 mean.', src: 'results/stage1_h3/h3b_party_monthly.csv' });
    card(hostS, { id: 'mEv', span: 'span-5', i: 3, title: 'Events and elections in view', desc: 'Filtered by the event types chosen above. Most recent first.',
      src: 'provenance/events.csv; provenance/political_elections.csv', after: '<div class="rel-list" id="evList" style="max-height:300px;overflow:auto"></div>' });
    const b17 = D.bias;
    card(hostN, { id: 'mTone', span: 'span-8', i: 0, title: 'Tone of economic news and posts, by source', legend: true,
      key: 'Coverage turned more negative in 2025–26, but no more than economic conditions predict (Tests, criterion 1).',
      desc: 'Net tone = share positive − share negative among items the LLM judged relevant, design-weighted. Hollow points mark thin months.',
      src: 'features/media_monthly.csv' });
    card(hostN, { id: 'mAttr', span: 'span-4', i: 1, title: 'Blame and credit for the administration', legend: true,
      key: `Blame on the administration: ${b17.map(b => `${esc(b.admin.replace(/ \d.*$/, ''))} ${fPct(b.blame)} (${esc(b.admin.replace(/^\D+/, ''))})`).join(', ')}.`,
      desc: 'National news: share of relevant items that blame or credit the president or administration. Lines mark the mean for each administration.',
      src: 'features/media_monthly.csv; results/stage2_bias/attribution_means.csv' });
    card(hostN, { id: 'mFrame', span: 'span-8', i: 2, title: 'Framing: which topics the coverage is about', key: '',
      desc: 'Share of relevant items that mention each topic (an item can mention several). Darker means a larger share.',
      tools: `<label class="ctl"><span class="ctl-lab">Source</span><select class="select" id="frameSel">${GROUP_ORDER.map(g => `<option value="${g}">${esc(D.media[g].label)}</option>`).join('')}</select></label>`,
      src: 'features/media_monthly.csv' });
    card(hostN, { id: 'mSal', span: 'span-4', i: 3, title: 'Salience: estimated volume of relevant items',
      desc: 'Relevant items in the full collection, estimated from the coded sample. Uses the source chosen for framing.', src: 'features/media_monthly.csv' });
    const natF = D.factcal.by_source.find(r => r.source === 'national news');
    card(hostN, { id: 'mFact', span: 'span-12', i: 4, title: 'Factual calibration of quoted numbers', legend: true,
      key: `Numbers quoted in national news are rarely wrong: ${natF.wrong} errors in ${natF.verifiable} verifiable claims (${fPct(natF.error_rate, 1)}).`,
      desc: 'Each point is a numeric claim in national news about inflation, jobs, unemployment or GDP, checked against the official value available on the publication date.',
      src: 'results/stage2_factcal/claims.csv; summary.csv', after: '<div id="factSum"></div>' });

    confC = new TimeChart(document.getElementById('mConfC'), {
      linked: true, fill: 318, lane: 16, m: { t: 10, r: 62, b: 22, l: 36 }, aria: 'Michigan index, model prediction and interval',
      events: eventsOn,
      frame() {
        const c = confSeries(S.dv);
        return { x: rangeX(), y: yExtent([c.actual, c.pred, c.lo, c.hi, c.fit], 0.06), shades: shadesBase(),
          layers: bandLayers(c, false, 'pred').concat([
            { key: 'fit', kind: 'line', v: c.fit, color: 'var(--c-model)', cls: 'dash thin', focus: 'pred', nodot: true },
            { key: 'pred', kind: 'line', v: c.pred, color: 'var(--c-model)', end: 'Model' },
            { key: 'act', kind: 'line', v: c.actual, color: 'var(--c-actual)', end: DV_SHORT[S.dv] }]),
          ann: [] };
      },
      readout(i) {
        const c = confSeries(S.dv);
        const head = `<span class="m">${mLab(M[i])}</span><span>${DV_SHORT[S.dv]} <b>${f(c.actual[i], 1)}</b></span>`;
        RO('mConf', isPand(i) ? head + '<span class="m">pandemic, model not applied</span>'
          : head + `<span>Model <b>${f(D.conf[S.dv].pred[i], 1)}</b></span>` +
            (isNum(c.lo[i]) ? `<span>${S.pi}% <b>${f(c.lo[i], 1)}–${f(c.hi[i], 1)}</b></span>` : '<span class="m">in sample</span>'));
      },
    });
    gapC = new TimeChart(document.getElementById('mGapC'), {
      linked: true, fill: 240, m: { t: 8, r: 40, b: 22, l: 36 }, yTicks: 5, aria: 'Gap between actual and model',
      frame() {
        const c = confSeries(S.dv);
        const bands = bandLayers(c, true);
        return { x: rangeX(), y: yExtent([c.gap, c.resid].concat(bands.flatMap(b => [b.lo, b.hi])), 0.06, [-5, 5]),
          shades: shadesBase().filter(s => s.key === 'pand'),
          layers: bands.concat([
            { key: 'resid', kind: 'line', v: c.resid, color: 'var(--faint)', cls: 'thin', nodot: true },
            { key: 'gap', kind: 'line', v: c.gap, color: 'var(--c-gap)' }]),
          ann: [{ key: 'z', type: 'hline', y: 0 }] };
      },
      readout(i) {
        const g = D.conf[S.dv].gap[i];
        RO('mGap', `<span class="m">${mLab(M[i])}</span>` + (isPand(i) ? '<span class="m">pandemic, model not applied</span>' : `<span>Gap <b>${f(g, 1)}</b></span>`));
      },
    });
    const PK = [['dem', 'Democrats'], ['ind', 'Independents'], ['rep', 'Republicans']];
    partyC = new TimeChart(document.getElementById('mPartyC'), {
      linked: true, height: 230, m: { t: 8, r: 40, b: 22, l: 36 }, yTicks: 5, aria: 'Sentiment by party',
      frame() {
        return { x: rangeX(), y: yExtent(PK.map(([k]) => D.party[k]), 0.06, [-10, 10]), shades: [],
          layers: PK.map(([k, l]) => ({ key: k, kind: 'line', v: D.party[k], color: `var(--c-${k})`, cls: 'thin', end: l.slice(0, 3) + '.' })),
          ann: [{ key: 'z', type: 'hline', y: 0 }] };
      },
      readout(i, idle) {
        if (idle && !isNum(D.party.dem[i])) for (let k = i; k >= S.range[0]; k--) if (isNum(D.party.dem[k])) { i = k; break; }
        RO('mParty', isNum(D.party.dem[i]) ? `<span class="m">${mLab(M[i])}</span>` + PK.map(([k, l]) => `<span>${l.slice(0, 3)}. <b>${f(D.party[k][i], 0)}</b></span>`).join('')
          : `<span class="m">${mLab(M[i])}: no party data</span>`);
      },
    });
    toneC = new TimeChart(document.getElementById('mToneC'), {
      linked: true, fill: 250, m: { t: 10, r: 76, b: 22, l: 40 }, yTicks: 5, yFmt: v => f(v, 1), aria: 'News tone by source',
      frame() {
        const gs = GROUP_ORDER.filter(g => S.groups.has(g));
        const layers = gs.map(g => ({ key: g, kind: 'line', v: sm(D.media[g].net_tone), color: gcol(g), cls: g === 'national' ? '' : 'thin',
          end: D.media[g].label.replace(' comments', '').replace('Other national outlets', 'Other nat.').replace(' news', '') }));
        const pts = gs.map(g => ({ key: g + 'low', kind: 'points', pts: D.media[g].net_tone.map((v, i) => ({ i, v }))
          .filter(p => D.media[g].low_n[p.i] && isNum(sm(D.media[g].net_tone)[p.i]) && inRange(p.i))
          .map(p => ({ t: TMS[p.i], y: sm(D.media[g].net_tone)[p.i], r: 3, fill: 'var(--surface)', stroke: gcol(g) })) }));
        return { x: rangeX(), y: yExtent(layers.map(l => l.v), 0.06, [-0.2, 0]), shades: [],
          layers: layers.concat(pts), ann: [{ key: 'z', type: 'hline', y: 0 }] };
      },
      readout(i) {
        const gs = GROUP_ORDER.filter(g => S.groups.has(g));
        RO('mTone', `<span class="m">${mLab(M[i])}</span>` + gs.map(g => {
          const v = sm(D.media[g].net_tone)[i];
          return isNum(v) ? `<span><span class="swatch" style="background:${gcol(g)}"></span><b>${f(v, 2)}</b> <span class="m">n=${D.media[g].n_relevant[i]}</span></span>` : '';
        }).join(''));
      },
    });
    const bias = D.bias;
    attrC = new TimeChart(document.getElementById('mAttrC'), {
      linked: true, fill: 250, m: { t: 10, r: 44, b: 22, l: 36 }, yTicks: 5, yFmt: v => (v * 100).toFixed(0) + '%', aria: 'Blame and credit shares',
      frame() {
        const bl = sm(D.media.national.blame_admin_share), cr = sm(D.media.national.credit_admin_share);
        const segs = bias.map(b => ({ key: 'b' + b.start, type: 'seg', x0: TMS[idx(b.start)], x1: b.end ? TMS[idx(b.end)] + 30 * 864e5 : TMS[N - 1],
          y: b.blame, label: (b.blame * 100).toFixed(0) + '%' }));
        return { x: rangeX(), y: yExtent([bl, cr], 0.06, [0, 0.3]).map((v, k) => (k === 0 ? Math.max(0, v) : v)),
          shades: bias.filter(b => b.admin.startsWith('Trump')).map(b => ({ key: 's' + b.start, x0: TMS[idx(b.start)],
            x1: b.end ? TMS[idx(b.end)] + 30 * 864e5 : TMS[N - 1] + 30 * 864e5, label: b.admin.split(' ')[0], fill: 'var(--shade)' })),
          layers: [{ key: 'cr', kind: 'line', v: cr, color: 'var(--c-model)', cls: 'thin', end: 'Credit' },
            { key: 'bl', kind: 'line', v: bl, color: 'var(--c-gap)', end: 'Blame' }], ann: segs };
      },
      readout(i) {
        RO('mAttr', `<span class="m">${mLab(M[i])}</span><span>Blame <b>${fPct(sm(D.media.national.blame_admin_share)[i])}</b></span><span>Credit <b>${fPct(sm(D.media.national.credit_admin_share)[i])}</b></span>`);
      },
    });
    salC = new TimeChart(document.getElementById('mSalC'), {
      linked: true, fill: 228, m: { t: 10, r: 14, b: 22, l: 46 }, yTicks: 4, yFmt: d3.format('~s'), aria: 'Estimated relevant items',
      frame() {
        const g = S.framing;
        const v = sm(D.media[g].est_relevant_items);
        return { x: rangeX(), y: yExtent([v], 0.06, [0, 0]).map((q, k) => (k === 0 ? 0 : q)), shades: [],
          layers: [{ key: 'v', kind: 'line', v, color: gcol(g) }], ann: [] };
      },
      readout(i) {
        const g = S.framing;
        RO('mSal', `<span class="m">${mLab(M[i])}</span><span><b>${isNum(sm(D.media[g].est_relevant_items)[i]) ? fInt(Math.round(sm(D.media[g].est_relevant_items)[i])) : '–'}</b> items</span>`);
      },
    });
    const FC = D.factcal.claims.map(r => ({ date: r[0], source: r[1], frag: r[2], ind: r[3], claim: r[4], off: r[5], cat: r[6], why: r[7], t: +parseD(r[0]) }));
    const CATY = { correct: 2, correct_within_rounding: 2, wrong: 1, unverifiable: 0 };
    const CATC = { correct: 'var(--c-good)', correct_within_rounding: 'var(--c-good)', wrong: 'var(--c-bad)', unverifiable: 'var(--faint)' };
    factC = new TimeChart(document.getElementById('mFactC'), {
      linked: true, height: 150, m: { t: 10, r: 14, b: 22, l: 84 }, yTicks: 3, aria: 'Checked numeric claims',
      yFmt: v => ({ 2: 'Correct', 1: 'Wrong', 0: 'Unverifiable' }[v] || ''),
      frame() {
        const pts = FC.filter(p => p.t >= TMS[S.range[0]] && p.t <= TMS[S.range[1]] + 31 * 864e5)
          .map(p => ({ t: p.t, y: CATY[p.cat] + (((p.t / 864e5) % 7) - 3) * 0.04, r: 3.5, fill: CATC[p.cat], stroke: 'var(--surface)', p }));
        return { x: rangeX(), y: [-0.6, 2.6], shades: [], layers: [{ key: 'pts', kind: 'points', pts }], ann: [] };
      },
      after(ch, { x, y }) {
        ch.gPts.selectAll('circle').on('pointerenter', (e, d) => {
          const p = d.p;
          showTip(`<b>${esc(p.source)}, ${esc(dLab(p.date))}</b><br>${esc(p.frag || '')}<br>Claim ${esc(p.claim)} · official ${esc(p.off == null ? 'n/a' : p.off)}<br>${esc(p.cat.replace(/_/g, ' '))}${p.why ? ' (' + esc(p.why) + ')' : ''}`, e);
        }).on('pointerleave', hideTip).style('cursor', 'default');
        ch.gY.selectAll('text').attr('dy', '0.32em');
      },
      readout(i) {
        const n = FC.filter(p => p.date.slice(0, 7) === M[i]);
        RO('mFact', `<span class="m">${mLab(M[i])}</span><span><b>${n.length}</b> claim${n.length === 1 ? '' : 's'}</span>`);
      },
    });
    linked.push(confC, gapC, partyC, toneC, attrC, salC, factC);
    document.getElementById('frameSel').addEventListener('change', e => { S.framing = e.target.value; renderFramingHeat(); salC.update(true); updateCardKeys(); });
    buildHeat();
    renderFactSummary();
    updateLegends();
    linked.forEach(c => c.update(false));
    updateKpis();
    renderEventList();
  }
  function legendItem(key, color, label, type = 'line', pressed = null) {
    const sw = keySwatch(type, color);
    if (pressed === null) return `<span class="lg" data-key="${key}">${sw}${esc(label)}</span>`;
    return `<button type="button" class="pill" data-g="${key}" aria-pressed="${pressed}" style="color:${color}"><span class="sw"></span><span class="txt">${esc(label)}</span></button>`;
  }
  function updateLegends() {
    document.getElementById('mConfL').innerHTML = [legendItem('act', 'var(--c-actual)', DV_NAME[S.dv]), legendItem('pred', 'var(--c-model)', 'Model, out of sample'),
      legendItem('fit', 'var(--c-model)', 'Model, 2010–19 fit', 'dash'), legendItem('band', 'var(--c-model-band)', `${S.pi}% prediction interval`, 'band'), legendItem('', 'var(--shade)', PAND_NOTE, 'shade')].join('');
    document.getElementById('mPartyL').innerHTML = [['dem', 'Democrats'], ['ind', 'Independents'], ['rep', 'Republicans']]
      .map(([k, l]) => legendItem(k, `var(--c-${k})`, l)).join('');
    document.getElementById('mToneL').innerHTML = `<div class="pills">${GROUP_ORDER.map(g => legendItem(g, gcol(g), D.media[g].label, 'line', S.groups.has(g))).join('')}</div>`;
    document.getElementById('mAttrL').innerHTML = [legendItem('bl', 'var(--c-gap)', 'Blame'), legendItem('cr', 'var(--c-model)', 'Credit')].join('');
    document.getElementById('mFactL').innerHTML = [legendItem('c', 'var(--c-good)', 'Correct', 'dot'), legendItem('w', 'var(--c-bad)', 'Wrong', 'dot'), legendItem('u', 'var(--faint)', 'Unverifiable', 'dot')].join('');
    wireLegend('mConfL', confC);
    wireLegend('mPartyL', partyC);
    wireLegend('mAttrL', attrC);
    document.querySelectorAll('#mToneL .pill').forEach(b => {
      b.addEventListener('click', () => {
        const g = b.dataset.g;
        if (S.groups.has(g)) { if (S.groups.size > 1) S.groups.delete(g); } else S.groups.add(g);
        b.setAttribute('aria-pressed', S.groups.has(g));
        toneC.update(true);
      });
      b.addEventListener('pointerenter', () => { if (S.groups.has(b.dataset.g)) toneC.focus(b.dataset.g); });
      b.addEventListener('pointerleave', () => toneC.focus(null));
    });
  }
  function wireLegend(id, chart) {
    document.querySelectorAll('#' + id + ' .lg[data-key]:not([data-key=""])').forEach(el => {
      el.addEventListener('pointerenter', () => chart.focus(el.dataset.key === 'band' || el.dataset.key === 'fit' ? 'pred' : el.dataset.key));
      el.addEventListener('pointerleave', () => chart.focus(null));
    });
  }

  // framing heat strip (topics x months), linked to range and crosshair
  function buildHeat() {
    const el = document.getElementById('mFrameC');
    const svg = d3.select(el).append('svg').attr('role', 'img').attr('aria-label', 'Topic shares by month');
    const defs = svg.append('defs');
    defs.append('pattern').attr('id', 'hatch').attr('width', 4).attr('height', 4).attr('patternUnits', 'userSpaceOnUse')
      .attr('patternTransform', 'rotate(45)').append('line').attr('x1', 0).attr('y1', 0).attr('x2', 0).attr('y2', 4)
      .style('stroke', 'var(--faint)').style('stroke-width', 1);
    const gC = svg.append('g'), gY = svg.append('g').attr('class', 'axis y'), gX = svg.append('g').attr('class', 'axis x');
    const gH = svg.append('g').attr('class', 'xhair'), gPin = svg.append('g').attr('class', 'pin');
    const hit = svg.append('rect').attr('class', 'hit');
    heat = { el, svg, gC, gY, gX, gH, gPin, hit, x: null };
    heat.hover = i => {
      const g = S.framing, md = D.media[g];
      if (i == null || !heat.x) {
        heat.gH.selectAll('*').remove();
        const j = S.range[1];
        RO('mFrame', `<span class="m">${mLab(M[j])}</span><span>${topTopics(g, j)}</span>`);
        return;
      }
      const x0 = heat.x(T[i]);
      heat.gH.selectAll('line').data([0]).join('line').attr('x1', x0 + heat.bw / 2).attr('x2', x0 + heat.bw / 2).attr('y1', heat.m.t).attr('y2', heat.m.t + heat.ih);
      RO('mFrame', `<span class="m">${mLab(M[i])}</span><span>${topTopics(g, i)}</span><span class="m">n=${md.n_relevant[i] ?? 0}</span>`);
    };
    hit.on('pointermove', ev => {
      const [px] = d3.pointer(ev, svg.node());
      let i = d3.bisectLeft(TMS, +heat.x.invert(px)) - 1;
      i = Math.max(S.range[0], Math.min(S.range[1], i));
      setHover(i);
    }).on('pointerleave', () => setHover(null)).on('click', ev => {
      const [px] = d3.pointer(ev, svg.node());
      openInspector(Math.max(S.range[0], Math.min(S.range[1], d3.bisectLeft(TMS, +heat.x.invert(px)) - 1)));
    });
    new ResizeObserver(() => { if (el.clientWidth) renderFramingHeat(); }).observe(el);
    renderFramingHeat();
  }
  function topTopics(g, i) {
    const md = D.media[g];
    const t = D.topics.map((name, k) => ({ name, v: md[topicCol(k)][i] })).filter(d => isNum(d.v) && d.name !== 'Other')
      .sort((a, b) => b.v - a.v).slice(0, 3);
    return t.length ? t.map(d => `${esc(d.name)} <b>${fPct(d.v)}</b>`).join(' · ') : 'no coded items';
  }
  const TOPIC_KEYS = ['topic_layoffs_unemployment_up', 'topic_hiring_jobs_growth', 'topic_prices_rising', 'topic_inflation_easing', 'topic_economic_growth',
    'topic_recession_risk', 'topic_interest_rates_borrowing', 'topic_housing_costs', 'topic_gas_prices', 'topic_food_prices', 'topic_tariffs_trade',
    'topic_stock_market', 'topic_other'];
  const topicCol = k => TOPIC_KEYS[k];
  function renderFramingHeat() {
    if (!heat) return;
    const { el, svg, gC, gY, gX, hit } = heat;
    const w = el.clientWidth || 700;
    const g = S.framing, md = D.media[g];
    const rows = D.topics.slice(0, 12);
    const m = { t: 4, r: 8, b: 22, l: Math.min(165, Math.max(140, w * 0.3)) };
    const rh = 15, ih = rows.length * rh, H = ih + m.t + m.b;
    svg.attr('width', w).attr('height', H);
    const [a, b] = S.range;
    const x = d3.scaleTime().domain([T[a], d3.timeMonth.offset(T[b], 1)]).range([m.l, w - m.r]);
    heat.x = x; heat.m = m; heat.ih = ih;
    const bw = Math.max(1, (w - m.r - m.l) / (b - a + 1));
    heat.bw = bw;
    const vals = [];
    rows.forEach((_, r) => { for (let i = a; i <= b; i++) { const v = md[topicCol(r)][i]; if (isNum(v)) vals.push(v); } });
    const vmax = Math.max(0.2, d3.quantile(vals.sort(d3.ascending), 0.98) || 0.2);
    const col = d3.scaleLinear().domain([0, vmax * 0.25, vmax * 0.5, vmax * 0.75, vmax]).range(['--seq-0', '--seq-1', '--seq-2', '--seq-3', '--seq-4'].map(css)).clamp(true);
    const cells = [];
    rows.forEach((name, r) => {
      for (let i = a; i <= b; i++) {
        const v = md[topicCol(r)][i];
        if (md.n_coded[i] == null) continue;
        cells.push({ r, i, v, thin: md.low_n[i] });
      }
    });
    gC.selectAll('rect').data(cells, d => d.r + '-' + d.i).join('rect').attr('class', 'cell')
      .attr('x', d => x(T[d.i])).attr('y', d => m.t + d.r * rh).attr('width', bw + 0.3).attr('height', rh - 1)
      .style('fill', d => (isNum(d.v) ? col(d.v) : 'var(--surface-2)'));
    gY.attr('transform', `translate(${m.l - 6},0)`).selectAll('text').data(rows).join('text')
      .attr('x', 0).attr('y', (d, r) => m.t + r * rh + rh / 2 + 3.5).attr('text-anchor', 'end').text(d => d);
    const span = (b - a) / 12;
    let ticks = x.ticks(Math.max(2, Math.floor((w - m.l) / 78)));
    if (span > 2.5) ticks = ticks.filter(d => d.getMonth() === 0);
    gX.attr('transform', `translate(0,${m.t + ih})`).call(d3.axisBottom(x).tickValues(ticks).tickSize(3)
      .tickFormat(d => (d.getMonth() === 0 || span > 2.5 ? d3.timeFormat('%Y')(d) : d3.timeFormat('%b')(d))));
    hit.attr('x', m.l).attr('y', m.t).attr('width', Math.max(0, w - m.l - m.r)).attr('height', ih);
    heat.gPin.selectAll('line').data(S.pin != null && S.pin >= a && S.pin <= b ? [S.pin] : []).join('line')
      .attr('x1', d => x(T[d]) + bw / 2).attr('x2', d => x(T[d]) + bw / 2).attr('y1', m.t).attr('y2', m.t + ih);
    heat.hover(S.hover);
  }
  function renderFactSummary() {
    const bs = D.factcal.by_source;
    document.getElementById('factSum').innerHTML = `<div class="tbl-wrap"><table><thead><tr><th>Source</th><th class="r">Checked</th><th class="r">Correct</th><th class="r">Wrong</th><th class="r">Unverifiable</th><th class="r">Error rate</th></tr></thead><tbody>${
      bs.map(r => `<tr><td>${esc(r.source.replace(/^./, c => c.toUpperCase()))}</td><td class="r">${r.verifiable}</td><td class="r">${r.correct}</td><td class="r">${r.wrong}</td><td class="r">${r.unverifiable}</td><td class="r">${fPct(r.error_rate, 1)}</td></tr>`).join('')
    }</tbody></table></div><p class="note">An inflation figure that does not say whether it is CPI or PCE counts as unverifiable. Claims in Reddit and YouTube posts are reported only as counts; their text is not shown.</p>`;
  }
  function renderEventList() {
    const [a, b] = S.range;
    const t0 = TMS[a], t1 = TMS[b] + 31 * 864e5;
    const ev = eventsOn().filter(e => e.t >= t0 && e.t <= t1).sort((p, q) => q.t - p.t);
    const host = document.getElementById('evList');
    if (!host) return;
    const kindLab = { fomc: 'FOMC', shutdown: 'Shutdown', trade: 'Trade', election: 'Election', mode: 'Survey', other: 'Other' };
    host.innerHTML = ev.length ? ev.map(e => `<div class="rel"><span class="d">${esc(dLab(e.date))}</span>
      <span class="l">${e.url ? `<a href="${esc(e.url)}" target="_blank" rel="noopener">${esc(e.label)}</a>` : esc(e.label)}</span>
      <span class="tag" style="border-color:transparent;background:var(--shade-2)">${kindLab[e.kind] || e.kind}</span></div>`).join('')
      : '<p class="note">No events of the chosen types in this period.</p>';
  }

  // ------------------------------------------------------------------ inspector drawer
  const drawer = document.getElementById('drawer');
  const TONE = { n: ['Negative', 'tone-n'], p: ['Positive', 'tone-p'], m: ['Mixed', 'tone-m'], u: ['Neutral', 'tone-u'] };
  let hlFilter = 'rel';
  function openInspector(i) {
    S.pin = i;
    renderInspector();
    drawer.classList.add('open');
    drawer.setAttribute('aria-hidden', 'false');
    linked.forEach(c => c.drawPin());
    renderFramingHeat();
  }
  function closeInspector() {
    drawer.classList.remove('open');
    drawer.setAttribute('aria-hidden', 'true');
    S.pin = null;
    linked.forEach(c => c.drawPin());
    renderFramingHeat();
  }
  function renderInspector() {
    const i = S.pin, m = M[i];
    const e = D.econ;
    document.getElementById('drawerTitle').textContent = mLong(m);
    document.getElementById('drawerEyebrow').textContent = 'Month inspector';
    const flags = [];
    flags.push(e.status[i] === 'prelim' ? 'Michigan preliminary' : 'Michigan final');
    flags.push(isPand(i) ? 'Pandemic month, model not applied' : D.conf.ics.in_sample[i] ? 'Estimation window' : 'Out of sample');
    if (i >= web0) flags.push('Web interviews'); else if (i >= mixed0) flags.push('Mixed phone and web');
    GROUP_ORDER.forEach(g => { if (D.media[g].note[i]) flags.push(D.media[g].label + ': ' + D.media[g].note[i]); });
    const confRows = ['ics', 'icc', 'ice'].map(dv => {
      const c = D.conf[dv];
      return `<tr><td>${DV_SHORT[dv]}</td><td class="r">${f(c.actual[i], 1)}</td><td class="r">${f(c.pred[i], 1)}</td><td class="r">${isNum(c.pi95lo[i]) && !isPand(i) ? f(c.pi95lo[i], 1) + '–' + f(c.pi95hi[i], 1) : '–'}</td><td class="r">${f(c.gap[i], 1)}</td></tr>`;
    }).join('');
    const ym = s => (s ? mLab(String(s).slice(0, 7)) : '–');
    const est = { 1: 'advance', 2: 'second', 3: 'third' };
    const inputs = [
      ['Unemployment rate', `${f(e.u[i], 1)}%`, `${ym(e.u_ref[i])}, released ${e.u_rel[i] ? dShort(e.u_rel[i]) + ' ' + String(e.u_rel[i]).slice(0, 4) : '–'}`],
      ['PCE inflation, year on year', `${f(e.pce[i], 2)}%`, `${ym(e.pce_ref[i])}, released ${e.pce_rel[i] ? dLab(e.pce_rel[i]) : '–'}`],
      ['Real GDP growth, annualised', `${f(e.gdp[i], 2)}%`, `${e.gdp_ref[i] || '–'} ${est[e.gdp_est[i]] || (e.gdp_est[i] ? 'revised' : '')} estimate, released ${e.gdp_rel[i] ? dLab(e.gdp_rel[i]) : '–'}`],
      ['30-year mortgage rate', isNum(e.mort[i]) ? f(e.mort[i], 2) + '%' : '–', ''],
      ['Regular gasoline, $ per gallon', isNum(e.gas[i]) ? '$' + f(e.gas[i], 2) : '–', ''],
      ['PCE prices since Jan 2021', isNum(e.pce_cum[i]) ? f(e.pce_cum[i], 1, true) + '%' : '–', ''],
    ];
    const media = GROUP_ORDER.filter(g => isNum(D.media[g].n_coded[i])).map(g => {
      const md = D.media[g];
      return `<tr><td><span class="swatch" style="background:${gcol(g)}"></span>${esc(md.label)}</td><td class="r">${md.n_coded[i]}</td><td class="r">${md.n_relevant[i]}</td><td class="r">${f(md.net_tone[i], 2)}</td><td class="r">${fPct(md.blame_admin_share[i])}</td></tr>`;
    }).join('');
    const ev = EVENTS.filter(x => x.date.slice(0, 7) === m);
    const party = isNum(D.party.dem[i]) ? `<div class="kv">${[['dem', 'Democrats'], ['ind', 'Independents'], ['rep', 'Republicans']].map(([k, l]) =>
      `<span class="k">${l}</span><span class="v">${f(D.party[k][i], 1, true)}</span>`).join('')}</div>` : '<p class="note">No party breakdown for this month.</p>';
    const hl = D.headlines[m] || [];
    document.getElementById('drawerBody').innerHTML = `
      <div class="flags">${flags.map(x => `<span class="tag">${esc(x)}</span>`).join('')}</div>
      <div class="dsec"><h4>Michigan indexes and the model</h4><div class="tbl-wrap"><table><thead><tr><th>Index</th><th class="r">Actual</th><th class="r">Model</th><th class="r">95% interval</th><th class="r">Gap</th></tr></thead><tbody>${confRows}</tbody></table></div>
        <p class="src">Michigan ${e.status[i] === 'prelim' ? 'preliminary released ' + esc(dLab(e.mich_prelim[i])) + '; final due ' + esc(dLab(e.mich_final[i])) : 'final released ' + esc(dLab(e.mich_final[i]))}</p></div>
      <div class="dsec"><h4>What the model knew (information cutoff ${esc(dLab(e.origin[i]))})</h4>
        <div class="kv">${inputs.map(([k, v, s]) => `<span class="k">${k}${s ? `<br><small class="src" style="margin:0">${esc(s)}</small>` : ''}</span><span class="v">${v}</span>`).join('')}</div></div>
      <div class="dsec"><h4>News measures</h4>${media ? `<div class="tbl-wrap"><table><thead><tr><th>Source</th><th class="r">Coded</th><th class="r">Relevant</th><th class="r">Net tone</th><th class="r">Blame</th></tr></thead><tbody>${media}</tbody></table></div>` : '<p class="note">No coded items this month.</p>'}
        <p class="src" style="margin:0">Top national topics: ${topTopics('national', i)}</p></div>
      <div class="dsec"><h4>Partisans against their 2017–19 level</h4>${party}</div>
      ${ev.length ? `<div class="dsec"><h4>Events</h4>${ev.map(x => `<div class="kv"><span class="k">${esc(x.label)}</span><span class="v">${esc(dShort(x.date))}</span></div>`).join('')}</div>` : ''}
      <div class="dsec"><h4>Coded news items (${hl.length})</h4>
        <div class="hl-filter" id="hlFilter">${[['rel', 'Relevant'], ['n', 'Negative'], ['p', 'Positive'], ['all', 'All coded']].map(([k, l]) => `<button type="button" class="pill" data-f="${k}" aria-pressed="${hlFilter === k}"><span class="txt">${l}</span></button>`).join('')}</div>
        <div id="hlList"></div>
        <p class="src">Headlines from national and local outlets with the frozen LLM labels; labels are not individually human-checked. Reddit and YouTube text is not shown.</p></div>`;
    document.querySelectorAll('#hlFilter .pill').forEach(b => b.addEventListener('click', () => {
      hlFilter = b.dataset.f;
      document.querySelectorAll('#hlFilter .pill').forEach(x => x.setAttribute('aria-pressed', x === b));
      renderHeadlines(hl);
    }));
    renderHeadlines(hl);
  }
  function renderHeadlines(hl) {
    const keep = r => (hlFilter === 'all' ? true : hlFilter === 'rel' ? r[5] === 1 : r[5] === 1 && r[6] === hlFilter);
    const rows = hl.filter(keep);
    const GL = { national: 'National', mc_national: 'Other national', local: 'Local' };
    document.getElementById('hlList').innerHTML = rows.length ? rows.map(r => {
      const [g, date, outlet, title, url, rel, tone, , topics] = r;
      const tc = rel === 1 && TONE[tone] ? TONE[tone] : ['Not relevant', 'tone-x'];
      return `<div class="hl"><span class="td ${tc[1]}" title="${esc(tc[0])}"></span><div>
        ${url ? `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(title || '(untitled)')}</a>` : esc(title || '(untitled)')}
        <div class="meta">${esc(outlet)} · ${esc(dShort(date))} · ${GL[g]} · ${esc(tc[0])}${topics && topics.length ? ' · ' + topics.map(k => esc(D.topics[k])).join(', ') : ''}</div></div></div>`;
    }).join('') : '<p class="note">No items match this filter.</p>';
  }
  document.getElementById('drClose').addEventListener('click', closeInspector);
  document.getElementById('drPrev').addEventListener('click', () => stepInspector(-1));
  document.getElementById('drNext').addEventListener('click', () => stepInspector(1));
  function stepInspector(d) {
    if (S.pin == null) return;
    const i = Math.max(0, Math.min(N - 1, S.pin + d));
    if (i === S.pin) return;
    S.pin = i;
    renderInspector();
    linked.forEach(c => c.drawPin());
    renderFramingHeat();
    setHover(i);
  }
  document.addEventListener('keydown', ev => {
    if (!drawer.classList.contains('open')) return;
    if (ev.key === 'Escape') closeInspector();
    else if (ev.key === 'ArrowLeft' || ev.key === 'ArrowUp') { ev.preventDefault(); stepInspector(-1); }
    else if (ev.key === 'ArrowRight' || ev.key === 'ArrowDown') { ev.preventDefault(); stepInspector(1); }
  });

  // ------------------------------------------------------------------ measurement quality
  function buildQuality() {
    const host = document.getElementById('qualityGrid');
    const cov = D.coverage;
    card(host, { id: 'qCorpus', span: 'span-7', i: 0, title: 'Corpus and coded sample',
      desc: `Keyword-filtered items after removing ${fInt(cov.duplicates)} duplicates; ${fInt(cov.reposts)} syndicated copies are flagged. The LLM coded a stratified sample and judged relevance first.`,
      src: 'corpus/items_stats.json; labels/ai_corpus_labels.csv',
      after: `<div class="tbl-wrap"><table><thead><tr><th>Source</th><th class="r">In collection</th><th class="r">Coded</th><th class="r">Relevant</th><th>Relevant share of coded</th></tr></thead><tbody>${
        cov.rows.map(r => `<tr><td>${esc(r.source)}</td><td class="r">${fInt(r.frame)}</td><td class="r">${fInt(r.coded)}</td><td class="r">${fInt(r.relevant)}</td>
          <td class="bar-cell"><div style="display:flex;align-items:center;gap:8px"><div class="minibar" style="flex:1"><i style="width:${(r.relevant / r.coded * 100).toFixed(1)}%"></i></div><span class="num" style="font-size:12px;width:34px;text-align:right">${fPct(r.relevant / r.coded)}</span></div></td></tr>`).join('')
      }<tr><td><b>Total</b></td><td class="r"><b>${fInt(cov.total_frame)}</b></td><td class="r"><b>${fInt(cov.total_coded)}</b></td><td class="r"><b>${fInt(cov.total_relevant)}</b></td><td></td></tr></tbody></table></div>` });
    const ai = D.ai;
    card(host, { id: 'qRel', span: 'span-5', i: 1, title: 'National tone against the San Francisco Fed news index', legend: true,
      desc: 'Both as 3-month means, standardised over 2010–2026. Low monthly reliability comes from about 26 relevant items a month.',
      src: 'results/stage2_reliability/reliability.csv; results/stage2_dictindex/correlations.csv',
      after: `<div class="kpis" style="grid-template-columns:repeat(3,minmax(0,1fr));margin:4px 0 0">
        <div class="kpi"><div class="kpi-lab">Monthly reliability</div><div class="kpi-val">${f(ai.reliability, 2)}</div><div class="kpi-sub">${f(ai.reliability_3m, 2)} as a 3-month mean</div></div>
        <div class="kpi"><div class="kpi-lab">Correlation with SF Fed</div><div class="kpi-val">${f(ai.r_sffed, 2)}</div><div class="kpi-sub">${f(ai.r_sffed_3m, 2)} as 3-month means</div></div>
        <div class="kpi"><div class="kpi-lab">Full-volume dictionary</div><div class="kpi-val">${f(ai.r_sffed_dict_full, 2)}</div><div class="kpi-sub">correlation with SF Fed, all items</div></div></div>` });
    card(host, { id: 'qCov', span: 'span-12', i: 2, title: 'Coded items per month, by source',
      desc: 'Darker cells hold more coded items; hatched cells are months flagged as thin. Blank means the source was not collected for that month.' +
        `<span class="legend" style="margin-top:6px">${[0, 10, 20, 30, 40].map((v, k) => `<span class="lg">${keySwatch('band', `var(--seq-${k})`)}${v}${k === 4 ? '+' : ''}</span>`).join('')}<span class="lg">${keySwatch('band', 'repeating-linear-gradient(45deg, var(--faint) 0 1px, var(--surface-2) 1px 4px)')}Thin month</span></span>`,
      src: 'features/media_monthly.csv' });
    card(host, { id: 'qAI', span: 'span-7', i: 3, title: 'Agreement with the human gold standard', legend: true,
      desc: `Cohen’s κ on the ${ai.test_n}-item test set, scored once after the prompt was frozen on the development set. Relevance uses items whose gold label is yes or no; the other dimensions use items both the gold standard and the LLM judge relevant.`,
      src: 'results/ai_validation/codex__v2_isolated_r1_test_metrics.csv; labels/agreement_summary.csv; results/stage2_r35/item_metrics.csv' });
    card(host, { id: 'qSwap', span: 'span-5', i: 4, title: 'Name and outlet swap test',
      desc: 'Excess flip rate: how much more often a label changes when names, parties or the outlet label are swapped than when the same text is simply coded again. Bars are 95% intervals.',
      src: 'results/stage2_r37/flip_rates.csv' });
    const relC = new TimeChart(document.getElementById('qRelC'), {
      height: 190, m: { t: 8, r: 52, b: 22, l: 30 }, yTicks: 4, aria: 'National tone and SF Fed index',
      frame() {
        return { x: [TMS[0], TMS[N - 1]], y: [-3.2, 2.6], shades: [], ann: [{ key: 'z', type: 'hline', y: 0 }],
          layers: [{ key: 'sf', kind: 'line', v: zscore(trailing(D.sffed)), color: 'var(--c-sffed)', cls: 'thin', end: 'SF Fed' },
            { key: 'nt', kind: 'line', v: zscore(trailing(D.media.national.net_tone)), color: 'var(--c-national)', cls: 'thin', end: 'LLM' }] };
      },
      readout(i) {
        RO('qRel', `<span class="m">${mLab(M[i])}</span><span>LLM <b>${f(zscore(trailing(D.media.national.net_tone))[i], 2)}</b></span><span>SF Fed <b>${f(zscore(trailing(D.sffed))[i], 2)}</b></span>`);
      },
    });
    relC.update(false);
    document.getElementById('qRelL').innerHTML = [legendItem('nt', 'var(--c-national)', 'LLM national net tone'), legendItem('sf', 'var(--c-sffed)', 'SF Fed daily news sentiment')].join('');
    wireLegend('qRelL', relC);
    drawCoverage();
    drawAgreement();
    drawSwap();
  }
  function drawCoverage() {
    const el = document.getElementById('qCovC');
    const draw = () => {
      const w = el.clientWidth || 900;
      const m = { t: 4, r: 8, b: 22, l: Math.min(150, w * 0.26) }, rh = 18;
      const H = GROUP_ORDER.length * rh + m.t + m.b;
      const svg = d3.select(el).selectAll('svg').data([0]).join('svg').attr('width', w).attr('height', H)
        .attr('role', 'img').attr('aria-label', 'Coded items per month by source');
      const x = d3.scaleTime().domain([T[0], d3.timeMonth.offset(T[N - 1], 1)]).range([m.l, w - m.r]);
      const bw = (w - m.l - m.r) / N;
      const col = d3.scaleLinear().domain([0, 10, 20, 30, 40]).range(['--seq-0', '--seq-1', '--seq-2', '--seq-3', '--seq-4'].map(css)).clamp(true);
      const cells = [];
      GROUP_ORDER.forEach((g, r) => D.media[g].n_coded.forEach((v, i) => { if (isNum(v)) cells.push({ g, r, i, v, thin: D.media[g].low_n[i], note: D.media[g].note[i] }); }));
      svg.selectAll('g.cells').data([0]).join('g').attr('class', 'cells').selectAll('rect').data(cells, d => d.g + d.i).join('rect').attr('class', 'cell')
        .attr('x', d => x(T[d.i])).attr('y', d => m.t + d.r * rh).attr('width', bw + 0.3).attr('height', rh - 2)
        .style('fill', d => col(d.v))
        .on('pointerenter', (e, d) => showTip(`<b>${esc(D.media[d.g].label)}, ${esc(mLab(M[d.i]))}</b><br>${d.v} coded, ${D.media[d.g].n_relevant[d.i]} relevant${d.thin ? '<br>Thin month' : ''}${d.note ? '<br>' + esc(d.note) : ''}`, e))
        .on('pointerleave', hideTip);
      svg.selectAll('g.thin').data([0]).join('g').attr('class', 'thin').style('pointer-events', 'none').selectAll('rect').data(cells.filter(c => c.thin || c.note), d => d.g + d.i).join('rect')
        .attr('x', d => x(T[d.i])).attr('y', d => m.t + d.r * rh).attr('width', bw + 0.3).attr('height', rh - 2).style('fill', 'url(#hatch)');
      svg.selectAll('g.yl').data([0]).join('g').attr('class', 'axis yl').selectAll('text').data(GROUP_ORDER).join('text')
        .attr('x', m.l - 8).attr('y', (d, r) => m.t + r * rh + rh / 2 + 2.5).attr('text-anchor', 'end').text(g => D.media[g].label);
      svg.selectAll('g.xa').data([0]).join('g').attr('class', 'axis x xa').attr('transform', `translate(0,${m.t + GROUP_ORDER.length * rh})`)
        .call(d3.axisBottom(x).ticks(d3.timeYear.every(w < 700 ? 4 : 2)).tickSize(3).tickFormat(d3.timeFormat('%Y')));
    };
    draw();
    new ResizeObserver(() => { if (el.clientWidth) draw(); }).observe(el);
  }
  function drawAgreement() {
    const el = document.getElementById('qAIC');
    const ai = D.ai;
    const rows = ai.dims.concat([{ dim: 'topics', label: 'Topics (mean of 13)', llm: ai.topics.llm, human: null, baselines: Object.fromEntries(Object.entries(ai.topics).filter(([k]) => k !== 'llm')), n: ai.dims[1].n }]);
    document.getElementById('qAIL').innerHTML = [legendItem('l', 'var(--ink)', 'LLM (frozen prompt)', 'dot'), legendItem('h', 'var(--ink)', 'Two human annotators', 'ring'),
      legendItem('b', 'var(--faint)', 'Low-cost baselines (dictionaries, keywords, TF-IDF)', 'dot')].join('');
    const draw = () => {
      const w = el.clientWidth || 600;
      const m = { t: 18, r: 14, b: 24, l: Math.min(170, w * 0.34) }, rh = 21;
      const H = rows.length * rh + m.t + m.b;
      const x = d3.scaleLinear().domain([0, 1]).range([m.l, w - m.r]);
      const svg = d3.select(el).selectAll('svg').data([0]).join('svg').attr('width', w).attr('height', H).attr('role', 'img').attr('aria-label', 'Kappa by dimension');
      svg.selectAll('g.xa').data([0]).join('g').attr('class', 'axis x xa').attr('transform', `translate(0,${H - m.b})`)
        .call(d3.axisBottom(x).tickValues([0, 0.2, 0.4, 0.6, 0.8, 1]).tickSize(-(H - m.b - m.t)).tickFormat(d3.format('.1f')))
        .call(g => g.selectAll('line').style('stroke', d => (d === 0.6 || d === 0.8 ? 'var(--axis)' : 'var(--grid)')));
      const roomy = x(0.8) - x(0.6) > 100;
      svg.selectAll('text.bandlab').data([[0.6, 'substantial'], [0.8, 'almost perfect']]).join('text').attr('class', 'ann bandlab')
        .attr('x', d => x(d[0]) + 3).attr('y', m.t - 6).text(d => (roomy ? d[1] + ' →' : '≥ ' + d[0].toFixed(1)));
      const g = svg.selectAll('g.rows').data([0]).join('g').attr('class', 'rows').selectAll('g.r').data(rows, d => d.dim).join(en => {
        const e = en.append('g').attr('class', 'r');
        e.append('rect').attr('class', 'hit');
        e.append('text').attr('class', 'ann lab');
        e.append('line').attr('class', 'conn');
        e.append('g').attr('class', 'bases');
        e.append('circle').attr('class', 'hum');
        e.append('circle').attr('class', 'llm');
        return e;
      });
      const cy = (d, k) => m.t + k * rh + rh / 2;
      g.attr('transform', (d, k) => `translate(0,${cy(d, k)})`);
      g.select('rect.hit').attr('x', 0).attr('y', -rh / 2).attr('width', w).attr('height', rh).style('fill', 'transparent');
      g.select('text.lab').attr('x', m.l - 8).attr('y', 3.5).attr('text-anchor', 'end').text(d => d.label);
      g.select('line.conn').attr('x1', d => x(d.llm)).attr('x2', d => x(isNum(d.human) ? d.human : d.llm)).style('stroke', 'var(--axis)').style('stroke-width', 1.4);
      g.select('g.bases').selectAll('rect').data(d => Object.values(d.baselines || {}).filter(isNum)).join('rect')
        .attr('x', v => x(Math.max(0, v)) - 1).attr('y', -5).attr('width', 2).attr('height', 10).style('fill', 'var(--faint)');
      g.select('circle.hum').attr('cx', d => x(isNum(d.human) ? d.human : 0)).attr('r', 4.5).style('display', d => (isNum(d.human) ? null : 'none'))
        .style('fill', 'var(--surface)').style('stroke', 'var(--ink)').style('stroke-width', 1.5);
      g.select('circle.llm').attr('cx', d => x(d.llm)).attr('r', 4.5).style('fill', 'var(--ink)');
      g.on('pointerenter', (e, d) => showTip(`<b>${esc(d.label)}</b> (n = ${d.n})<br>LLM κ ${f(d.llm, 2)}${d.llm_ci ? ` [${f(d.llm_ci[0], 2)}, ${f(d.llm_ci[1], 2)}]` : ''}` +
        (isNum(d.human) ? `<br>Human A vs B κ ${f(d.human, 2)}` : '') + (isNum(d.f1) ? `<br>LLM macro F1 ${f(d.f1, 2)}` : '') +
        (isNum(d.self_consistency) ? `<br>Same label on re-run: ${fPct(d.self_consistency)} of ${ai.repeat_items}` : '') +
        Object.entries(d.baselines || {}).map(([k, v]) => `<br>${esc(k)} κ ${f(v, 2)}`).join(''), e)).on('pointerleave', hideTip);
    };
    draw();
    new ResizeObserver(() => { if (el.clientWidth) draw(); }).observe(el);
  }
  function drawSwap() {
    const el = document.getElementById('qSwapC');
    const sw = D.ai.swap;
    const versions = [...new Set(sw.map(s => s.version))];
    const dims = [...new Set(sw.map(s => s.dim))];
    const draw = () => {
      const w = el.clientWidth || 480;
      const m = { t: 30, r: 8, b: 22, l: Math.min(150, w * 0.36) }, rh = 17, gap = 10;
      const pw = (w - m.l - m.r - gap * (versions.length - 1)) / versions.length;
      const H = dims.length * rh + m.t + m.b;
      const svg = d3.select(el).selectAll('svg').data([0]).join('svg').attr('width', w).attr('height', H).attr('role', 'img').attr('aria-label', 'Excess flip rates');
      const x = d3.scaleLinear().domain([-0.2, 0.2]).range([0, pw]);
      svg.selectAll('text.yl').data(dims).join('text').attr('class', 'ann yl').attr('x', m.l - 8)
        .attr('y', (d, k) => m.t + k * rh + rh / 2 + 3.5).attr('text-anchor', 'end').text(d => sw.find(s => s.dim === d).label.replace(' to administration', w < 560 ? '' : ' to administration'));
      const panels = svg.selectAll('g.p').data(versions).join(en => {
        const e = en.append('g').attr('class', 'p');
        e.append('text').attr('class', 'ann ttl');
        e.append('g').attr('class', 'axis x xa');
        e.append('line').attr('class', 'zero z');
        e.append('g').attr('class', 'pts');
        return e;
      }).attr('transform', (d, k) => `translate(${m.l + k * (pw + gap)},0)`);
      panels.select('text.ttl').attr('x', pw / 2).attr('y', 12).attr('text-anchor', 'middle').text(d => d.replace('Names and parties swapped', 'Names swapped').replace('Labelled as ', ''));
      panels.select('g.xa').attr('transform', `translate(0,${H - m.b})`).call(d3.axisBottom(x).tickValues(pw < 90 ? [-0.1, 0.1] : [-0.1, 0, 0.1]).tickSize(-(H - m.b - m.t + 6)).tickFormat(v => (v * 100).toFixed(0)))
        .call(g => g.selectAll('line').style('stroke', 'var(--grid)'));
      panels.select('line.z').attr('x1', x(0)).attr('x2', x(0)).attr('y1', m.t - 6).attr('y2', H - m.b);
      panels.select('g.pts').each(function (v) {
        const d = sw.filter(s => s.version === v);
        const g = d3.select(this).selectAll('g').data(d, s => s.dim).join(en => { const e = en.append('g'); e.append('line'); e.append('circle'); return e; })
          .attr('transform', s => `translate(0,${m.t + dims.indexOf(s.dim) * rh + rh / 2})`);
        g.select('line').attr('x1', s => x(Math.max(-0.2, s.lo))).attr('x2', s => x(Math.min(0.2, s.hi))).style('stroke', 'var(--ink-2)').style('stroke-width', 1.4);
        g.select('circle').attr('cx', s => x(s.excess)).attr('r', 3.2).style('fill', s => (s.p < 0.05 ? 'var(--c-bad)' : 'var(--ink)'));
        g.on('pointerenter', (e, s) => showTip(`<b>${esc(s.label)}</b>, ${esc(s.version.toLowerCase())}<br>Excess flip ${f(s.excess * 100, 1, true)} pp [${f(s.lo * 100, 1, true)}, ${f(s.hi * 100, 1, true)}]<br>Re-run flip rate ${fPct(s.base, 1)} · one-sided ${fPeq(s.p)}`, e)).on('pointerleave', hideTip);
      });
      svg.selectAll('text.xl').data([0]).join('text').attr('class', 'ann xl').attr('x', w - m.r).attr('y', H - 1).attr('text-anchor', 'end').text('percentage points');
    };
    draw();
    new ResizeObserver(() => { if (el.clientWidth) draw(); }).observe(el);
  }

  // ------------------------------------------------------------------ tests
  function buildTests() {
    const host = document.getElementById('testsGrid');
    card(host, { id: 'tSpec', span: 'span-7', i: 0, title: 'Does lagged news tone improve one-month forecasts?', legend: true,
      desc: 'Clark–West test p-values, out of sample 2017–2026, for the main specification and 19 variants. Left of the line is significant at 5%.',
      src: 'results/stage3_robustness/variants.csv' });
    card(host, { id: 'tLP', span: 'span-5', i: 1, title: 'Which moves first, tone or sentiment?', legend: true,
      desc: 'Local projections: response over the next 0–6 months to a one-standard-deviation change, with 95% intervals. “Avg” is the 0–6 average used for the pre-registered test.',
      src: 'results/stage4_timing/local_projections.csv' });
    const fdiv = document.createElement('div');
    fdiv.className = 'card span-12';
    fdiv.style.setProperty('--i', 2);
    const F = D.falsification;
    fdiv.innerHTML = `<div class="card-head"><div><div class="card-title">Pre-registered falsification criteria for the media-bias explanation</div>
      <div class="card-desc">Criteria and decision rules were fixed before estimation. ${F.filter(x => x.triggered).length} of ${F.length} are triggered.</div></div></div>
      <div class="fals">${F.map(x => `<div class="fcard ${x.triggered ? 'trig' : ''}"><div class="fn"><span>Criterion ${x.n}</span><span class="tag ${x.triggered ? 'solid' : ''}">${x.triggered ? 'Triggered' : 'Not triggered'}</span></div>
        <div class="fc">${esc(x.criterion)}</div><div class="fr">${esc(x.result)}</div><div class="fr" style="color:var(--muted)">${esc(x.verdict)}</div></div>`).join('')}</div>
      <p class="src">Source: <code>results/FINDINGS_stage4.md</code>, section 2; numbers from <code>results/stage3_robustness/variants.csv</code>, <code>results/stage4_timing/</code>, <code>results/stage1_h3/</code>, <code>results/stage2_r37/flip_rates.csv</code></p>`;
    host.appendChild(fdiv);
    drawSpec();
    drawLP();
  }
  function drawSpec() {
    const el = document.getElementById('tSpecC');
    const specs = D.forecast.specs;
    document.getElementById('tSpecL').innerHTML = [legendItem('a', 'var(--c-model)', 'Tone added to the three fundamentals (M2 vs M1)', 'ring'),
      legendItem('b', 'var(--c-gap)', 'Tone added after household and political controls (M3 vs M1c)', 'dot')].join('');
    const draw = () => {
      const w = el.clientWidth || 600;
      const m = { t: 20, r: 14, b: 26, l: Math.min(210, Math.max(150, w * 0.4)) }, rh = 17;
      const H = specs.length * rh + m.t + m.b;
      const x = d3.scaleLog().domain([0.0005, 1]).range([m.l, w - m.r]).clamp(true);
      const svg = d3.select(el).selectAll('svg').data([0]).join('svg').attr('width', w).attr('height', H).attr('role', 'img').attr('aria-label', 'Specification curve');
      svg.selectAll('rect.sig').data([0]).join('rect').attr('class', 'sig shade-rect').attr('x', m.l).attr('y', m.t).attr('width', Math.max(0, x(0.05) - m.l)).attr('height', H - m.t - m.b);
      svg.selectAll('text.sigl').data([0]).join('text').attr('class', 'ann sigl').attr('x', x(0.05) - 4).attr('y', m.t - 7).attr('text-anchor', 'end').text('← significant at 5%');
      svg.selectAll('g.xa').data([0]).join('g').attr('class', 'axis x xa').attr('transform', `translate(0,${H - m.b})`)
        .call(d3.axisBottom(x).tickValues(w < 560 ? [0.001, 0.01, 0.05, 0.5] : [0.001, 0.01, 0.05, 0.1, 0.5, 1]).tickSize(-(H - m.b - m.t)).tickFormat(d3.format('~g')))
        .call(g => g.selectAll('line').style('stroke', d => (d === 0.05 ? 'var(--ink)' : 'var(--grid)')));
      const g = svg.selectAll('g.r').data(specs, d => d.key).join(en => {
        const e = en.append('g').attr('class', 'r');
        e.append('rect').attr('class', 'hit');
        e.append('text').attr('class', 'ann');
        e.append('line');
        e.append('circle').attr('class', 'a');
        e.append('circle').attr('class', 'b');
        return e;
      }).attr('transform', (d, k) => `translate(0,${m.t + k * rh + rh / 2})`);
      g.select('rect.hit').attr('x', 0).attr('y', -rh / 2).attr('width', w).attr('height', rh).style('fill', 'transparent');
      g.select('text').attr('x', m.l - 8).attr('y', 3.5).attr('text-anchor', 'end').style('font-weight', d => (d.key === 'main' ? 600 : null))
        .style('fill', d => (d.key === 'main' ? 'var(--ink)' : null)).text(d => d.label);
      g.select('line').attr('x1', d => x(d.p_m2)).attr('x2', d => x(d.p_m3)).style('stroke', 'var(--axis)');
      g.select('circle.a').attr('cx', d => x(d.p_m2)).attr('r', 4).style('fill', 'var(--surface)').style('stroke', 'var(--c-model)').style('stroke-width', 1.6);
      g.select('circle.b').attr('cx', d => x(d.p_m3)).attr('r', 4).style('fill', 'var(--c-gap)');
      g.on('pointerenter', (e, d) => showTip(`<b>${esc(d.label)}</b><br>M2 vs M1: ${fPeq(d.p_m2)}, RMSE ratio ${f(d.ratio_m2, 3)}<br>M3 vs M1c: ${fPeq(d.p_m3)}, RMSE ratio ${f(d.ratio_m3, 3)}`, e)).on('pointerleave', hideTip);
    };
    draw();
    new ResizeObserver(() => { if (el.clientWidth) draw(); }).observe(el);
  }
  function drawLP() {
    const el = document.getElementById('tLPC');
    el.classList.add('fill');
    el.style.setProperty('--minh', '230px');
    const lp = D.forecast.lp;
    document.getElementById('tLPL').innerHTML = [legendItem('f', 'var(--c-national)', 'Tone → later sentiment', 'line'), legendItem('r', 'var(--c-actual)', 'Sentiment → later tone', 'line')].join('');
    const draw = () => {
      const w = el.clientWidth || 420;
      const H = Math.max(230, el.clientHeight), m = { t: 18, r: 10, b: 24, l: 40 }, gap = 52;
      const pw = (w - m.l - m.r - gap) / 2;
      const svg = d3.select(el).selectAll('svg').data([0]).join('svg').attr('width', w).attr('height', H).attr('role', 'img').attr('aria-label', 'Local projections');
      const dirs = [['forward', 'Tone → sentiment', 'var(--c-national)'], ['reverse', 'Sentiment → tone', 'var(--c-actual)']];
      const panels = svg.selectAll('g.p').data(dirs).join(en => {
        const e = en.append('g').attr('class', 'p');
        e.append('text').attr('class', 'ann ttl');
        e.append('g').attr('class', 'axis y ya');
        e.append('g').attr('class', 'axis x xa');
        e.append('line').attr('class', 'zero z');
        e.append('path').attr('class', 'band');
        e.append('path').attr('class', 'series thin');
        e.append('g').attr('class', 'pts');
        e.append('g').attr('class', 'avg');
        return e;
      }).attr('transform', (d, k) => `translate(${m.l + k * (pw + gap)},0)`);
      panels.each(function ([dir, title, color]) {
        const d = lp.filter(r => r.dir === dir);
        const hz = d.filter(r => !r.h.startsWith('avg')).map(r => ({ ...r, h: +r.h }));
        const av = d.find(r => r.h.startsWith('avg'));
        const lo = r => r.coef - 1.96 * r.se, hi = r => r.coef + 1.96 * r.se;
        const ext = d3.extent(d.flatMap(r => [lo(r), hi(r)]));
        const x = d3.scaleLinear().domain([0, 7.8]).range([0, pw]);
        const y = d3.scaleLinear().domain(ext).nice(4).range([H - m.b, m.t]);
        const p = d3.select(this);
        p.select('text.ttl').attr('x', 0).attr('y', 10).text(title);
        p.select('g.ya').call(d3.axisLeft(y).ticks(4).tickSize(-pw).tickFormat(v => f(v, 2))).call(g => g.selectAll('line').style('stroke', 'var(--grid)'));
        p.select('g.xa').attr('transform', `translate(0,${H - m.b})`).call(d3.axisBottom(x).tickValues([0, 1, 2, 3, 4, 5, 6, 7.4]).tickSize(3)
          .tickFormat(v => (v > 7 ? 'Avg' : v)));
        p.select('line.z').attr('x1', 0).attr('x2', pw).attr('y1', y(0)).attr('y2', y(0));
        p.select('path.band').style('fill', color).style('opacity', 0.14).attr('d', d3.area().x(r => x(r.h)).y0(r => y(lo(r))).y1(r => y(hi(r)))(hz));
        p.select('path.series').style('stroke', color).attr('d', d3.line().x(r => x(r.h)).y(r => y(r.coef))(hz));
        p.select('g.pts').selectAll('circle').data(hz).join('circle').attr('cx', r => x(r.h)).attr('cy', r => y(r.coef)).attr('r', 3).style('fill', color)
          .on('pointerenter', (e, r) => showTip(`<b>Horizon ${r.h}</b><br>${f(r.coef, 3)} (se ${f(r.se, 3)})<br>two-sided ${fPeq(r.p)}`, e)).on('pointerleave', hideTip);
        const ag = p.select('g.avg');
        ag.selectAll('line').data([av]).join('line').attr('x1', x(7.4)).attr('x2', x(7.4)).attr('y1', r => y(lo(r))).attr('y2', r => y(hi(r))).style('stroke', color).style('stroke-width', 1.6);
        ag.selectAll('rect').data([av]).join('rect').attr('x', x(7.4) - 4).attr('y', r => y(r.coef) - 4).attr('width', 8).attr('height', 8).style('fill', color)
          .on('pointerenter', (e, r) => showTip(`<b>Average over 0–6</b><br>${f(r.coef, 3)} (se ${f(r.se, 3)})<br>one-sided ${fPeq(r.p1)}`, e)).on('pointerleave', hideTip);
      });
    };
    draw();
    new ResizeObserver(() => { if (el.clientWidth) draw(); }).observe(el);
  }

  // ------------------------------------------------------------------ update plan
  function buildUpdate() {
    const host = document.getElementById('updateGrid');
    const today = d3.timeDay.floor(new Date());
    const cut = parseD(meta.cutoff), el = parseD(meta.election);
    const rel = D.releases.map(r => ({ ...r, d: parseD(r.date) }));
    const marks = [{ d: cut, marker: 'Data cutoff for this build' }, { d: el, marker: 'Election Day' }];
    if (today >= parseD('2026-10-01') && today <= parseD('2026-12-31')) marks.push({ d: today, marker: 'Today' });
    const all = rel.concat(marks).sort((a, b) => a.d - b.d || (a.marker ? -1 : 1));
    const items = all.map(r => {
      if (r.marker) return `<div class="rel marker"><span class="d">${esc(d3.timeFormat('%b %-d')(r.d))}</span><span class="l"><b>${esc(r.marker)}</b></span><span></span></div>`;
      const status = r.d <= cut ? 'In this build' : r.d < today ? 'Released, not yet added' : 'Scheduled';
      const ref = r.ref ? (r.ref.length === 7 ? mLab(r.ref) : r.ref) : '';
      return `<div class="rel ${r.d <= cut ? 'past' : ''}"><span class="d">${esc(d3.timeFormat('%b %-d')(r.d))}</span>
        <span class="l"><a href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.label)}</a>${ref || r.kind ? ` <span class="w">${esc([ref, r.kind].filter(Boolean).join(', '))}</span>` : ''}<br><span class="w">${esc(r.agency)}</span></span>
        <span class="tag">${status}</span></div>`;
    }).join('');
    card(host, { id: 'uRel', span: 'span-7', i: 0, title: 'Release calendar, October to December 2026',
      desc: 'Scheduled dates from the agencies’ calendars as recorded at collection. Status is computed against the data cutoff and today’s date.',
      src: 'provenance/release_calendar.csv', after: `<div class="rel-list">${items}</div>` });
    const steps = [
      ['Pull the new releases', 'Run the collection scripts on your own machine, where the API keys live. FRED and ALFRED are not reachable from the cloud environment.', 'python3 src/collect/macro.py   # and survey.py, news archives'],
      ['Rebuild the processed data', 'Rebuilds the real-time panel, corpus and monthly media measures from the raw files without network requests.', 'sh src/process/run_all.sh'],
      ['Code new news items with the frozen prompt', `Use ${meta.prompt.replace('.md', '')} unchanged with the same model and settings, in an isolated folder that holds only the prompt and the inputs, then import the labels.`, null],
      ['Re-run the frozen analysis', 'Same specifications as the registry. New months are reported as observations after the cutoff, not used to re-tune anything.', 'sh src/analysis/run_research.sh'],
      ['Rebuild this dashboard', 'Writes a new single-file page with the updated data vintage in the header.', 'python3 src/dashboard/build.py'],
    ];
    card(host, { id: 'uSteps', span: 'span-5', i: 1, title: 'How to update', desc: 'Each step reads only the outputs of the step before it.',
      after: `<ol class="steps">${steps.map(([t, p, c]) => `<li><div><b>${esc(t)}</b><p>${esc(p)}</p>${c ? `<code class="cmd">${esc(c)}</code>` : ''}</div></li>`).join('')}</ol>
        <p class="note" style="margin-top:6px"><b>Post-election review.</b> After the November and December Michigan readings, compare the gap and the news measures with the months before the election and with the same months in 2010, 2014, 2018 and 2022. A change around Election Day cannot be attributed to the election alone; tariffs, prices, interest rates and the end of the 2025 shutdown overlap with it.</p>` });
  }

  // ------------------------------------------------------------------ footer, nav, theme
  function buildFoot() {
    document.getElementById('foot').innerHTML = `
      <div><h4>Project</h4><p>AI, economic perceptions and consumer sentiment ahead of the 2026 midterm elections. Final project, AI Applications in Finance.</p>
        <p>Repository: <span class="mono">${esc(meta.repo)}</span></p><p>Built from frozen results with <code>src/dashboard/build.py</code>; opens offline.</p></div>
      <div><h4>Sources</h4><p>University of Michigan Surveys of Consumers; ALFRED real-time vintages (BLS, BEA); NYT Archive API; Guardian Open Platform; Media Cloud; Reddit via Arctic Shift; YouTube Data API; San Francisco Fed Daily News Sentiment; Federal Reserve, OPM, USTR and House records for events.</p></div>
      <div><h4>Reading this page</h4><p>Results are associations in observational data. The page does not claim that news coverage causes changes in sentiment.</p>
        <p>Reddit and YouTube content appears only as counts and averages. Headlines link to the publishers. D3 v7.9.0, ISC License.</p></div>`;
  }
  // ------------------------------------------------------------------ overview tab
  function buildOverviewTab() {
    const host = document.getElementById('overviewGrid');
    card(host, { id: 'oChart', span: 'span-12', i: 0, title: 'Michigan sentiment and what the fundamentals predict', legend: true,
      key: 'The shaded area is the gap: since mid-2021 sentiment has stayed far below what unemployment, inflation and growth predict.',
      desc: 'Model fit on 2010–2019 with data as published before each survey month. Grey band: pandemic months, where the model is not applied. Hover to read a month; click to open it.',
      src: 'results/stage1_m1/m1_gap_monthly.csv' });
    document.getElementById('oChartL').innerHTML = [legendItem('act', 'var(--c-actual)', 'Michigan ICS'), legendItem('pred', 'var(--c-model)', 'Model'),
      legendItem('fit', 'var(--c-model)', 'Model, 2010–19 fit', 'dash'), legendItem('gapfill', 'var(--c-gap-band)', 'Gap', 'band'), legendItem('', 'var(--shade)', PAND_NOTE, 'shade')].join('');
    const c = D.conf.ics, cs = confSeries('ics');
    const oos = i => isNum(cs.pred[i]);
    const ch = new TimeChart(document.getElementById('oChartC'), {
      height: 340, m: { t: 12, r: 64, b: 22, l: 36 }, yTicks: 5, aria: 'Michigan sentiment index and the fundamentals model',
      frame: () => ({ x: [TMS[0], TMS[N - 1]], y: [35, 115],
        shades: [PAND_SHADE],
        layers: [
          { key: 'gapfill', kind: 'band', lo: c.actual.map((v, i) => (oos(i) ? v : null)), hi: c.pred.map((v, i) => (oos(i) ? v : null)), color: 'var(--c-gap-band)' },
          { key: 'fit', kind: 'line', v: cs.fit, color: 'var(--c-model)', cls: 'dash thin', nodot: true },
          { key: 'pred', kind: 'line', v: cs.pred, color: 'var(--c-model)', end: 'Model' },
          { key: 'act', kind: 'line', v: c.actual, color: 'var(--c-actual)', end: 'ICS' }],
        ann: P.filter(p => p.start >= '2025-01').map(p => ({ key: 'g' + p.start, type: 'seg', x0: TMS[idx(p.start)], x1: TMS[idx(p.end)] + 30 * 864e5,
          y: (p.actual + p.pred) / 2, label: f(p.gap, 1) })) }),
      readout(i) {
        RO('oChart', `<span class="m">${mLab(M[i])}</span><span>ICS <b>${f(c.actual[i], 1)}</b></span>` + (isPand(i) ? '<span class="m">pandemic, model not applied</span>'
          : `<span>Model <b>${f(c.pred[i], 1)}</b></span><span>Gap <b>${f(c.gap[i], 1)}</b></span>`));
      },
    });
    ch.update(false);
    wireLegend('oChartL', ch);
    const tone = D.ai.dims.find(d => d.dim === 'tone_overall'), rel = D.ai.dims.find(d => d.dim === 'relevant');
    const toneBase = d3.max(Object.values(tone.baselines).filter(isNum));
    const T4 = [
      ['findings', 'The gap', `${f(P25.gap, 1)} / ${f(P26.gap, 1)}`, 'Sentiment is far below what fundamentals predict',
        `Average gap in 2025 and in 2026 so far, in index points. The three fundamentals explain only ${fPct(Math.min(P25.explained, P26.explained))}–${fPct(Math.max(P25.explained, P26.explained))} of the fall since 2019.`, 'See the five steps'],
      ['sentiment', 'Survey and party', `≤ ${f(D.party.composition_max, 1)}`, 'Survey mode and party mix account for little',
        `Party composition moves the index by at most ${f(D.party.composition_max, 1)} points. The web-survey switch is associated with ${f(ME.ics.coef, 1)} points in the headline index (${fPeq(ME.ics.p)}).`, 'Explore sentiment'],
      ['tests', 'News tone', fPeq(mainSpec.p_m3), 'News tone adds no forecasting power after controls',
        `${nSig3} of ${fc.specs.length} specifications are significant once household and political controls are included; at most about ${fPct(fc.tone_share_max)} of the 2025–26 gap is associated with tone.`, 'See the tests'],
      ['measurement', 'AI measurement', `κ ${f(tone.llm, 2)}`, 'LLM coding is close to human agreement',
        `Tone: ${f(tone.llm, 2)} against the gold standard versus ${f(tone.human, 2)} between two humans (relevance ${f(rel.llm, 2)} vs ${f(rel.human, 2)}). Dictionary and keyword methods reach at most ${f(toneBase, 2)} on tone.`, 'Check the measures'],
    ];
    document.getElementById('takeaways').innerHTML = T4.map(([t, n, v, tt, tb, tl], k) => `<a class="take" href="#${t}" style="--i:${k}">
      <span class="tn">${String(k + 1).padStart(2, '0')} · ${esc(n)}</span><span class="tv">${esc(v)}</span><span class="tt">${esc(tt)}</span><span class="tb">${esc(tb)}</span><span class="tl">${esc(tl)} →</span></a>`).join('');
  }

  // ------------------------------------------------------------------ tab heads: what to look at
  const HEADS = {};
  function buildHeads() {
    const F = D.falsification, trig = F.filter(x => x.triggered);
    const tone = D.ai.dims.find(d => d.dim === 'tone_overall'), rel = D.ai.dims.find(d => d.dim === 'relevant');
    const swapSig = D.ai.swap.filter(x => x.p < 0.05).length;
    const c95 = D.conf.ics, k0 = idx('2021-07');
    let nOos = 0, nBelow = 0;
    for (let i = k0; i < N; i++) if (isNum(c95.pi95lo[i]) && isNum(c95.actual[i])) { nOos++; if (c95.actual[i] < c95.pi95lo[i]) nBelow++; }
    const cut = parseD(meta.cutoff), el = parseD(meta.election);
    const before = D.releases.filter(r => parseD(r.date) > cut && parseD(r.date) < el);
    const afterMich = D.releases.find(r => parseD(r.date) > el && /Michigan/.test(r.label));
    const head = (eyebrow, h2, key, sub) => `<p class="eyebrow">${eyebrow}</p><h2>${h2}</h2><p class="keypoint">${key}</p>${sub ? `<p class="sec-sub">${sub}</p>` : ''}`;
    HEADS.findings = head('Findings', 'How the gap was tested',
      '<b>The point:</b> the gap is large, persistent and shared by every demographic group, and none of the explanations tested here (survey mode, party mix, news tone) accounts for more than a small part of it.',
      'Five steps. Use the buttons, or the ← and → keys.');
    HEADS.sentiment = head('Sentiment', 'Sentiment against the fundamentals model, month by month',
      `<b>Look at:</b> the black line against the blue band. Since July 2021 the headline index has been below the 95% band in ${nBelow} of ${nOos} months, and all three partisan groups sit below their own 2017–19 levels.`,
      'Drag across the strip to choose a period; every chart and number below follows it. Hover to compare panels at one month, click to open the month.');
    HEADS.news = head('News', 'What the news said: tone, blame, topics and quoted numbers',
      '<b>Look at:</b> tone and blame. Coverage became more negative and more critical of the administration after January 2025, but tone adds no forecasting power once household and political conditions are controlled for (see Tests).',
      'Drag across the strip to choose a period; every chart and number below follows it. Hover to compare panels at one month, click to open the month and its headlines.');
    HEADS.measurement = head('Measurement', 'How far to trust the AI-coded measures',
      `<b>The point:</b> the LLM agrees with the human gold standard about as well as two humans agree with each other (tone κ ${f(tone.llm, 2)} vs ${f(tone.human, 2)}; relevance ${f(rel.llm, 2)} vs ${f(rel.human, 2)}), and no label shifts significantly when names, parties or outlets are swapped (${swapSig} of ${D.ai.swap.length}). Monthly series are noisy, so 3-month means are used.`);
    HEADS.tests = head('Tests', 'Forecast comparisons and pre-registered falsification',
      `<b>The point:</b> ${trig.length} of ${F.length} pre-registered criteria are triggered (${trig.map(x => `${x.n}: ${x.criterion.toLowerCase()}`).join('; ')}). These count against news coverage as the explanation for the gap.`);
    HEADS.update = head('Update plan', 'Releases between the data cutoff and the end of the year',
      `<b>Before Election Day:</b> ${before.map(r => `${esc(r.label.replace(/ \(.*\)/, ''))} on ${dShort(r.date)}`).join(', ')}. ` +
      (afterMich ? `<b>First Michigan reading after it:</b> ${dShort(afterMich.date)}. ` : '') + 'Changes around the election cannot be attributed to the election alone.');
    ['findings', 'measurement', 'tests', 'update'].forEach(t => {
      document.getElementById('head' + t[0].toUpperCase() + t.slice(1)).innerHTML = HEADS[t];
    });
  }

  // ------------------------------------------------------------------ tabs
  const TABS = ['overview', 'findings', 'sentiment', 'news', 'measurement', 'tests', 'update'];
  let curTab = null;
  function setTab(t) {
    if (!TABS.includes(t)) t = 'overview';
    if (t === curTab) return;
    const wasEx = curTab === 'sentiment' || curTab === 'news';
    curTab = t;
    const ex = t === 'sentiment' || t === 'news';
    const exEl = document.getElementById('explorer');
    exEl.hidden = !ex;
    TABS.forEach(k => { document.getElementById(k).hidden = k !== t; });
    const anim = ex && !wasEx ? exEl : document.getElementById(t);
    anim.classList.remove('enter');
    void anim.offsetWidth;
    anim.classList.add('enter');
    if (ex) document.getElementById('headExplorer').innerHTML = HEADS[t];
    document.querySelectorAll('.nav a').forEach(a => {
      const on = a.getAttribute('href') === '#' + t;
      a.classList.toggle('on', on);
      a.setAttribute('aria-selected', on);
      if (on && a.scrollIntoView) a.scrollIntoView({ block: 'nearest', inline: 'nearest' });
    });
    try { history.replaceState(null, '', '#' + t); } catch (e) { /* history unavailable */ }
    hideTip();
    setHover(null);
    window.scrollTo({ top: 0, behavior: 'instant' });
  }
  function wireTabs() {
    document.addEventListener('click', ev => {
      const a = ev.target.closest && ev.target.closest('a[href^="#"]');
      if (!a) return;
      const t = a.getAttribute('href').slice(1);
      if (TABS.includes(t)) { ev.preventDefault(); setTab(t); }
    });
    window.addEventListener('hashchange', () => setTab(location.hash.slice(1)));
    document.addEventListener('keydown', ev => {
      if (curTab !== 'findings' || drawer.classList.contains('open')) return;
      if (ev.target.closest && ev.target.closest('input, select, textarea')) return;
      if (ev.key === 'ArrowRight') { ev.preventDefault(); setStep(storyStep + 1); }
      else if (ev.key === 'ArrowLeft') { ev.preventDefault(); setStep(storyStep - 1); }
    });
    setTab(location.hash.slice(1));
  }
  function wireTheme() {
    const btn = document.getElementById('themeBtn');
    const root = document.documentElement;
    try { const t = localStorage.getItem('pgm-theme'); if (t) root.setAttribute('data-theme', t); } catch (e) { /* storage unavailable */ }
    const isDark = () => (root.getAttribute('data-theme') || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')) === 'dark';
    btn.addEventListener('click', () => {
      const t = isDark() ? 'light' : 'dark';
      root.setAttribute('data-theme', t);
      try { localStorage.setItem('pgm-theme', t); } catch (e) { /* storage unavailable */ }
      rethemed();
    });
    matchMedia('(prefers-color-scheme: dark)').addEventListener('change', rethemed);
  }
  function rethemed() {
    renderFramingHeat();
    drawCoverage();
  }

  // ------------------------------------------------------------------ boot
  buildIntro();
  buildOverviewTab();
  buildHeads();
  buildStory();
  buildDock();
  buildKpis();
  buildMonitor();
  buildOverview();
  buildQuality();
  buildTests();
  buildUpdate();
  buildFoot();
  wireTabs();
  wireTheme();
})();
