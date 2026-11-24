// his012: You Can Hear Every Phone Call Where Someone Says Your Name. Planos nuevos: centro de llamadas, onda de voz con tu nombre,
// ciudad de noche con llamadas, puente al amanecer y piso compartido luminoso.
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

const NAME = (info) => info.name || 'SAM ROOK';

// centro de llamadas: filas de mesas con cascos y pantallas; params: boss (Crane pasea), e, empty
reg2('callcenter', (g, t, info) => {
  const s = SC(), cam = cam2(t, info, 0.7), GY = H() * 0.9;
  withCam(g, cam, (g) => {
    backdrop(g, ['#d8e0ea', '#c4ced8']);
    for (let i = 0; i < 8; i++) { const x = W() * (0.04 + i * 0.125); rr(g, x, H() * 0.06, W() * 0.09, 22 * s, 8 * s); g.fillStyle = '#f8fbff'; g.fill(); glow(g, x + W() * 0.045, H() * 0.08, 120 * s, '#ffffff', 0.3); }
    rr(g, W() * 0.3, H() * 0.14, W() * 0.4, 90 * s, 10 * s); g.fillStyle = '#1a2a3a'; g.fill();
    const calls = 120 + Math.floor(t * 7);
    text(g, `CALLS TODAY  ${calls}`, CX(), H() * 0.14 + 45 * s, { size: 44 * s, color: '#7affc0', font: FONTS.ui, weight: 900, glow: 14, glowColor: '#7affc0' });
    for (let row = 0; row < 2; row++) {
      const y = H() * (0.55 + row * 0.25), k = row ? 1 : 0.8;
      for (let i = 0; i < 5; i++) {
        const x = W() * (0.08 + i * 0.2);
        rr(g, x - 40 * k * s, y - 150 * k * s, 150 * k * s, 100 * k * s, 6 * s); g.fillStyle = '#1a2230'; g.fill();
        g.fillStyle = (Math.floor(t * 2 + i + row) % 3) ? '#4a8ad0' : '#6ac0f0'; g.fillRect(x - 32 * k * s, y - 142 * k * s, 134 * k * s, 84 * k * s);
        g.fillStyle = '#8a96a6'; g.fillRect(x - 90 * k * s, y - 40 * k * s, 260 * k * s, 16 * k * s);
        if (!(row === 1 && i === 2)) fig(g, { x: x + 20 * k * s, y: y + 100 * k * s, s: 1.2 * k * s, facing: i % 2 ? -1 : 1, outfit: { top: 'tshirt', color: ['#8a6ad0', '#d08a4a', '#4aa08a', '#c05a6a', '#6a7ad0'][i] }, pose: breathe(P('talk'), t + i), expr: 'neutral', rim: false });
      }
    }
    if (!info.empty) fig(g, { x: W() * 0.48, y: H() * 0.8 + 100 * s, s: 1.25 * s, facing: 1, outfit: CAST.YOU, pose: breathe(P(info.pose || 'phone'), t), expr: info.e || 'neutral' });
    if (info.boss) { const bx = W() * (0.1 + 0.8 * prog(t, 0, info.dur || 3)); fig(g, { x: bx, y: GY + 40 * s, s: 1.7 * s, facing: 1, outfit: CAST.BOSS, pose: breathe(P(info.bossPose || 'crossArms'), t), expr: info.bossE || 'angry' }); }
  });
  caption(g, t, info);
});

// onda de voz de una llamada; tu nombre se ilumina cuando se dice. params: who (texto arriba: "LANDLORD"), name, hot (rojo), at (segundo en que sale el nombre)
reg2('wave', (g, t, info) => {
  const s = SC(), cam = cam2(t, info, 0.3), at = info.at ?? 0.9, hot = info.hot;
  const col = hot ? '#ff4a4a' : '#5ae0d0';
  backdrop(g, ['#05070c', '#0a1018']);
  withCam(g, cam, (g) => {
    const y = H() * 0.55, n = 90, x0 = W() * 0.06, x1 = W() * 0.94;
    for (let i = 0; i < n; i++) {
      const x = lerp(x0, x1, i / (n - 1)), env = 0.35 + 0.65 * Math.abs(noise(i * 0.31 + t * 3, 7)), live = i / n < (t / (info.dur || 3)) + 0.25;
      const h = (40 + 260 * env * Math.abs(Math.sin(i * 0.7 + t * 9))) * s * (live ? 1 : 0.15);
      const nameZone = Math.abs(i - n / 2) < 14 && t > at;
      rr(g, x - 4 * s, y - h / 2, 8 * s, h, 4 * s); g.fillStyle = nameZone ? '#ffd24a' : alpha(col, live ? 0.9 : 0.3); g.fill();
    }
    text(g, info.who || 'INCOMING CALL', CX(), H() * 0.2, { size: 48 * s, color: alpha(CREAM, 0.85), font: FONTS.ui, weight: 900, spacing: 6 });
    circle(g, W() * 0.08, H() * 0.2, 14 * s, (Math.floor(t * 2) % 2) ? RED : '#601010');
    const k = ease.outBack(prog(t, at, at + 0.4)); if (k > 0) { g.save(); g.translate(CX(), H() * 0.84); g.scale(k, k); text(g, `"${NAME(info)}"`, 0, 0, { size: 90 * s, color: '#ffd24a', font: FONTS.ui, weight: 900, glow: 30, glowColor: '#ffb24a' }); g.restore(); }
  });
  caption(g, t, info, 0.1);
});

