const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ viewport: { width: 1200, height: 800 } });

  const pages = [
    '/',
    '/letters/',
    '/letters/?topics=monasticism',
    '/letters/?firstEnglish=true',
    '/letters/?from=350&to=399',
    '/letters/augustine_hippo/1/',
    '/letters/gregory_great/1001/',
    '/letters/pliny_younger/1001/',
    '/letters/basil_caesarea/',
    '/letters/symmachus/',
    '/authors/',
    '/map/',
    '/network/',
    '/thesis/',
    '/about/',
    '/correspondence/',
    '/heatmap/',
  ];

  for (const path of pages) {
    const url = 'https://romanletters.org' + path;
    const page = await context.newPage();
    const errors = [];
    const warnings = [];

    page.on('console', msg => {
      if (msg.type() === 'error') errors.push(msg.text());
      if (msg.type() === 'warning') warnings.push(msg.text());
    });

    page.on('pageerror', err => {
      errors.push('PAGE ERROR: ' + err.message);
    });

    try {
      await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
      await page.waitForTimeout(3000); // Wait for client-side hydration + data loading

      // Try clicking interactive elements
      if (path === '/letters/') {
        // Click a century button
        try {
          await page.click('text=4th c.', { timeout: 5000 });
          await page.waitForTimeout(1000);
        } catch (e) { /* button may not exist */ }

        // Try topic pill
        try {
          await page.click('text=monasticism', { timeout: 3000 });
          await page.waitForTimeout(1000);
        } catch (e) {}
      }

      if (path === '/letters/?from=350&to=399') {
        // Test pagination
        try {
          await page.click('text=Next', { timeout: 5000 });
          await page.waitForTimeout(1000);
        } catch (e) {}
      }

      // Check for 404 resources
      const failedRequests = [];
      page.on('response', response => {
        if (response.status() >= 400) {
          failedRequests.push(`${response.status()} ${response.url()}`);
        }
      });

    } catch (e) {
      errors.push('NAVIGATION ERROR: ' + e.message);
    }

    const status = errors.length > 0 ? 'ERRORS' : 'OK';
    console.log(`${status} ${path}`);
    if (errors.length > 0) {
      for (const err of errors) {
        console.log(`  ERROR: ${err.substring(0, 200)}`);
      }
    }
    if (warnings.length > 0 && warnings.length <= 3) {
      for (const w of warnings) {
        console.log(`  WARN: ${w.substring(0, 150)}`);
      }
    }

    await page.close();
  }

  await browser.close();
  console.log('\nDone.');
})();
