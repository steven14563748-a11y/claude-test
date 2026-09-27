// 用无头 Chromium 逐帧渲染 index.html，并通过管道交给 ffmpeg 编码成 MP4
//   node render.js                 → 输出 medical-history.mp4（需先运行 audio.py 生成 audio.wav）
//   node render.js --still 3,7.5   → 只截取指定时间点的静帧到 frames/
const path = require('path');
const fs = require('fs');
const { spawn, execSync } = require('child_process');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const FPS = 30, DURATION = 30;
const OUT = path.join(__dirname, 'medical-history.mp4');
const ffmpegBin = process.env.FFMPEG ||
  execSync(`python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"`).toString().trim();

(async () => {
  const stillArg = process.argv.indexOf('--still');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('pageerror', e => { console.error('page error:', e.message); process.exit(1); });
  await page.goto('file://' + path.join(__dirname, 'index.html'));
  await page.evaluate(() => window.ready);

  if (stillArg > 0) {
    fs.mkdirSync(path.join(__dirname, 'frames'), { recursive: true });
    for (const t of process.argv[stillArg + 1].split(',').map(Number)) {
      await page.evaluate(t => window.render(t), t);
      const file = path.join(__dirname, 'frames', `still_${t.toFixed(2)}.png`);
      await page.screenshot({ path: file });
      console.log(file);
    }
    await browser.close();
    return;
  }

  const ff = spawn(ffmpegBin, [
    '-y', '-loglevel', 'error',
    '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'png', '-i', '-',
    '-i', path.join(__dirname, 'audio.wav'),
    '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-r', String(FPS),
    '-c:a', 'aac', '-b:a', '192k', '-shortest', '-movflags', '+faststart',
    OUT,
  ], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => ff.on('close', c => (c === 0 ? res() : rej(new Error('ffmpeg exit ' + c)))));

  const total = FPS * DURATION, t0 = Date.now();
  for (let i = 0; i < total; i++) {
    await page.evaluate(t => window.render(t), i / FPS);
    const buf = await page.screenshot({ type: 'png' });
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (i % 90 === 0) console.log(`frame ${i}/${total}  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end();
  await done;
  await browser.close();
  console.log('done →', OUT);
})();