// ciudad de noche: arcos de luz entre ventanas (llamadas); los que dicen tu nombre van hacia ti. params: n (cuantas te llegan), e
reg2('citycalls', (g, t, info) => {
  const s = SC(), cam = cam2(t, info, 0.5), GY = H() * 0.86;
  withCam(g, cam, (g) => {
    backdrop(g, ['#04040c', '#0c0a1e', '#1a1030']); FX.stars(g, t, { count: 60 });
    FX.skyline(g, { x: -200, y: GY, w: W() + 400, minH: 200 * s, maxH: 620 * s, color: '#0e0c1c', windowColor: alpha('#ffd08a', 0.6), lit: 0.25, seed: 31, minW: 90, maxW: 200 });
    const r = rng(5), you = [W() * 0.5, GY - 60 * s], n = info.n ?? 3;
    for (let i = 0; i < 9; i++) {
      const a = [r() * W(), GY - (200 + r() * 380) * s], b = i < n ? you : [r() * W(), GY - (200 + r() * 380) * s];
      const k = (t * 0.5 + i * 0.13) % 1, mid = [(a[0] + b[0]) / 2, Math.min(a[1], b[1]) - 220 * s];
      const c = i < n ? '#ffd24a' : '#5a8aff';
      g.save(); g.strokeStyle = alpha(c, i < n ? 0.75 : 0.3); g.lineWidth = (i < n ? 4 : 2) * s; g.setLineDash([14 * s, 12 * s]); g.lineDashOffset = -t * 80;
      g.beginPath(); g.moveTo(a[0], a[1]); g.quadraticCurveTo(mid[0], mid[1], b[0], b[1]); g.stroke(); g.restore();
      const q = (u) => [(1 - u) ** 2 * a[0] + 2 * (1 - u) * u * mid[0] + u * u * b[0], (1 - u) ** 2 * a[1] + 2 * (1 - u) * u * mid[1] + u * u * b[1]];
      const [px, py] = q(k); glow(g, px, py, 40 * s, c, 0.8); circle(g, a[0], a[1], 7 * s, c);
    }
    g.fillStyle = '#08060e'; g.fillRect(-W(), GY, W() * 3, H());
    fig(g, { x: you[0], y: GY + 70 * s, s: 1.6 * s, facing: 1, outfit: CAST.YOU, pose: breathe(P(info.pose || 'handsOnHead'), t), expr: info.e || 'scared', rim: { color: '#ffd24a', dir: [0, -1], w: 5 } });
  });
  caption(g, t, info);
});

// puente sobre el rio, al amanecer o de noche. params: night, dad (tu padre al otro lado), e, dadE, close (0-1: se acercan)
reg2('bridge', (g, t, info) => {
  const s = SC(), cam = cam2(t, info, 0.5), GY = H() * 0.66, night = !!info.night;
  withCam(g, cam, (g) => {
    backdrop(g, night ? ['#05060e', '#10142a', '#1a1e38'] : ['#2a1a3a', '#c86a5a', '#ffb070', '#ffd8a0']);
    if (night) FX.moon(g, W() * 0.78, H() * 0.18, 50 * s); else FX.sun(g, W() * 0.72, GY - 40 * s, 80 * s, '#fff0c0', '#ffa050', 4);
    FX.skyline(g, { x: -200, y: GY, w: W() + 400, minH: 60 * s, maxH: 240 * s, color: night ? '#0a0a18' : '#4a2a3a', windowColor: alpha('#ffd08a', night ? 0.6 : 0.2), lit: 0.25, seed: 44, minW: 60, maxW: 140 });
    g.fillStyle = linGrad(g, 0, GY, 0, H(), night ? ['#0a1028', '#04060e'] : ['#e08a6a', '#5a3a5a']); g.fillRect(-W(), GY, W() * 3, H());
    for (let i = 0; i < 14; i++) { const y = GY + 20 * s + i * 22 * s, x = (i * 173 + t * 40) % W(); g.fillStyle = alpha(night ? '#8ab0ff' : '#fff0c0', 0.18); g.fillRect(x, y, 120 * s, 3 * s); }
    const DY = H() * 0.8;
    g.fillStyle = night ? '#1a1a28' : '#3a2a34'; g.fillRect(-W(), DY, W() * 3, 50 * s);
    for (let i = -2; i < 12; i++) { const x = i * 200 * s; seg(g, [[x, DY], [x, DY - 120 * s]], 8 * s, night ? '#2a2a3a' : '#4a3440'); }
    seg(g, [[-W(), DY - 120 * s], [W() * 2, DY - 120 * s]], 10 * s, night ? '#2a2a3a' : '#4a3440');
    for (const x of [0.15, 0.85]) FX.lampPost(g, W() * x, DY, 360 * s, { on: night, light: '#ffcf8a' });
    const c = info.close ?? 0;
    fig(g, { x: W() * lerp(0.3, 0.44, c), y: DY, s: 1.8 * s, facing: 1, outfit: CAST.YOU, pose: breathe(P(info.pose || 'stand'), t), expr: info.e || 'worried' });
    if (info.dad) fig(g, { x: W() * lerp(0.72, 0.56, c), y: DY, s: 1.85 * s, facing: -1, outfit: CAST.DAD, pose: breathe(P(info.dadPose || 'holdFront'), t), expr: info.dadE || 'sad' });
  });
  caption(g, t, info);
});

