// Efectos sintetizados con Web Audio (autoría propia, sin archivos externos).
let ctx = null;

export function initAudio() {
  if (!ctx) ctx = new (window.AudioContext || window.webkitAudioContext)();
  return ctx.resume();
}

function tone(freq, start, dur, { type = 'triangle', vol = 0.2, slide = 0 } = {}) {
  const o = ctx.createOscillator();
  const g = ctx.createGain();
  o.type = type;
  o.frequency.setValueAtTime(freq, start);
  if (slide) o.frequency.exponentialRampToValueAtTime(freq * slide, start + dur);
  g.gain.setValueAtTime(vol, start);
  g.gain.exponentialRampToValueAtTime(0.0001, start + dur);
  o.connect(g).connect(ctx.destination);
  o.start(start);
  o.stop(start + dur + 0.02);
}

function ruido(start, dur, vol) {
  const buf = ctx.createBuffer(1, ctx.sampleRate * dur, ctx.sampleRate);
  const d = buf.getChannelData(0);
  for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * Math.sin((i / d.length) * Math.PI);
  const src = ctx.createBufferSource();
  const filtro = ctx.createBiquadFilter();
  const g = ctx.createGain();
  filtro.type = 'lowpass';
  filtro.frequency.value = 900;
  g.gain.value = vol;
  src.buffer = buf;
  src.connect(filtro).connect(g).connect(ctx.destination);
  src.start(start);
}

const SFX = {
  // rugido de alebrije: ruido grave + sierra que baja
  rugido: t => { ruido(t, 0.7, 0.5); tone(140, t, 0.6, { type: 'sawtooth', vol: 0.15, slide: 0.55 }); },
  // campanitas al cambiar de colores
  colores: t => [784, 988, 1175, 1568].forEach((f, i) => tone(f, t + i * 0.06, 0.35, { vol: 0.12 })),
  brillo: t => { tone(1760, t, 0.15, { type: 'sine', vol: 0.1 }); tone(2637, t + 0.05, 0.25, { type: 'sine', vol: 0.08 }); },
};

export function sfx(nombre) {
  if (ctx?.state === 'running') SFX[nombre]?.(ctx.currentTime);
}
