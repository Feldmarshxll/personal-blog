/* An artistic accretion disk, not a physical simulation. No network resources. */
(() => {
  'use strict';
  const root = document.querySelector('[data-black-hole]');
  if (!root) return;
  const canvas = root.querySelector('canvas');
  const button = root.querySelector('[data-animation-toggle]');
  const label = root.querySelector('[data-animation-label]');
  const context = canvas && canvas.getContext('2d');
  if (!context || !button || !label) return;

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let paused = reducedMotion.matches;
  let visible = true;
  let frame = null;
  let previousTime = 0;
  let elapsed = 0;
  let width = 0;
  let height = 0;
  let density = 1;
  const scene = document.createElement('canvas');
  const paint = scene.getContext('2d');
  if (!paint) return;
  const SIZE = 1200;
  scene.width = SIZE;
  scene.height = 1000;
  let seed = 84371;
  const random = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 4294967296; };
  const stars = Array.from({ length: 51 }, () => ({ x: random() * SIZE, y: random() * 910, size: random() * .9 + .3, alpha: random() * .3 + .1, phase: random() * Math.PI * 2 }));

  const glow = paint.createRadialGradient(620, 465, 70, 620, 465, 485);
  glow.addColorStop(0, '#a06a352c');
  glow.addColorStop(.38, '#7e482526');
  glow.addColorStop(.72, '#4b32100e');
  glow.addColorStop(1, '#0b0c0e00');
  paint.fillStyle = glow;
  paint.fillRect(0, 0, SIZE, 1000);
  paint.save();
  paint.translate(620, 465);
  paint.rotate(-.225);

  // Broad, low-opacity bloom gives the narrow bands room to breathe.
  paint.save();
  paint.filter = 'blur(19px)';
  paint.strokeStyle = '#c2834633';
  paint.lineWidth = 29;
  paint.beginPath();
  paint.ellipse(0, 0, 312, 50, 0, 0, Math.PI * 2);
  paint.stroke();
  paint.strokeStyle = '#dcaa6460';
  paint.lineWidth = 14;
  paint.beginPath();
  paint.ellipse(0, 0, 146, 138, 0, 0, Math.PI * 2);
  paint.stroke();
  paint.restore();

  // Hundreds of individually perturbed tracks and dust grains produce texture.
  for (let i = 0; i < 210; i += 1) {
    const radius = 154 + i * 1.28;
    const inner = 1 - i / 210;
    const gradient = paint.createLinearGradient(-radius, 0, radius, 0);
    const alpha = .12 + inner * .36;
    gradient.addColorStop(0, `rgba(155,91,39,${alpha * .08})`);
    gradient.addColorStop(.24, `rgba(202,133,62,${alpha * .7})`);
    gradient.addColorStop(.55, `rgba(250,215,157,${alpha})`);
    gradient.addColorStop(.83, `rgba(207,139,70,${alpha * .55})`);
    gradient.addColorStop(1, `rgba(127,75,32,${alpha * .06})`);
    paint.strokeStyle = gradient;
    paint.lineWidth = random() * .6 + .25;
    paint.beginPath();
    for (let j = 0; j <= 180; j += 1) {
      const angle = j / 180 * Math.PI * 2;
      const ripple = Math.sin(angle * 13 + i * .21) * .45 + Math.sin(angle * 27 - i * .2) * .24;
      const x = Math.cos(angle) * (radius + ripple);
      const y = Math.sin(angle) * (radius * .15 + ripple);
      if (j === 0) paint.moveTo(x, y); else paint.lineTo(x, y);
    }
    paint.stroke();
  }
  for (let i = 0; i < 16000; i += 1) {
    const angle = random() * Math.PI * 2;
    const r = 155 + Math.pow(random(), .7) * 270;
    const alpha = (.12 + random() * .4) * (1 - (r - 155) / 340);
    paint.fillStyle = `rgba(237,${Math.round(164 + random() * 63)},113,${alpha})`;
    paint.fillRect(Math.cos(angle) * r, Math.sin(angle) * r * .15 + (random() - .5) * 3, random() * 1.6 + .3, .4 + random() * .55);
  }

  // The central void occludes the rear disk; its lensed rim rises above it.
  const voidGradient = paint.createRadialGradient(0, 0, 116, 0, 0, 153);
  voidGradient.addColorStop(0, '#08090a');
  voidGradient.addColorStop(.86, '#08090a');
  voidGradient.addColorStop(1, '#08090a00');
  paint.fillStyle = voidGradient;
  paint.beginPath();
  paint.ellipse(0, 0, 153, 146, 0, 0, Math.PI * 2);
  paint.fill();

  for (let i = 0; i < 48; i += 1) {
    const r = 139 + i * .65;
    const strength = Math.exp(-i / 12);
    paint.strokeStyle = `rgba(248,${Math.round(194 + strength * 38)},${Math.round(121 + strength * 49)},${strength * .65})`;
    paint.lineWidth = i < 5 ? 1 : .5;
    paint.beginPath();
    for (let j = 0; j <= 150; j += 1) {
      const angle = Math.PI + j / 150 * Math.PI;
      const wave = Math.sin(angle * 19 + i * .5) * .15;
      const x = Math.cos(angle) * (r + wave);
      const y = Math.sin(angle) * (r * .94 + wave);
      if (j === 0) paint.moveTo(x, y); else paint.lineTo(x, y);
    }
    paint.stroke();
    paint.strokeStyle = `rgba(219,166,103,${strength * .28})`;
    paint.beginPath();
    paint.ellipse(0, 0, r, r * .94, 0, 0, Math.PI);
    paint.stroke();
  }

  // The foreground disk curves around the lower part of the silhouette.
  for (let i = 0; i < 74; i += 1) {
    const offset = i * .55;
    const alpha = Math.exp(-i / 19) * .9;
    const gradient = paint.createLinearGradient(-450, 0, 450, 0);
    gradient.addColorStop(0, 'rgba(160,94,38,0)');
    gradient.addColorStop(.26, `rgba(223,155,82,${alpha * .6})`);
    gradient.addColorStop(.51, `rgba(255,234,190,${alpha})`);
    gradient.addColorStop(.73, `rgba(231,177,105,${alpha * .8})`);
    gradient.addColorStop(1, 'rgba(151,88,33,0)');
    paint.strokeStyle = gradient;
    paint.lineWidth = .55;
    paint.beginPath();
    for (let j = 0; j <= 240; j += 1) {
      const x = -446 + j / 240 * 892;
      const warp = Math.exp(-Math.pow(x / 177, 2)) * (44 + offset);
      const ripple = Math.sin(x * .095 + i * .53) * .28;
      const y = 4 + offset * .17 + warp + ripple;
      if (j === 0) paint.moveTo(x, y); else paint.lineTo(x, y);
    }
    paint.stroke();
  }
  paint.restore();

  const render = () => {
    context.setTransform(density, 0, 0, density, 0, 0);
    context.clearRect(0, 0, width, height);
    context.save();
    context.scale(width / SIZE, height / 1000);
    context.drawImage(scene, 0, 0);
    stars.forEach((star) => {
      const shimmer = .8 + Math.sin(elapsed * .0004 + star.phase) * .2;
      context.fillStyle = `rgba(230,218,196,${star.alpha * shimmer})`;
      context.beginPath();
      context.arc(star.x, star.y, star.size, 0, Math.PI * 2);
      context.fill();
    });
    // Visible streams orbit the disk; the central void occludes their rear path.
    context.save();
    context.translate(620, 465);
    context.rotate(-.225);
    context.globalCompositeOperation = 'screen';
    for (let i = 0; i < 96; i += 1) {
      const angle = i * 2.39996 + elapsed * .00022 * (1 + (i % 4) * .1);
      const r = 165 + (i % 29) * 8.3;
      const x = Math.cos(angle) * r;
      const y = Math.sin(angle) * r * .15;
      if (Math.abs(x) < 154) continue;
      context.strokeStyle = `rgba(255,211,146,${.2 + (i % 5) * .08})`;
      context.lineWidth = .9 + (i % 3) * .35;
      context.beginPath();
      context.ellipse(0, 0, r, r * .15, 0, angle, angle + .13 + (i % 4) * .025);
      context.stroke();
      if (y > 0) { context.fillStyle = '#ffe1aabf'; context.fillRect(x, y, 2.2, 1); }
    }
    context.restore();
    context.restore();
  };
  const shouldRun = () => !paused && visible && !document.hidden;
  const tick = (time) => {
    frame = null;
    if (!shouldRun()) { previousTime = 0; return; }
    if (time - previousTime >= 1000 / 30) {
      elapsed += previousTime ? Math.min(time - previousTime, 100) : 0;
      previousTime = time;
      render();
    }
    frame = window.requestAnimationFrame(tick);
  };
  const synchronize = () => {
    if (shouldRun() && frame === null) { previousTime = 0; frame = window.requestAnimationFrame(tick); }
    if (!shouldRun() && frame !== null) { window.cancelAnimationFrame(frame); frame = null; previousTime = 0; }
    button.setAttribute('aria-pressed', String(paused));
    label.textContent = paused ? 'Включить анимацию' : 'Приостановить анимацию';
  };
  const resize = () => {
    width = root.clientWidth;
    height = root.clientHeight;
    density = Math.min(window.devicePixelRatio || 1, 1.75);
    canvas.width = Math.round(width * density);
    canvas.height = Math.round(height * density);
    render();
  };
  button.addEventListener('click', () => { paused = !paused; synchronize(); render(); });
  reducedMotion.addEventListener('change', (event) => { paused = event.matches; synchronize(); render(); });
  document.addEventListener('visibilitychange', synchronize);
  if ('IntersectionObserver' in window) new IntersectionObserver((entries) => { visible = entries[0].isIntersecting; synchronize(); }, { threshold: 0 }).observe(root);
  if ('ResizeObserver' in window) new ResizeObserver(resize).observe(root); else window.addEventListener('resize', resize);
  resize();
  canvas.hidden = false;
  button.hidden = false;
  root.classList.add('is-ready');
  synchronize();
})();
