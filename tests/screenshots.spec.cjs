const { test, expect } = require('@playwright/test');

async function prepare(page, path, mode = 'light') {
  await page.addInitScript((selectedMode) => {
    localStorage.setItem('exerxeye-color-mode-v1', selectedMode);
  }, mode);

  const response = await page.goto(path, {
    waitUntil: 'networkidle',
    timeout: 30000
  });

  expect(response).not.toBeNull();
  expect(response.status()).toBeLessThan(400);
  expect(response.headers()['content-type'] || '').toContain('text/html');
  await expect(page.locator('body')).toBeVisible();

  await page.addStyleTag({
    content: `
      *, *::before, *::after {
        animation: none !important;
        transition: none !important;
        caret-color: transparent !important;
      }
      html { scroll-behavior: auto !important; }
    `
  });

  await page.evaluate(async () => {
    if ('serviceWorker' in navigator) {
      const regs = await navigator.serviceWorker.getRegistrations();
      for (const reg of regs) await reg.unregister();
    }
    window.scrollTo(0, 0);
  });

  await page.waitForTimeout(250);
}

test('generate README screenshots from the real HTML UI', async ({ page }) => {
  // IMPORTANT: / is the HTML exercise library.
  // /exercises is a backwards-compatible JSON API endpoint.
  await prepare(page, '/', 'light');
  await expect(page.locator('.page-header h1')).toContainText('Exercise library');
  await expect(page.locator('.movement-card').first()).toBeVisible();
  await page.screenshot({
    path: 'screenshots/01-exercise-library.png',
    fullPage: false
  });

  await prepare(page, '/', 'dark');
  await page.reload({ waitUntil: 'networkidle' });
  await expect(page.locator('html')).toHaveAttribute('data-color-mode', 'dark');
  await expect(page.locator('.movement-card').first()).toBeVisible();
  await page.screenshot({
    path: 'screenshots/02-exercise-library-dark.png',
    fullPage: false
  });

  await prepare(page, '/login', 'dark');
  await expect(page.locator('form')).toBeVisible();
  await page.screenshot({
    path: 'screenshots/03-login.png',
    fullPage: false
  });

  await prepare(page, '/signup', 'dark');
  await expect(page.locator('form')).toBeVisible();
  await page.screenshot({
    path: 'screenshots/04-signup.png',
    fullPage: false
  });
});
