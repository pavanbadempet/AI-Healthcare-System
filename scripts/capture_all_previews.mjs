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

  // Universal mock route handler for zero-config preview capture
  await page.route('**/*', async (route) => {
    const url = route.request().url();

    // Patient records
    if (url.includes('/records')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { id: 1, patient_name: "Sarah Jenkins", model_type: "General Health", risk_level: "Low", created_at: "2026-09-17T10:00:00Z" },
          { id: 2, patient_name: "Marcus Thorne", model_type: "Cardiovascular", risk_level: "High", created_at: "2026-09-17T11:30:00Z" },
          { id: 3, patient_name: "Linda Zhao", model_type: "Diabetes", risk_level: "Low", created_at: "2026-09-17T12:15:00Z" },
          { id: 4, patient_name: "Robert Garcia", model_type: "Kidney CKD", risk_level: "Moderate", created_at: "2026-09-17T13:45:00Z" },
          { id: 5, patient_name: "Emily Watson", model_type: "Pulmonary", risk_level: "Low", created_at: "2026-09-17T14:20:00Z" }
        ])
      });
    }

    // Doctor & Admin Patient Registries
    if (url.includes('/doctor/patients') || url.includes('/admin/patients')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          { patient_id: 2, username: "sarah_jenkins", full_name: "Sarah Jenkins", email: "sarah@patient.local", role: "patient", latest_encounter_type: "ICU-A", latest_status: "active", open_orders: 2, active_admissions: 1 },
          { patient_id: 3, username: "marcus_thorne", full_name: "Marcus Thorne", email: "marcus@patient.local", role: "patient", latest_encounter_type: "Cardiac Care", latest_status: "active", open_orders: 4, active_admissions: 1 },
          { patient_id: 4, username: "linda_zhao", full_name: "Linda Zhao", email: "linda@patient.local", role: "patient", latest_encounter_type: "Med-Surg 4B", latest_status: "active", open_orders: 1, active_admissions: 1 },
          { patient_id: 5, username: "robert_g", full_name: "Robert Garcia", email: "robert@patient.local", role: "patient", latest_encounter_type: "Med-Surg 4B", latest_status: "active", open_orders: 3, active_admissions: 1 },
          { patient_id: 6, username: "emily_watson", full_name: "Emily Watson", email: "emily@patient.local", role: "patient", latest_encounter_type: "Pediatric Ward", latest_status: "active", open_orders: 1, active_admissions: 1 },
          { patient_id: 7, username: "oscar_meyer", full_name: "Oscar Meyer", email: "oscar@patient.local", role: "patient", latest_encounter_type: "ICU-A", latest_status: "active", open_orders: 2, active_admissions: 1 }
        ])
      });
    }

    // Triage Queue
    if (url.includes('/triage/queue')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          queue: [
            { patient_id: 11, full_name: "Patricia Moore", esi_level: 2, triage_reason: "Acute Dyspnea / Asthma Exacerbation", arrival_time: "12m ago" },
            { patient_id: 12, full_name: "Thomas Wright", esi_level: 3, triage_reason: "Hyperglycemia / Diabetic Ketosis Workup", arrival_time: "28m ago" },
            { patient_id: 13, full_name: "Clara Oswald", esi_level: 4, triage_reason: "Left Flank Pain / Suspected Nephrolithiasis", arrival_time: "45m ago" },
            { patient_id: 14, full_name: "George Bailey", esi_level: 5, triage_reason: "Minor Forearm Abrasion & Wound Dressing", arrival_time: "58m ago" }
          ]
        })
      });
    }

    // Telemetry Summary
    if (url.includes('/telemetry/summary')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          system_latency_ms: 2.8,
          active_census: 79,
          total_capacity: 100,
          ed_boarding: 18,
          ed_avg_wait_min: 145,
          pending_discharges: 12,
          confirmed_discharges: 6,
          surge_prediction_pct: 15,
          bed_units: [
            { unit: "ICU-A", total: 20, occupied: 16, cleaning: 1, available: 3 },
            { unit: "MED-SURG 4B", total: 40, occupied: 32, cleaning: 2, available: 6 },
            { unit: "CARDIAC", total: 16, occupied: 12, cleaning: 1, available: 3 },
            { unit: "PEDS", total: 24, occupied: 19, cleaning: 2, available: 3 },
          ]
        })
      });
    }

    // Clinical Alerts
    if (url.includes('/alerts')) {
      return route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 1,
            patient_id: 3,
            patient_name: "Marcus Thorne",
            alert_type: "CARDIAC_TACHYCARDIA",
            severity: "CRITICAL",
            message: "Acute Sinus Tachycardia (118 bpm) with anterior lead ST elevation (V2-V4). Bedside echocardiogram and serial troponin ordered.",
            acknowledged: 0,
            created_at: new Date().toISOString()
          },
          {
            id: 2,
            patient_id: 2,
            patient_name: "Sarah Jenkins",
            alert_type: "RESPIRATORY_HYPOXEMIA",
            severity: "WARNING",
            message: "Transient SpO2 desaturation (93%) on room air post-ambulation. Nasal cannula 2L/min initiated.",
            acknowledged: 1,
            created_at: new Date().toISOString()
          }
        ])
      });
    }

    // Chat History
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

    if (url.includes('/telemedicine/appointments') || url.includes('/appointments/')) {
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

    if (url.includes('/telemedicine/doctors') || url.includes('/appointments/doctors')) {
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

  // Set authenticated doctor session in localStorage
  await page.goto('http://127.0.0.1:3000/login');
  await page.evaluate(() => {
    localStorage.setItem('healthcare-auth', JSON.stringify({
      state: {
        token: 'mock-valid-jwt-token-for-preview',
        user: {
          id: 1,
          username: 'dr_sarah_lin',
          email: 'clinician@hospital.org',
          role: 'doctor',
          full_name: 'Dr. Sarah Lin, MD'
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

  // 1. Clinical Workstation & Operations Cockpit (Hero Dashboard)
  await capture('/dashboard', 'clinical-workstation-preview.png', async (p) => {
    await p.waitForTimeout(1000);
  });

  // 2. Patient Records Registry (Full EMR)
  await capture('/patients', 'patient-records-preview.png', async (p) => {
    await p.waitForTimeout(1000);
  });

  // 3. Admission Capacity & Hospital Bed Board
  await capture('/capacity', 'capacity-command-preview.png', async (p) => {
    await p.waitForTimeout(1000);
  });

  // 4. AI Clinical Copilot & Multi-Agent Assistant
  await capture('/chat', 'ai-clinical-chat-preview.png', async (p) => {
    await p.waitForTimeout(1000);
  });

  // 5. Clinical Intelligence & Decision Support Suite
  await capture('/intelligence', 'digital-twin-preview.png', async (p) => {
    await p.waitForTimeout(1000);
  });

  // 6. Autonomous Frontier & 10-Year Multi-Organ Digital Twin Trajectory
  await capture('/frontier', 'autonomous-frontier-preview.png', async (p) => {
    await p.waitForTimeout(1000);
  });

  // 7. Multi-Organ Diagnostic Hub (TabICLv2 + Conformal Prediction)
  await capture('/predict/unified', 'ai-diagnostics-hub-preview.png', async (p) => {
    await p.waitForTimeout(1000);
  });

  // 8. Telemedicine Consultation Studio
  await capture('/telemedicine', 'telemedicine-preview.png', async (p) => {
    await p.waitForTimeout(1000);
  });

  // 9. Bedside Patient Companion Studio
  await capture('/companion', 'companion-preview.png', async (p) => {
    await p.waitForTimeout(1000);
  });

  // 10. ABDM Sandbox, ABHA Health IDs, & WASM Edge AI
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

  // 11. Databricks Lakehouse & Medallion Data Engineering Platform
  await capture('/data-engineering', 'data-platform-preview.png', async (p) => {
    await p.waitForTimeout(1000);
  });

  // 12. Privacy-Preserving Federated Learning Studio
  await capture('/federated', 'federated-learning-preview.png', async (p) => {
    await p.waitForTimeout(1000);
  });

  // 13. Interactive BioTwin-X & Frontier Simulation Tour (Frames for Animated GIF)
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