// piso compartido de dia (cocina luminosa); params: lena (Maya), lenaE, e, pose, mail (sobres en la mesa)
reg2('apartment', (g, t, info) => {
  const s = SC(), cam = cam2(t, info, 0.6), GY = H() * 0.88;
  withCam(g, cam, (g) => {
    backdrop(g, ['#f8e8cc', '#f0d8b0']);
    for (let i = 0; i < W(); i += 120 * s) { g.fillStyle = 'rgba(200,160,110,.12)'; g.fillRect(i, 0, 60 * s, H() * 0.7); }
    const wx = W() * 0.58, wy = H() * 0.12, ww = W() * 0.32, wh = H() * 0.36;
    g.fillStyle = linGrad(g, 0, wy, 0, wy + wh, ['#7cc4f8', '#d8f0ff']); g.fillRect(wx, wy, ww, wh);
    FX.skyline(g, { x: wx, y: wy + wh, w: ww, minH: 30 * s, maxH: 140 * s, color: '#9aa6c0', windowColor: alpha('#ffffff', 0.4), lit: 0.3, seed: 52, minW: 40, maxW: 90 });
    g.strokeStyle = '#fff8ee'; g.lineWidth = 14 * s; g.strokeRect(wx, wy, ww, wh); seg(g, [[wx + ww / 2, wy], [wx + ww / 2, wy + wh]], 10 * s, '#fff8ee');
    rr(g, W() * 0.06, H() * 0.14, W() * 0.3, H() * 0.2, 8 * s); g.fillStyle = '#b8845a'; g.fill();
    for (let i = 0; i < 4; i++) circle(g, W() * (0.1 + i * 0.07), H() * 0.3, 22 * s, ['#e05a4a', '#f0c04a', '#5ac08a', '#4a8ae0'][i]);
    g.fillStyle = '#c89a6a'; g.fillRect(-W(), GY - 10 * s, W() * 3, H());
    rr(g, W() * 0.28, GY - 190 * s, W() * 0.44, 26 * s, 8 * s); g.fillStyle = '#8a5a3a'; g.fill();
    seg(g, [[W() * 0.32, GY - 170 * s], [W() * 0.32, GY]], 12 * s, '#6a4028'); seg(g, [[W() * 0.68, GY - 170 * s], [W() * 0.68, GY]], 12 * s, '#6a4028');
    if (info.mail) for (let i = 0; i < 3; i++) { g.save(); g.translate(W() * (0.4 + i * 0.07), GY - 200 * s); g.rotate(-0.1 + i * 0.12); rr(g, -50 * s, -32 * s, 100 * s, 64 * s, 4 * s); g.fillStyle = i === 1 ? '#ffe0e0' : '#fffaf0'; g.fill(); if (i === 1) text(g, 'PAID', 0, 0, { size: 26 * s, color: '#c8102a', font: FONTS.ui, weight: 900 }); g.restore(); }
    if (info.lena) fig(g, { x: W() * 0.8, y: GY + 20 * s, s: 2 * s, facing: -1, outfit: CAST.LENA, pose: breathe(P(info.lenaPose || 'phone'), t), expr: info.lenaE || 'nervous' });
    if (info.you !== false) fig(g, { x: W() * 0.2, y: GY + 20 * s, s: 2 * s, facing: 1, outfit: CAST.YOU, pose: breathe(P(info.pose || 'stand'), t), expr: info.e || 'neutral' });
  });
  caption(g, t, info);
});
