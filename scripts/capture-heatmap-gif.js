const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1200, height: 800 });

  // Navigate to heatmap timelapse
  await page.goto('http://localhost:3001/heatmap/', { waitUntil: 'networkidle' });

  // Wait for data to load and animation to start
  await page.waitForTimeout(3000);

  // Capture frames every 200ms for 16 seconds (one full cycle)
  const framesDir = '/tmp/heatmap-frames';
  fs.mkdirSync(framesDir, { recursive: true });

  const totalFrames = 80; // 16 seconds at 5fps
  for (let i = 0; i < totalFrames; i++) {
    const framePath = path.join(framesDir, `frame-${String(i).padStart(4, '0')}.png`);
    await page.screenshot({ path: framePath });
    await page.waitForTimeout(200);
    if (i % 10 === 0) console.log(`Frame ${i}/${totalFrames}`);
  }

  await browser.close();
  console.log(`Captured ${totalFrames} frames`);

  // Now convert to GIF using ffmpeg
  const { execSync } = require('child_process');
  try {
    execSync('which ffmpeg');
    console.log('Converting to GIF with ffmpeg...');
    execSync(`ffmpeg -y -framerate 5 -i ${framesDir}/frame-%04d.png -vf "scale=800:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer" /tmp/roman-heatmap-timelapse.gif`);

    const gifSize = fs.statSync('/tmp/roman-heatmap-timelapse.gif').size;
    console.log(`GIF created: ${(gifSize / 1024 / 1024).toFixed(1)} MB`);

    // Copy to MacBook
    execSync('scp /tmp/roman-heatmap-timelapse.gif craigvandergalien@100.106.66.72:/Users/craigvandergalien/Desktop/roman-heatmap-timelapse.gif');
    console.log('Copied to MacBook Desktop');
  } catch (e) {
    console.log('ffmpeg not available, trying with gifski or other tools...');
    // Try gifski
    try {
      execSync(`gifski -o /tmp/roman-heatmap-timelapse.gif --fps 5 --width 800 ${framesDir}/frame-*.png`);
      execSync('scp /tmp/roman-heatmap-timelapse.gif craigvandergalien@100.106.66.72:/Users/craigvandergalien/Desktop/roman-heatmap-timelapse.gif');
      console.log('Created with gifski and copied to MacBook');
    } catch (e2) {
      console.log('No GIF tool available. Frames are at ' + framesDir);
      console.log('Install ffmpeg: brew install ffmpeg');
      console.log('Then run: ffmpeg -framerate 5 -i /tmp/heatmap-frames/frame-%04d.png -vf "scale=800:-1" /tmp/roman-heatmap-timelapse.gif');
    }
  }
})();
