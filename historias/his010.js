// his010: The Last Bus Always Drops You Off Tomorrow. Planos nuevos: interior del bus nocturno, billete con fecha,
// calendario de la pared, cafeteria de dia (diner) y el conductor en el retrovisor.
import { E, V, registerShot, ease, prog, lerp, seg, circle, rr, poly, glow, alpha, text, FONTS, backdrop, linGrad, rng, noise, wordTime } from '/engine/core.js';
import { drawFigure, POSES, breathe, bigFace } from '/engine/rig2d.js';
import * as FX from '/engine/fx2d.js';
import * as CAST from '../cast.js';

const W = () => E.W, H = () => E.H, CX = () => E.W / 2;
const GOLD = '#ffb24a', CREAM = '#fff0e0', RED = '#ff3b30';
const SC = () => Math.min(E.W, E.H) / 1080;
const popIn = (t, t0) => 0.6 + 0.4 * ease.outBack(prog(t, t0, t0 + 0.3));
function label(g, str, x, y, size, col = CREAM, a = 1, pop = 1) {
  if (a <= 0) return; g.save(); g.translate(x, y); g.scale(pop, pop);
  text(g, str, 0, 0, { size, color: col, font: FONTS.ui, weight: 900, alpha: a, glow: 22, glowColor: alpha(col, 0.55), stroke: size * 0.12, strokeColor: 'rgba(8,3,3,.9)' }); g.restore();
}
function cam2(t, info, amp = 1) { const v = info.v || 0, d = info.dur || 3; const dirs = [[0, 0, 1.0, 1.08], [-60, 0, 1.1, 1.18], [60, -30, 1.15, 1.05], [0, -50, 1.25, 1.12]]; const [x, y, z0, z1] = dirs[v % 4]; const k = ease.inOut(prog(t, 0, d)); return { x: x * k * amp, y: y * k * amp, z: lerp(z0, z1, k) }; }
function withCam(g, cam, fn) { g.save(); g.translate(CX(), H() / 2); g.scale(cam.z, cam.z); g.translate(-CX() + cam.x, -H() / 2 + cam.y); fn(g); g.restore(); }
function hud(g, info) {
  if (!info.day) return; const s = SC(), x = V(70, 60) * s, y = V(70, 140) * s;
  g.save(); rr(g, x - 20 * s, y - 34 * s, 170 * s, 68 * s, 14 * s); g.fillStyle = 'rgba(10,4,4,.55)'; g.fill(); g.strokeStyle = alpha(GOLD, 0.5); g.lineWidth = 2; g.stroke();
  g.textAlign = 'left'; g.font = `900 ${34 * s}px "${FONTS.ui}"`; g.fillStyle = GOLD; g.textBaseline = 'middle'; g.fillText(info.hudTxt ? `${info.hudTxt} ${info.day}` : `DAY ${info.day}`, x, y);
  g.restore();
}
function reg2(id, draw) { registerShot(id, { draw(g, t, info) { draw(g, t, info); hud(g, info); } }); }
const fig = (g, o) => drawFigure(g, { s: 1.6 * SC(), rim: { color: GOLD, dir: [-0.8, -0.5], w: 5 }, ...o });
const P = (n, d = 'stand') => POSES[n] || POSES[d];
const caption = (g, t, info, y = 0.15) => { if (info.caption) label(g, info.caption, CX(), H() * y, 84 * SC(), info.capColor || CREAM, prog(t, 0.15, 0.35), popIn(t, 0.15)); };

