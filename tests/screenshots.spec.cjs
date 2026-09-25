const { test, expect } = require('@playwright/test');

test('generate README screenshots', async ({ page }) => {
  await page.goto('/exercises');
  await expect(page.locator('body')).toBeVisible();

  await page.screenshot({
    path: 'screenshots/01-exercises.png',
    fullPage: true
  });

  await page.goto('/login');
  await expect(page.locator('body')).toBeVisible();

  await page.screenshot({
    path: 'screenshots/02-login.png',
    fullPage: true
  });

  await page.goto('/signup');
  await expect(page.locator('body')).toBeVisible();

  await page.screenshot({
    path: 'screenshots/03-signup.png',
    fullPage: true
  });
});
