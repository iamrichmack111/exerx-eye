(async () => {
const { chromium } = require('@playwright/test');
const fs = require('fs');
const path = require('path');

const baseURL = process.env.DEMO_BASE_URL || 'http://127.0.0.1:8017';
const outDir = path.resolve(process.env.DEMO_CAPTURE_DIR || 'demo/captures');
fs.mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1920, height: 1080 },
  deviceScaleFactor: 1,
  colorScheme: 'dark',
  reducedMotion: 'reduce'
});
const page = await context.newPage();

async function prep(url) {
  await page.addInitScript(() => {
    localStorage.setItem('exerxeye-color-mode-v1', 'dark');
  });
  const response = await page.goto(baseURL + url, { waitUntil: 'networkidle', timeout: 45000 });
  if (!response || response.status() >= 400) {
    throw new Error(`Failed to load ${url}: ${response ? response.status() : 'no response'}`);
  }
  const contentType = response.headers()['content-type'] || '';
  if (!contentType.includes('text/html')) {
    throw new Error(`Expected HTML at ${url}, got ${contentType}`);
  }
  await page.addStyleTag({ content: `
    *, *::before, *::after { animation: none !important; transition: none !important; caret-color: transparent !important; }
    html { scroll-behavior: auto !important; }
  `});
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.waitForTimeout(250);
}

async function shot(name) {
  await page.screenshot({ path: path.join(outDir, name), fullPage: false });
}

// 1 — Exercise library, real HTML route is / (not legacy JSON /exercises).
await prep('/');
await page.locator('.movement-card').first().waitFor({ state: 'visible' });
await shot('01-explore-dark.png');

// 2 — Exercise detail.
const exerciseId = await page.evaluate(async () => {
  const r = await fetch('/api/exercises?limit=1');
  const data = await r.json();
  const item = data.results?.[0] || data[0];
  return item?.id;
});
if (!exerciseId) throw new Error('Could not resolve an exercise for demo capture');
await prep(`/exercise/${exerciseId}`);
await shot('02-exercise-detail.png');

// Create a local demo account. A fresh demo database is used by build_demo.sh.
await prep('/signup');
await page.locator('input[name="username"]').fill('demoathlete');
await page.locator('input[name="password"]').fill('DemoTraining42!');
await page.locator('input[name="confirm_password"]').fill('DemoTraining42!');
await Promise.all([
  page.waitForURL(/\/dashboard/, { timeout: 20000 }),
  page.locator('button[type="submit"]').click()
]);
await page.waitForLoadState('networkidle');
await shot('03-dashboard.png');

// Generate a full-body plan so the demo has real content.
await prep('/workouts');
await page.locator('#generator-preset').selectOption('full_body');
const count = page.locator('select[name="count"]');
if (await count.count()) await count.selectOption('6');
const name = page.locator('input[name="name"]');
if (await name.count()) await name.fill('Demo Full Body');
await Promise.all([
  page.waitForURL(/\/workouts\/\d+/, { timeout: 20000 }),
  page.locator('#generator-form button[type="submit"]').click()
]);
await page.waitForLoadState('networkidle');
await shot('04-workout.png');

// 5 — Planner.
await prep('/planner');
await shot('05-planner.png');

// 6 — Progress.
await prep('/progress?days=30');
await shot('06-progress.png');

// 7 — Export center.
await prep('/exports');
await shot('07-exports.png');

// 8 — Finish on the dashboard after a plan exists.
await prep('/dashboard');
await shot('08-outro.png');

await browser.close();
console.log(`Captured 8 demo screens in ${outDir}`);

})().catch(err => { console.error(err); process.exit(1); });
