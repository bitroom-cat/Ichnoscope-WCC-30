const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');

const ARTIFACT_DIR = 'C:\\Users\\LENOVO\\.gemini\\antigravity-ide\\brain\\de457f0a-eb31-4748-9500-fde2a0251805';
const EDGE_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';

const TABS = [
  { id: 'tokens', label: '1. Design Tokens & Contrast' },
  { id: 'buttons-badges', label: '2. Buttons & Badges' },
  { id: 'forms-cards', label: '3. Forms & Cards' },
  { id: 'data-table', label: '4. Table & Stepper' },
  { id: 'code-diff', label: '5. Diff & Logs' },
  { id: 'feedback', label: '6. Modals & Feedback' },
];

const CONFIGS = [
  { width: 1440, height: 900, isMobile: false },
  { width: 390, height: 844, isMobile: true },
];

const THEMES = ['dark', 'light'];

async function run() {
  const browser = await puppeteer.launch({
    executablePath: EDGE_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  try {
    for (const conf of CONFIGS) {
      for (const theme of THEMES) {
        const page = await browser.newPage();
        await page.setViewport({
          width: conf.width,
          height: conf.height,
          isMobile: conf.isMobile,
          deviceScaleFactor: 2,
        });

        // Set theme in localStorage before load
        await page.goto('http://localhost:3000/styleguide', { waitUntil: 'networkidle0' });

        await page.evaluate((th) => {
          localStorage.setItem('theme', th);
          if (th === 'dark') {
            document.documentElement.classList.add('dark');
            document.documentElement.classList.remove('light');
          } else {
            document.documentElement.classList.add('light');
            document.documentElement.classList.remove('dark');
          }
        }, theme);

        // Reload to let next-themes pick it up cleanly
        await page.reload({ waitUntil: 'networkidle0' });
        await new Promise((r) => setTimeout(r, 400));

        // Ensure theme class is applied
        await page.evaluate((th) => {
          if (th === 'dark') {
            document.documentElement.classList.add('dark');
            document.documentElement.classList.remove('light');
          } else {
            document.documentElement.classList.remove('dark');
            document.documentElement.classList.add('light');
          }
        }, theme);

        for (const tab of TABS) {
          // Click tab button
          await page.evaluate((tabId) => {
            const tabs = Array.from(document.querySelectorAll('button[role="tab"]'));
            const target = tabs.find((b) => b.textContent.includes(tabId) || b.textContent.includes(tabId.replace('-', ' ')));
            if (target) {
              target.click();
            } else {
              // try matching by tab order
              const map = {
                'tokens': 0,
                'buttons-badges': 1,
                'forms-cards': 2,
                'data-table': 3,
                'code-diff': 4,
                'feedback': 5
              };
              const idx = map[tabId];
              if (tabs[idx]) tabs[idx].click();
            }
          }, tab.id);

          await new Promise((r) => setTimeout(r, 400));

          const filename = `styleguide_${tab.id}_${theme}_${conf.width}px.png`;
          const filePath = path.join(ARTIFACT_DIR, filename);

          await page.screenshot({
            path: filePath,
            fullPage: false, // capture the primary viewport clearly
          });

          console.log(`Captured: ${filename}`);
        }

        await page.close();
      }
    }
  } finally {
    await browser.close();
  }
}

run().catch((err) => {
  console.error(err);
  process.exit(1);
});