// interior del ultimo bus de noche: asientos vacios, luces de la calle pasando por las ventanas
// params: e (gesto), pose (sit, sleepy...), sleep (true: cabeza dormida), empty (true: sin ti)
reg2('busint', (g, t, info) => {
  const s = SC(), cam = cam2(t, info, 0.6), GY = H() * 0.86;
  withCam(g, cam, (g) => {
    backdrop(g, ['#0a0c16', '#121626', '#1a1e30']);
    for (let i = 0; i < 4; i++) {
      const x = W() * (0.06 + i * 0.235), y = H() * 0.18, w = W() * 0.2, h = H() * 0.3;
      g.save(); rr(g, x, y, w, h, 14 * s); g.clip(); g.fillStyle = linGrad(g, 0, y, 0, y + h, ['#05060e', '#141a30']); g.fillRect(x, y, w, h);
      for (let k = 0; k < 3; k++) { const lx = x + w - (((t * 520 + k * 330 + i * 90) % (w + 400)) - 200); glow(g, lx, y + h * 0.5, 90 * s, k % 2 ? '#ffcf8a' : '#8ab0ff', 0.55); }
      FX.rain(g, t, { area: [x, y, w, h], count: 40, color: '#c8d4ff', a: 0.3, len: 24 }); g.restore();
      g.strokeStyle = '#2a3048'; g.lineWidth = 10 * s; rr(g, x, y, w, h, 14 * s); g.stroke();
    }
    seg(g, [[0, H() * 0.12], [W(), H() * 0.12]], 8 * s, '#3a4058');
    for (let i = 0; i < 6; i++) { const x = W() * (0.1 + i * 0.16); seg(g, [[x, H() * 0.12], [x, H() * 0.15]], 3 * s, '#5a6078'); rr(g, x - 14 * s, H() * 0.15, 28 * s, 26 * s, 8 * s); g.strokeStyle = '#5a6078'; g.lineWidth = 4 * s; g.stroke(); }
    g.fillStyle = '#0c0e18'; g.fillRect(-W(), GY, W() * 3, H());
    for (let i = 0; i < 4; i++) { const x = W() * (0.02 + i * 0.26); if (i === 2) continue; rr(g, x, GY - 330 * s, 230 * s, 240 * s, 24 * s); g.fillStyle = '#28324e'; g.fill(); rr(g, x, GY - 110 * s, 260 * s, 70 * s, 16 * s); g.fillStyle = '#323d5e'; g.fill(); }
    rr(g, W() * 0.54, GY - 330 * s, 230 * s, 240 * s, 24 * s); g.fillStyle = '#28324e'; g.fill();
    glow(g, CX(), H() * 0.12, 600 * s, '#cfe0ff', 0.12 + 0.04 * noise(t * 6));
    if (!info.empty) {
      const yo = info.sleep ? 8 * Math.sin(t * 1.4) : 0;
      fig(g, { x: W() * 0.6, y: GY - 40 * s + yo, s: 2.6 * s, facing: 1, outfit: CAST.YOU, pose: breathe(P(info.pose || 'sit', 'sit'), t), expr: info.sleep ? 'sleepy' : (info.e || 'neutral'), rim: { color: '#8ab0ff', dir: [1, -0.4], w: 5 } });
    }
  });
  caption(g, t, info);
});

// billete de papel con fecha (a veces la fecha de manana). params: date, route, stamp ("TOMORROW"), hot (rojo)
reg2('ticket', (g, t, info) => {
  const s = SC(), cam = cam2(t, info, 0.4);
  backdrop(g, ['#0c0a10', '#1a1420', '#241a24']); glow(g, CX(), H() * 0.45, 700 * s, '#ffcf8a', 0.18);
  withCam(g, cam, (g) => {
    const w = 1300 * s, h = 560 * s, z = Math.min(1, W() * 0.92 / (1300 * s)), x = CX() - w / 2, y = H() * 0.48 - h / 2, rot = -0.05 + 0.02 * Math.sin(t * 0.8);
    g.save(); g.translate(CX(), H() * 0.48); g.rotate(rot); g.scale(z, z); g.translate(-CX(), -H() * 0.48);
    rr(g, x + 14 * s, y + 18 * s, w, h, 16 * s); g.fillStyle = 'rgba(0,0,0,.45)'; g.fill();
    rr(g, x, y, w, h, 16 * s); g.fillStyle = '#efe6cf'; g.fill();
    for (let i = 0; i < 14; i++) circle(g, x + w * 0.72, y + 18 * s + i * (h - 36 * s) / 13, 6 * s, '#1a1420');
    text(g, 'CITY TRANSIT', x + w * 0.36, y + 80 * s, { size: 56 * s, color: '#3a2a20', font: FONTS.ui, weight: 900, spacing: 3 });
    text(g, `ROUTE ${info.route || '9'}  ·  LAST RUN`, x + w * 0.36, y + 160 * s, { size: 44 * s, color: '#5a4a3a', font: FONTS.ui, weight: 800 });
    const k = ease.out(prog(t, 0.3, 0.9)), dstr = info.date || 'NOV 14', dsz = Math.min(130 * s, w * 0.62 / Math.max(1, dstr.length * 0.62));
    text(g, dstr, x + w * 0.36, y + h * 0.54, { size: dsz, color: info.hot ? '#b0101a' : '#1a1622', font: FONTS.ui, weight: 900, alpha: k });
    text(g, info.num || 'No. 000417', x + w * 0.86, y + h / 2, { size: 30 * s, color: '#5a4a3a', font: FONTS.ui, weight: 800 });
    if (info.stamp) { const p = prog(t, 0.9, 1.2); if (p > 0) { g.save(); g.translate(x + w * 0.36, y + h * 0.84); g.rotate(-0.08); g.scale(1.6 - 0.6 * ease.out(p), 1.6 - 0.6 * ease.out(p)); g.globalAlpha = p; rr(g, -260 * s, -46 * s, 520 * s, 92 * s, 10 * s); g.strokeStyle = RED; g.lineWidth = 8 * s; g.stroke(); text(g, info.stamp, 0, 4 * s, { size: 58 * s, color: RED, font: FONTS.ui, weight: 900, spacing: 4 }); g.restore(); } }
    g.restore();
  });
  caption(g, t, info, 0.12);
});

