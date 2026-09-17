import pkg from '../frontend/node_modules/@playwright/test/index.js';
const { chromium } = pkg;
import path from 'path';
import fs from 'fs';

const CHROME_PATH = 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe';
const ASSETS_DIR = path.resolve('docs/assets');
const FRAMES_DIR = path.resolve('docs/assets/frames');

if (!fs.existsSync(FRAMES_DIR)) {
  fs.mkdirSync(FRAMES_DIR, { recursive: true });
}

(async () => {
  console.log('Launching Chrome for UI capture...');
  const browser = await chromium.launch({
    executablePath: CHROME_PATH,
    headless: true,
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1.5,
  });

  const page = await context.newPage();

  // Mock common API endpoints for rich UI state
  await page.route('**/v1/**', async (route) => {
    const url = route.request().url();

    if (url.includes('/chat/history')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            role: 'user',
            content: 'Review 10-year cardiovascular risk profile for Patient #8491 (58yo M, SBP 142, HbA1c 7.4%, eGFR 64) and assess SGLT2i + GLP-1 RA combination therapy.'
          },
          {
            role: 'assistant',
            content: `### Clinical Risk Assessment & Multi-Organ Trajectory

Based on the MIMIC-IV and Framingham calibration cohorts, here is the synthesis for **Patient #8491**:

| Clinical Dimension | Baseline Metric | Target Threshold | 10-Yr MACE Risk |
| :--- | :--- | :--- | :--- |
| **Systolic BP** | 142 mmHg | < 130 mmHg | +3.8% relative risk |
| **Glycemic Control (HbA1c)** | 7.4% | < 7.0% | Moderate macrovascular risk |
| **Renal Filtration (eGFR)** | 64 mL/min/1.73m² | > 60 mL/min | Stage G2 CKD trajectory |

#### Neuro-Symbolic Guidance & Pharmacogenomics:
1. **SGLT2i + GLP-1 RA Dual Therapy**: Projected to yield an estimated **32% relative risk reduction** in 5-year MACE and attenuate renal filtration decay from -3.8 to -1.2 mL/min/year.
2. **Safety Screen**: Zero detected contraindications. Cross-referenced against CYP2C9 and SLCO1B1 genotypic variants with 99.8% confidence.

*Disclaimer: AI-generated recommendation. Confirm with primary cardiologist before clinical titration.*`
          }
        ])
      });
    }

    if (url.includes('/chat/suggestions')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          suggestions: [
            "Assess 5-year sepsis decompensation risk",
            "Screen drug-drug interactions for Metformin + Empagliflozin",
            "Generate FHIR R4 CarePlan export",
            "Review differential diagnosis for elevated troponin"
          ]
        })
      });
    }

    if (url.includes('/telemedicine/appointments')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 101,
            doctor_name: "Dr. Marcus Vance, MD (Cardiology)",
            patient_name: "Eleanor Rigby",
            appointment_time: "2026-09-18T10:30:00Z",
            status: "CONFIRMED",
            channel_name: "cardio-icu-telemetry-101",
            notes: "Post-STEMI remote telemetry review and titration assessment."
          },
          {
            id: 102,
            doctor_name: "Dr. Elena Rostova, MD (Nephrology)",
            patient_name: "Jonathan Hastings",
            appointment_time: "2026-09-18T14:00:00Z",
            status: "SCHEDULED",
            channel_name: "nephro-consult-102",
            notes: "Stage 3b CKD ambulatory trajectory monitoring."
          }
        ])
      });
    }

    if (url.includes('/telemedicine/doctors')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 1, name: "Dr. Marcus Vance, MD", specialization: "Cardiovascular Medicine" },
          { id: 2, name: "Dr. Elena Rostova, MD", specialization: "Nephrology & Renal Transplant" },
          { id: 3, name: "Dr. Priya Patel, MD", specialization: "Pulmonary & Critical Care" }
        ])
      });
    }

    if (url.includes('/federated/stats')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          pending_count: 1420,
          total_epsilon_spent: 2.34
        })
      });
    }

    if (url.includes('/federated/audits')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            sync_run_id: "SYNC-FED-9021",
            node_id: "node-boston-icu-alpha",
            model_name: "TabICLv2 Multi-Organ Classifier",
            records_synced: 520,
            epsilon_consumed: 0.25,
            delta_consumed: 1e-5,
            status: "SUCCESS",
            error_message: null,
            created_at: "2026-09-17T20:15:00Z"
          },
          {
            id: 2,
            sync_run_id: "SYNC-FED-9020",
            node_id: "node-london-trust-beta",
            model_name: "Sepsis Early-Warning Transformer",
            records_synced: 900,
            epsilon_consumed: 0.40,
            delta_consumed: 1e-5,
            status: "SUCCESS",
            error_message: null,
            created_at: "2026-09-17T18:45:00Z"
          }
        ])
      });
    }

    // Default passthrough / fallback
    return route.continue();
  });

  // Set auth state
  await page.goto('http://127.0.0.1:3000/login');
  await page.evaluate(() => {
    localStorage.setItem('healthcare-auth', JSON.stringify({
      state: {
        token: 'mock-valid-jwt-token-for-preview',
        user: {
          id: 1,
          username: 'Dr. Sarah Lin',
          email: 'clinician@hospital.org',
          role: 'doctor',
          name: 'Dr. Sarah Lin, MD'
        }
      },
      version: 0
    }));
  });

  // Helper to safely capture screenshot
  const capture = async (urlPath, filename, prepareFn = null) => {
    console.log(`Navigating to http://127.0.0.1:3000${urlPath}...`);
    await page.goto(`http://127.0.0.1:3000${urlPath}`, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(2500);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(300);
    await page.keyboard.press('Escape');
    await page.waitForTimeout(500);

    if (prepareFn) {
      try {
        await prepareFn(page);
      } catch (err) {
        console.warn(`[PREPARE WARNING for ${filename}]:`, err.message);
      }
    }

    const dest = path.join(ASSETS_DIR, filename);
    await page.screenshot({ path: dest, fullPage: false });
    console.log(`[CAPTURED] ${filename}`);
  };

  // 1. Telemedicine Consultation Studio
  await capture('/telemedicine', 'telemedicine-preview.png', async (p) => {
    await p.waitForTimeout(1000);
  });

  // 2. AI Clinical Copilot & Multi-Agent Assistant
  await capture('/chat', 'ai-clinical-chat-preview.png', async (p) => {
    await p.waitForTimeout(1000);
  });

  // 3. Multi-Organ Diagnostic Hub
  await capture('/predict/unified', 'ai-diagnostics-hub-preview.png', async (p) => {
    const btn = await p.$('button:has-text("Run"), button:has-text("Screening"), button:has-text("Predict")');
    if (btn) {
      await btn.click();
      await p.waitForTimeout(1200);
    }
  });

  // 4. Privacy-Preserving Federated Learning Studio
  await capture('/federated', 'federated-learning-preview.png', async (p) => {
    await p.waitForTimeout(1000);
  });

  // 5. ABDM Sandbox & WASM Edge AI
  await capture('/abdm', 'abdm-integration-preview.png', async (p) => {
    const abhaBtn = await p.$('button:has-text("Generate ABHA"), button:has-text("Create ABHA")');
    if (abhaBtn) {
      await abhaBtn.click();
      await p.waitForTimeout(800);
    }
    const wasmBtn = await p.$('button:has-text("Run Offline WASM"), button:has-text("Predict")');
    if (wasmBtn) {
      await wasmBtn.click();
      await p.waitForTimeout(800);
    }
  });

  // 6. Patient Companion Studio
  await capture('/companion', 'companion-preview.png', async (p) => {
    await p.waitForTimeout(1000);
  });

  // 7. Interactive BioTwin-X & Frontier Simulation Tour (Frames for Animated GIF)
  console.log('Capturing frames for Frontier / Digital Twin simulation walkthrough...');
  await page.goto('http://127.0.0.1:3000/frontier', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(2000);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(500);

  // Frame 1: BioTwin-X baseline trajectory
  await page.screenshot({ path: path.join(FRAMES_DIR, 'frame_01.png'), fullPage: false });
  console.log('[FRAME 1] BioTwin-X Baseline Trajectory');

  // Frame 2: Trigger simulation / intervention change
  const simBtn = await page.$('button:has-text("Run BioTwin-X Simulation"), button:has-text("Simulation")');
  if (simBtn) {
    await simBtn.click();
    await page.waitForTimeout(400);
    await page.screenshot({ path: path.join(FRAMES_DIR, 'frame_02.png'), fullPage: false });
    console.log('[FRAME 2] Simulation Execution');
    await page.waitForTimeout(1200);
    await page.screenshot({ path: path.join(FRAMES_DIR, 'frame_03.png'), fullPage: false });
    console.log('[FRAME 3] Counterfactual Stabilization');
  }

  // Frame 4: Causal Inference tab
  const causalTab = await page.$('button:has-text("Causal"), button:has-text("ITE / E-Value")');
  if (causalTab) {
    await causalTab.click();
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(FRAMES_DIR, 'frame_04.png'), fullPage: false });
    console.log('[FRAME 4] Counterfactual Causal Inference Studio');
  }

  // Frame 5: Cybernetics & Lyapunov Infusion tab
  const cyberTab = await page.$('button:has-text("Cybernetics"), button:has-text("Lyapunov")');
  if (cyberTab) {
    await cyberTab.click();
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(FRAMES_DIR, 'frame_05.png'), fullPage: false });
    console.log('[FRAME 5] Closed-Loop Cybernetic Infusion Control');
  }

  // Frame 6: High-Frequency Waveforms tab
  const waveTab = await page.$('button:has-text("Waveforms"), button:has-text("High-Frequency")');
  if (waveTab) {
    await waveTab.click();
    await page.waitForTimeout(1000);
    await page.screenshot({ path: path.join(FRAMES_DIR, 'frame_06.png'), fullPage: false });
    console.log('[FRAME 6] High-Frequency Waveform Monitor');
  }

  await browser.close();
  console.log('All captures and frames completed successfully!');
})();
