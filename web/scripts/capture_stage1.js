const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');

const ARTIFACT_DIR = 'C:\\Users\\LENOVO\\.gemini\\antigravity-ide\\brain\\de457f0a-eb31-4748-9500-fde2a0251805';
const EDGE_PATH = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';

const SCREENS = [
  { id: 'marketing-home', url: 'http://127.0.0.1:3000/' },
  { id: 'branded-404', url: 'http://127.0.0.1:3000/does-not-exist' },
  { id: 'dashboard-runs', url: 'http://127.0.0.1:3000/app/runs' },
];

const CONFIGS = [
  { name: '1440px', width: 1440, height: 900, isMobile: false },
  { name: '390px', width: 390, height: 844, isMobile: true },
];

const THEMES = ['dark', 'light'];

async function run() {
  const browser = await puppeteer.launch({
    executablePath: EDGE_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  try {
    for (const screen of SCREENS) {
      for (const conf of CONFIGS) {
        for (const theme of THEMES) {
          const page = await browser.newPage();
          await page.setViewport({
            width: conf.width,
            height: conf.height,
            isMobile: conf.isMobile,
            deviceScaleFactor: 2,
          });

          await page.goto(screen.url, { waitUntil: 'domcontentloaded', timeout: 15000 });
          await new Promise((r) => setTimeout(r, 300));

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

          await page.reload({ waitUntil: 'domcontentloaded', timeout: 15000 });
          await new Promise((r) => setTimeout(r, 500));

          await page.evaluate((th) => {
            if (th === 'dark') {
              document.documentElement.classList.add('dark');
              document.documentElement.classList.remove('light');
            } else {
              document.documentElement.classList.add('light');
              document.documentElement.classList.remove('dark');
            }
          }, theme);
          await new Promise((r) => setTimeout(r, 300));

          const filename = `stage1_${screen.id}_${theme}_${conf.name}.png`;
          const filePath = path.join(ARTIFACT_DIR, filename);

          await page.screenshot({
            path: filePath,
            fullPage: false,
          });

          console.log(`Saved: ${filename}`);

          // For mobile on home, also capture mobile menu open
          if (screen.id === 'marketing-home' && conf.isMobile) {
            const menuBtn = await page.$('button[aria-label="Toggle navigation menu"]');
            if (menuBtn) {
              await menuBtn.click();
              await new Promise((r) => setTimeout(r, 400));
              const drawerFilename = `stage1_mobile_menu_${theme}_390px.png`;
              await page.screenshot({
                path: path.join(ARTIFACT_DIR, drawerFilename),
                fullPage: false,
              });
              console.log(`Saved: ${drawerFilename}`);
            }
          }

          await page.close();
        }
      }
    }
  } catch (err) {
    console.error('Error during capture:', err);
  } finally {
    await browser.close();
  }
}

run();