// calendario de pared: los dias se tachan solos; params: month, from (primer dia), n (cuantos tachados), skip (lista de dias en rojo), circle (dia rodeado)
reg2('calendar', (g, t, info) => {
  const s = SC(), cam = cam2(t, info, 0.5);
  backdrop(g, ['#e8dcc4', '#d8c8a8']);
  withCam(g, cam, (g) => {
    for (let i = 0; i < W(); i += 90 * s) { g.fillStyle = 'rgba(160,130,90,.12)'; g.fillRect(i, 0, 40 * s, H()); }
    const w = 1000 * s, h = 760 * s, x = CX() - w / 2, y = H() * 0.56 - h / 2;
    circle(g, CX(), y - 24 * s, 12 * s, '#6a5a4a');
    rr(g, x + 12 * s, y + 16 * s, w, h, 12 * s); g.fillStyle = 'rgba(0,0,0,.2)'; g.fill();
    rr(g, x, y, w, h, 12 * s); g.fillStyle = '#fbf7ee'; g.fill();
    rr(g, x, y, w, 130 * s, 12 * s); g.fillStyle = '#c8402a'; g.fill();
    text(g, info.month || 'NOVEMBER', CX(), y + 66 * s, { size: 68 * s, color: '#fff', font: FONTS.ui, weight: 900, spacing: 6 });
    const cw = w / 7, ch = (h - 150 * s) / 5, from = info.from ?? 0, skip = info.skip || [], n = info.n ?? 0;
    for (let d = 1; d <= 30; d++) {
      const c = (d - 1 + from) % 7, r = Math.floor((d - 1 + from) / 7); if (r > 4) continue;
      const cx = x + c * cw + cw / 2, cy = y + 150 * s + r * ch + ch / 2;
      g.strokeStyle = 'rgba(0,0,0,.08)'; g.lineWidth = 2; g.strokeRect(x + c * cw, y + 140 * s + r * ch, cw, ch);
      const red = skip.includes(d);
      text(g, String(d), cx, cy, { size: 46 * s, color: red ? '#c8102a' : '#2a2a34', font: FONTS.ui, weight: 900 });
      const order = skip.length ? skip.indexOf(d) : d - (info.start || 1); const k = order >= 0 && order < n ? ease.out(prog(t, 0.2 + order * 0.18, 0.4 + order * 0.18)) : 0;
      if (k > 0) { seg(g, [[cx - 40 * s, cy - 40 * s], [lerp(cx - 40 * s, cx + 40 * s, k), lerp(cy - 40 * s, cy + 40 * s, k)]], 8 * s, red ? '#c8102a' : '#1a1a2a'); if (k > 0.5) seg(g, [[cx + 40 * s, cy - 40 * s], [lerp(cx + 40 * s, cx - 40 * s, (k - 0.5) * 2), lerp(cy - 40 * s, cy + 40 * s, (k - 0.5) * 2)]], 8 * s, red ? '#c8102a' : '#1a1a2a'); }
      if (info.circle === d) { const p = prog(t, 0.6, 1.4); g.save(); g.strokeStyle = '#c8102a'; g.lineWidth = 7 * s; g.beginPath(); g.ellipse(cx, cy, 62 * s, 50 * s, 0.1, -Math.PI / 2, -Math.PI / 2 + Math.PI * 2 * p); g.stroke(); g.restore(); }
    }
  });
  caption(g, t, info, 0.075);
});

