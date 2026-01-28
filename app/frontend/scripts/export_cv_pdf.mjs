#!/usr/bin/env node
/**
 * Export CV page to PDF with custom fonts/styling.
 *
 * Usage: npx puppeteer browsers install chrome && node scripts/export_cv_pdf.mjs
 *
 * Requires: Dev server running on localhost:5173 (npm run dev)
 */

import puppeteer from 'puppeteer';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUTPUT_PATH = join(__dirname, '..', 'public', 'alex-rembish-cv.pdf');

// Custom CSS to style CV like the DOCX template
const PRINT_STYLES = `
  @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@300;400;600;700&family=Work+Sans:wght@200;300;400&display=swap');

  /* Hide non-CV elements */
  #header,
  .mobile-nav-toggle,
  footer,
  .location-button,
  .btn-download {
    display: none !important;
  }

  /* Reset page */
  body {
    background: white !important;
    color: #000 !important;
    font-family: "Assistant", sans-serif !important;
    font-size: 10pt !important;
    line-height: 1.4 !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }

  #root {
    min-height: auto !important;
  }

  #main {
    margin: 0 !important;
    padding: 0 !important;
    flex: none !important;
  }

  .resume {
    padding: 0 !important;
  }

  .container {
    max-width: none !important;
    padding: 0 !important;
  }

  /* Title section */
  .section-title {
    text-align: center;
    margin-bottom: 0.4cm !important;
    padding-bottom: 0.25cm !important;
    border-bottom: 2pt solid #999 !important;
  }

  .section-title h2 {
    font-family: "Work Sans", sans-serif !important;
    font-weight: 200 !important;
    font-size: 32pt !important;
    text-transform: uppercase !important;
    letter-spacing: 0.15em !important;
    color: #000 !important;
    margin-bottom: 0.15cm !important;
    padding-bottom: 0 !important;
  }

  .section-title h2::after {
    display: none !important;
  }

  .section-title p {
    font-family: "Assistant", sans-serif !important;
    font-weight: 300 !important;
    font-size: 11pt !important;
    color: #434343 !important;
    font-style: normal !important;
  }

  /* Two-column grid */
  .cv-grid {
    display: grid !important;
    grid-template-columns: 1fr 2fr !important;
    gap: 0.4cm !important;
  }

  /* Sidebar (left column) */
  .cv-sidebar {
    padding-right: 0.25cm !important;
    border-right: 1pt solid #ddd !important;
  }

  /* Section headers */
  .resume-title {
    font-family: "Assistant", sans-serif !important;
    font-weight: 600 !important;
    font-size: 10pt !important;
    text-transform: uppercase !important;
    color: #434343 !important;
    margin-top: 0.35cm !important;
    margin-bottom: 0.15cm !important;
    padding-bottom: 0.08cm !important;
    border-bottom: 1pt solid #999 !important;
  }

  .resume-title:first-child {
    margin-top: 0 !important;
  }

  /* Resume items */
  .resume-item {
    padding-left: 0 !important;
    margin-bottom: 0.25cm !important;
    border-left: none !important;
  }

  .resume-item::before {
    display: none !important;
  }

  .resume-item h4 {
    font-family: "Assistant", sans-serif !important;
    font-weight: 600 !important;
    font-size: 9.5pt !important;
    text-transform: uppercase !important;
    color: #434343 !important;
    margin-bottom: 0.05cm !important;
  }

  .resume-item h5 {
    font-family: "Assistant", sans-serif !important;
    font-weight: 400 !important;
    font-size: 8.5pt !important;
    color: #666 !important;
    background: none !important;
    padding: 0 !important;
    margin-bottom: 0.08cm !important;
  }

  .resume-item p,
  .resume-item li {
    font-size: 8.5pt !important;
    color: #000 !important;
    margin-bottom: 0.08cm !important;
    line-height: 1.35 !important;
  }

  .resume-item ul {
    padding-left: 0.35cm !important;
    margin-bottom: 0.08cm !important;
  }

  .resume-item li {
    margin-bottom: 0.03cm !important;
  }

  .resume-item em {
    font-style: normal !important;
    color: #666 !important;
  }

  .resume-item a {
    color: #000 !important;
    text-decoration: none !important;
  }

  .resume-item code {
    background: none !important;
    padding: 0 !important;
    font-family: "Assistant", sans-serif !important;
  }

  /* Icons in contact section */
  .resume-item p > svg {
    display: none !important;
  }

  /* Links section - keep simpler */
  .cv-sidebar .resume-item p {
    margin-bottom: 0.05cm !important;
  }

  /* Manual page breaks */
  .print-break-before {
    break-before: page !important;
  }
`;

async function exportPDF() {
  console.log('Launching browser...');

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();

  // Set viewport to A4-ish dimensions
  await page.setViewport({ width: 794, height: 1123 }); // A4 at 96 DPI

  console.log('Loading CV page...');
  await page.goto('http://localhost:5173/cv', {
    waitUntil: 'networkidle0',
    timeout: 30000
  });

  console.log('Injecting print styles...');
  await page.addStyleTag({ content: PRINT_STYLES });

  // Wait for fonts to load
  await page.evaluateHandle('document.fonts.ready');
  await new Promise(r => setTimeout(r, 1000)); // Extra wait for fonts

  console.log('Generating PDF...');
  await page.pdf({
    path: OUTPUT_PATH,
    format: 'A4',
    margin: {
      top: '1.2cm',
      right: '1.2cm',
      bottom: '1.2cm',
      left: '1.2cm'
    },
    printBackground: true,
    preferCSSPageSize: false
  });

  await browser.close();

  console.log(`\n✓ PDF saved to: ${OUTPUT_PATH}`);
}

exportPDF().catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});
