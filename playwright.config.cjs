const fs = require('fs');
const { defineConfig, devices } = require('@playwright/test');

const python = fs.existsSync('.venv/bin/python') ? '.venv/bin/python' : 'python3';

module.exports = defineConfig({
  testDir: './tests',
  timeout: 45000,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report', open: 'never' }]
  ],
  use: {
    baseURL: 'http://127.0.0.1:8000',
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
    colorScheme: 'light',
    reducedMotion: 'reduce',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure'
  },
  projects: [{
    name: 'chromium',
    use: {
      ...devices['Desktop Chrome'],
      viewport: { width: 1440, height: 900 },
      deviceScaleFactor: 1
    }
  }],
  webServer: {
    command: `EXERXEYE_SECRET=playwright-screenshot-secret ${python} app.py`,
    url: 'http://127.0.0.1:8000/health',
    reuseExistingServer: false,
    timeout: 120000
  }
});