// cafeteria de carretera de dia (luminosa): barra, taburetes, ventanal con sol. params: boss, lena, e, lenaE, bossE, sun (false: de noche)
reg2('diner', (g, t, info) => {
  const s = SC(), cam = cam2(t, info, 0.7), GY = H() * 0.88, day = info.sun !== false;
  withCam(g, cam, (g) => {
    backdrop(g, day ? ['#f6e3c0', '#f2d2a0'] : ['#1a1220', '#2a1a28']);
    const wx = W() * 0.05, wy = H() * 0.1, ww = W() * 0.9, wh = H() * 0.36;
    g.fillStyle = linGrad(g, 0, wy, 0, wy + wh, day ? ['#7cc4f8', '#d8f0ff'] : ['#060814', '#141a30']); g.fillRect(wx, wy, ww, wh);
    if (day) FX.sun(g, W() * 0.8, wy + wh * 0.35, 60 * s); else FX.stars(g, t, { area: [wx, wy, ww, wh * 0.6], count: 40 });
    FX.skyline(g, { x: wx, y: wy + wh, w: ww, minH: 40 * s, maxH: 160 * s, color: day ? '#9aa6c0' : '#0c0c18', windowColor: alpha('#ffd08a', day ? 0.2 : 0.7), lit: 0.3, seed: 21, minW: 50, maxW: 120 });
    for (let i = 0; i <= 6; i++) seg(g, [[wx + ww * i / 6, wy], [wx + ww * i / 6, wy + wh]], 10 * s, day ? '#e8e0d0' : '#2a2030');
    for (let i = 0; i < 9; i++) { g.fillStyle = i % 2 ? '#c8402a' : '#f4efe6'; g.fillRect(wx + i * ww / 9, wy - 30 * s, ww / 9, 30 * s); }
    rr(g, W() * 0.35, wy + 20 * s, W() * 0.3, 70 * s, 10 * s); g.fillStyle = day ? '#2a3a5a' : '#140c14'; g.fill();
    text(g, 'OPEN 24 HOURS', CX(), wy + 56 * s, { size: 40 * s, color: day ? '#ffe08a' : '#ff6a8a', font: FONTS.ui, weight: 900, glow: day ? 0 : 20, glowColor: '#ff6a8a' });
    if (info.boss) fig(g, { x: W() * 0.8, y: GY - 120 * s, s: 2.1 * s, facing: -1, outfit: CAST.BOSS, pose: breathe(P(info.bossPose || 'crossArms'), t), expr: info.bossE || 'angry' });
    FX.counter(g, { x: W() * 0.02, y: GY - 40 * s, w: W() * 0.96, h: 170 * s, color: day ? '#c8402a' : '#5a1a1a', top: '#e8e0d0', doors: 10 });
    for (let i = 0; i < 6; i++) FX.stool(g, W() * (0.1 + i * 0.16), GY + 60 * s, 1.4 * s, '#3a3a44');
    if (info.lena) fig(g, { x: W() * 0.24, y: GY - 120 * s, s: 2.1 * s, facing: 1, outfit: CAST.LENA, pose: breathe(P(info.lenaPose || 'talk'), t), expr: info.lenaE || 'smile', look: [1, 0] });
    if (info.you !== false) fig(g, { x: W() * 0.5, y: GY - 120 * s, s: 2.1 * s, facing: info.lena ? -1 : 1, outfit: CAST.YOU, pose: breathe(P(info.pose || 'holdFront'), t), expr: info.e || 'neutral' });
  });
  caption(g, t, info);
});

// el conductor visto en el retrovisor: solo se le ven los ojos; params: e (gesto), blink, say (bocadillo)
reg2('driver', (g, t, info) => {
  const s = SC(), cam = cam2(t, info, 0.3);
  backdrop(g, ['#05060c', '#0c0e1a']);
  withCam(g, cam, (g) => {
    for (let k = 0; k < 4; k++) { const lx = W() - ((t * 600 + k * 520) % (W() + 600)) + 300; glow(g, lx, H() * 0.75, 200 * s, k % 2 ? '#ffcf8a' : '#ff6a4a', 0.25); }
    seg(g, [[CX(), 0], [CX(), H() * 0.2]], 14 * s, '#1a1c26');
    const mw = Math.min(1100 * s, W() * 0.92), mh = 360 * s, mx = CX() - mw / 2, my = H() * 0.22;
    rr(g, mx - 16 * s, my - 16 * s, mw + 32 * s, mh + 32 * s, 60 * s); g.fillStyle = '#1a1c26'; g.fill();
    g.save(); rr(g, mx, my, mw, mh, 50 * s); g.clip();
    g.fillStyle = linGrad(g, 0, my, 0, my + mh, ['#141826', '#20263a']); g.fillRect(mx, my, mw, mh);
    const r = 520 * s; bigFace(g, CX(), my + mh * 0.95, r, { outfit: CAST.WORKER, expr: info.e || 'neutral', look: info.look || [0.1 * Math.sin(t), 0], blink: ((t + 0.3) % 3.4) < 0.1, rimColor: '#8ab0ff', rimSide: -1 });
    g.fillStyle = 'rgba(180,200,255,.07)'; g.beginPath(); g.moveTo(mx, my); g.lineTo(mx + mw * 0.3, my); g.lineTo(mx + mw * 0.1, my + mh); g.lineTo(mx, my + mh); g.fill();
    g.restore();
    rr(g, W() * 0.1, H() * 0.8, W() * 0.8, 40 * s, 20 * s); g.fillStyle = '#10121c'; g.fill();
    text(g, info.route ? `ROUTE ${info.route}` : 'ROUTE 9', CX(), H() * 0.9, { size: 50 * s, color: '#ffb24a', font: FONTS.ui, weight: 900, glow: 18, glowColor: '#ffb24a', alpha: 0.85 });
  });
  caption(g, t, info, 0.1);
});
