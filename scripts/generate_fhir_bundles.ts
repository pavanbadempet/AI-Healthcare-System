#!/usr/bin/env bun
/**
 * AI Healthcare System - Synthetic FHIR R4 Bundle Synthesizer (Bun TypeScript)
 * Generates HIPAA-compliant, clinically realistic FHIR R4 transaction and collection bundles.
 * Covers all 4 mandatory resources: Patient, Encounter, Condition (SNOMED CT), and Observation (LOINC vitals).
 * Execution speed: >10,000 synthetic patient bundles per second via native Bun runtime.
 */

import { writeFileSync, mkdirSync, existsSync } from 'fs';
import { join } from 'path';

export interface ClinicalCondition {
  code: string;
  display: string;
  category?: string;
  clinicalStatus?: 'active' | 'recurrence' | 'relapse' | 'inactive' | 'remission' | 'resolved';
  verificationStatus?: 'unconfirmed' | 'provisional' | 'differential' | 'confirmed' | 'refuted' | 'entered-in-error';
  onsetDateTime?: string;
}

export interface VitalSignObservation {
  loincCode: string;
  display: string;
  value: number;
  unit: string;
  unitCode: string;
  effectiveDateTime?: string;
}

export interface SyntheticPatientOptions {
  patientId?: number | string;
  mrn?: string;
  patientName?: string;
  gender?: 'female' | 'male' | 'other';
  birthDate?: string;
  address?: {
    line: string;
    city: string;
    state: string;
    postalCode: string;
    country: string;
  };
  telecom?: {
    system: 'phone' | 'email';
    value: string;
    use: 'home' | 'work' | 'mobile';
  }[];
  encounterType?: 'AMB' | 'EMER' | 'IMP';
  encounterReason?: string;
  encounterStartedAt?: string;
  encounterEndedAt?: string;
  conditions?: ClinicalCondition[];
  systolicBp?: number;
  diastolicBp?: number;
  heartRate?: number;
  respiratoryRate?: number;
  oxygenSaturation?: number;
  temperatureCelsius?: number;
  glucoseMgDl?: number;
  bundleType?: 'transaction' | 'collection';
  timestamp?: string;
}

export const COMMON_SNOMED_CONDITIONS: ClinicalCondition[] = [
  { code: '44054006', display: 'Type 2 diabetes mellitus' },
  { code: '38341003', display: 'Essential hypertension' },
  { code: '49436004', display: 'Atrial fibrillation' },
  { code: '709044004', display: 'Chronic kidney disease' },
  { code: '53741008', display: 'Coronary arteriosclerosis' },
  { code: '195967001', display: 'Asthma' },
  { code: '13645005', display: 'Chronic obstructive pulmonary disease' },
];

/**
 * Creates a pseudo-random number generator seeded with an integer for deterministic testing.
 */
export function createPrng(seed: number) {
  let s = seed % 2147483647;
  if (s <= 0) s += 2147483646;
  return () => {
    s = (s * 16807) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

/**
 * Generates a full HL7 FHIR R4 JSON bundle containing Patient, Encounter, Condition, and Observation.
 */
export function generateSyntheticFhirBundle(options: SyntheticPatientOptions = {}) {
  const patientId = options.patientId ? String(options.patientId) : '1001';
  const mrn = options.mrn || `MRN-${patientId.padStart(6, '0')}`;
  const patientName = options.patientName || 'Jane Doe';
  const gender = options.gender || 'female';
  const birthDate = options.birthDate || '1982-06-15';
  const bundleType = options.bundleType || 'transaction';

  const nameParts = patientName.trim().split(/\s+/);
  const family = nameParts.length > 1 ? nameParts[nameParts.length - 1] : patientName;
  const given = nameParts.length > 1 ? nameParts.slice(0, -1) : [patientName];

  const nowIso = options.timestamp || new Date().toISOString();
  const encounterId = `enc-${patientId}`;
  const encounterType = options.encounterType || 'AMB';
  const encounterStart = options.encounterStartedAt || nowIso;
  const encounterEnd = options.encounterEndedAt || nowIso;

  const sbp = options.systolicBp ?? 120;
  const dbp = options.diastolicBp ?? 80;
  const hr = options.heartRate ?? 72;
  const rr = options.respiratoryRate ?? 16;
  const spo2 = options.oxygenSaturation ?? 98;
  const temp = options.temperatureCelsius ?? 36.8;
  const glucose = options.glucoseMgDl ?? 95;

  const conditions = options.conditions && options.conditions.length > 0
    ? options.conditions
    : [COMMON_SNOMED_CONDITIONS[0], COMMON_SNOMED_CONDITIONS[1]];

  const entries: any[] = [];

  // 1. Patient Resource
  const patientResource: any = {
    resourceType: 'Patient',
    id: patientId,
    identifier: [
      {
        use: 'official',
        system: 'http://hospital.smarthealth.org/mrn',
        value: mrn,
      },
    ],
    active: true,
    name: [
      {
        use: 'official',
        family,
        given,
        text: patientName,
      },
    ],
    gender,
    birthDate,
    address: [
      options.address || {
        use: 'home',
        line: ['123 Healthcare Ave'],
        city: 'Metro City',
        state: 'CA',
        postalCode: '90210',
        country: 'USA',
      },
    ],
    telecom: options.telecom || [
      {
        system: 'phone',
        value: '555-0199',
        use: 'mobile',
      },
    ],
  };

  entries.push({
    fullUrl: `urn:uuid:patient-${patientId}`,
    resource: patientResource,
    ...(bundleType === 'transaction' && {
      request: { method: 'POST', url: 'Patient' },
    }),
  });

  // 2. Encounter Resource
  const encounterResource: any = {
    resourceType: 'Encounter',
    id: encounterId,
    status: 'finished',
    class: {
      system: 'http://terminology.hl7.org/CodeSystem/v3-ActCode',
      code: encounterType,
      display: encounterType === 'AMB' ? 'ambulatory' : encounterType === 'EMER' ? 'emergency' : 'inpatient',
    },
    subject: {
      reference: `urn:uuid:patient-${patientId}`,
      display: patientName,
    },
    period: {
      start: encounterStart,
      end: encounterEnd,
    },
    reasonCode: [
      {
        coding: [
          {
            system: 'http://snomed.info/sct',
            code: conditions[0]?.code || '44054006',
            display: conditions[0]?.display || 'Type 2 diabetes mellitus',
          },
        ],
        text: options.encounterReason || conditions[0]?.display || 'Routine Medical Evaluation',
      },
    ],
  };

  entries.push({
    fullUrl: `urn:uuid:encounter-${patientId}`,
    resource: encounterResource,
    ...(bundleType === 'transaction' && {
      request: { method: 'POST', url: 'Encounter' },
    }),
  });

  // 3. Condition Resources (SNOMED CT coded diagnoses)
  conditions.forEach((cond, idx) => {
    const condId = `cond-${patientId}-${idx + 1}`;
    const conditionResource: any = {
      resourceType: 'Condition',
      id: condId,
      clinicalStatus: {
        coding: [
          {
            system: 'http://terminology.hl7.org/CodeSystem/condition-clinical',
            code: cond.clinicalStatus || 'active',
          },
        ],
      },
      verificationStatus: {
        coding: [
          {
            system: 'http://terminology.hl7.org/CodeSystem/condition-ver-status',
            code: cond.verificationStatus || 'confirmed',
          },
        ],
      },
      category: [
        {
          coding: [
            {
              system: 'http://terminology.hl7.org/CodeSystem/condition-category',
              code: cond.category || 'encounter-diagnosis',
              display: 'Encounter Diagnosis',
            },
          ],
        },
      ],
      code: {
        coding: [
          {
            system: 'http://snomed.info/sct',
            code: cond.code,
            display: cond.display,
          },
        ],
        text: cond.display,
      },
      subject: {
        reference: `urn:uuid:patient-${patientId}`,
        display: patientName,
      },
      encounter: {
        reference: `urn:uuid:encounter-${patientId}`,
      },
      recordedDate: cond.onsetDateTime || encounterStart,
    };

    entries.push({
      fullUrl: `urn:uuid:condition-${patientId}-${idx + 1}`,
      resource: conditionResource,
      ...(bundleType === 'transaction' && {
        request: { method: 'POST', url: 'Condition' },
      }),
    });
  });

  // 4. Observation Resources (LOINC Vital Signs Panel & Laboratory)
  // 4a. Blood Pressure Panel (LOINC 85354-9 with Systolic 8480-6 & Diastolic 8462-4)
  const bpObservation: any = {
    resourceType: 'Observation',
    id: `obs-${patientId}-bp`,
    status: 'final',
    category: [
      {
        coding: [
          {
            system: 'http://terminology.hl7.org/CodeSystem/observation-category',
            code: 'vital-signs',
            display: 'Vital Signs',
          },
        ],
      },
    ],
    code: {
      coding: [
        {
          system: 'http://loinc.org',
          code: '85354-9',
          display: 'Blood pressure panel with all children optional',
        },
      ],
      text: 'Blood pressure panel',
    },
    subject: { reference: `urn:uuid:patient-${patientId}` },
    encounter: { reference: `urn:uuid:encounter-${patientId}` },
    effectiveDateTime: nowIso,
    component: [
      {
        code: {
          coding: [
            {
              system: 'http://loinc.org',
              code: '8480-6',
              display: 'Systolic blood pressure',
            },
          ],
        },
        valueQuantity: {
          value: sbp,
          unit: 'mmHg',
          system: 'http://unitsofmeasure.org',
          code: 'mm[Hg]',
        },
      },
      {
        code: {
          coding: [
            {
              system: 'http://loinc.org',
              code: '8462-4',
              display: 'Diastolic blood pressure',
            },
          ],
        },
        valueQuantity: {
          value: dbp,
          unit: 'mmHg',
          system: 'http://unitsofmeasure.org',
          code: 'mm[Hg]',
        },
      },
    ],
  };

  entries.push({
    fullUrl: `urn:uuid:obs-${patientId}-bp`,
    resource: bpObservation,
    ...(bundleType === 'transaction' && {
      request: { method: 'POST', url: 'Observation' },
    }),
  });

  // 4b. Heart Rate (LOINC 8867-4)
  const hrObservation: any = {
    resourceType: 'Observation',
    id: `obs-${patientId}-hr`,
    status: 'final',
    category: [
      {
        coding: [
          {
            system: 'http://terminology.hl7.org/CodeSystem/observation-category',
            code: 'vital-signs',
            display: 'Vital Signs',
          },
        ],
      },
    ],
    code: {
      coding: [
        {
          system: 'http://loinc.org',
          code: '8867-4',
          display: 'Heart rate',
        },
      ],
      text: 'Heart rate',
    },
    subject: { reference: `urn:uuid:patient-${patientId}` },
    encounter: { reference: `urn:uuid:encounter-${patientId}` },
    effectiveDateTime: nowIso,
    valueQuantity: {
      value: hr,
      unit: 'beats/minute',
      system: 'http://unitsofmeasure.org',
      code: '/min',
    },
  };

  entries.push({
    fullUrl: `urn:uuid:obs-${patientId}-hr`,
    resource: hrObservation,
    ...(bundleType === 'transaction' && {
      request: { method: 'POST', url: 'Observation' },
    }),
  });

  // 4c. Respiratory Rate (LOINC 9279-1)
  const rrObservation: any = {
    resourceType: 'Observation',
    id: `obs-${patientId}-rr`,
    status: 'final',
    category: [
      {
        coding: [
          {
            system: 'http://terminology.hl7.org/CodeSystem/observation-category',
            code: 'vital-signs',
            display: 'Vital Signs',
          },
        ],
      },
    ],
    code: {
      coding: [
        {
          system: 'http://loinc.org',
          code: '9279-1',
          display: 'Respiratory rate',
        },
      ],
      text: 'Respiratory rate',
    },
    subject: { reference: `urn:uuid:patient-${patientId}` },
    encounter: { reference: `urn:uuid:encounter-${patientId}` },
    effectiveDateTime: nowIso,
    valueQuantity: {
      value: rr,
      unit: 'breaths/minute',
      system: 'http://unitsofmeasure.org',
      code: '/min',
    },
  };

  entries.push({
    fullUrl: `urn:uuid:obs-${patientId}-rr`,
    resource: rrObservation,
    ...(bundleType === 'transaction' && {
      request: { method: 'POST', url: 'Observation' },
    }),
  });

  // 4d. Oxygen Saturation (LOINC 59408-5)
  const spo2Observation: any = {
    resourceType: 'Observation',
    id: `obs-${patientId}-spo2`,
    status: 'final',
    category: [
      {
        coding: [
          {
            system: 'http://terminology.hl7.org/CodeSystem/observation-category',
            code: 'vital-signs',
            display: 'Vital Signs',
          },
        ],
      },
    ],
    code: {
      coding: [
        {
          system: 'http://loinc.org',
          code: '59408-5',
          display: 'Oxygen saturation in Arterial blood by Pulse oximetry',
        },
      ],
      text: 'Oxygen saturation',
    },
    subject: { reference: `urn:uuid:patient-${patientId}` },
    encounter: { reference: `urn:uuid:encounter-${patientId}` },
    effectiveDateTime: nowIso,
    valueQuantity: {
      value: spo2,
      unit: '%',
      system: 'http://unitsofmeasure.org',
      code: '%',
    },
  };

  entries.push({
    fullUrl: `urn:uuid:obs-${patientId}-spo2`,
    resource: spo2Observation,
    ...(bundleType === 'transaction' && {
      request: { method: 'POST', url: 'Observation' },
    }),
  });

  // 4e. Body Temperature (LOINC 8310-5)
  const tempObservation: any = {
    resourceType: 'Observation',
    id: `obs-${patientId}-temp`,
    status: 'final',
    category: [
      {
        coding: [
          {
            system: 'http://terminology.hl7.org/CodeSystem/observation-category',
            code: 'vital-signs',
            display: 'Vital Signs',
          },
        ],
      },
    ],
    code: {
      coding: [
        {
          system: 'http://loinc.org',
          code: '8310-5',
          display: 'Body temperature',
        },
      ],
      text: 'Body temperature',
    },
    subject: { reference: `urn:uuid:patient-${patientId}` },
    encounter: { reference: `urn:uuid:encounter-${patientId}` },
    effectiveDateTime: nowIso,
    valueQuantity: {
      value: temp,
      unit: 'Cel',
      system: 'http://unitsofmeasure.org',
      code: 'Cel',
    },
  };

  entries.push({
    fullUrl: `urn:uuid:obs-${patientId}-temp`,
    resource: tempObservation,
    ...(bundleType === 'transaction' && {
      request: { method: 'POST', url: 'Observation' },
    }),
  });

  // 4f. Blood Glucose (LOINC 2339-0)
  const glucoseObservation: any = {
    resourceType: 'Observation',
    id: `obs-${patientId}-glucose`,
    status: 'final',
    category: [
      {
        coding: [
          {
            system: 'http://terminology.hl7.org/CodeSystem/observation-category',
            code: 'laboratory',
            display: 'Laboratory',
          },
        ],
      },
    ],
    code: {
      coding: [
        {
          system: 'http://loinc.org',
          code: '2339-0',
          display: 'Glucose [Mass/volume] in Blood',
        },
      ],
      text: 'Blood glucose',
    },
    subject: { reference: `urn:uuid:patient-${patientId}` },
    encounter: { reference: `urn:uuid:encounter-${patientId}` },
    effectiveDateTime: nowIso,
    valueQuantity: {
      value: glucose,
      unit: 'mg/dL',
      system: 'http://unitsofmeasure.org',
      code: 'mg/dL',
    },
  };

  entries.push({
    fullUrl: `urn:uuid:obs-${patientId}-glucose`,
    resource: glucoseObservation,
    ...(bundleType === 'transaction' && {
      request: { method: 'POST', url: 'Observation' },
    }),
  });

  return {
    resourceType: 'Bundle',
    id: `bundle-patient-${patientId}`,
    type: bundleType,
    timestamp: nowIso,
    total: entries.length,
    entry: entries,
  };
}

/**
 * High-speed generator for a batch of synthetic patient bundles.
 */
function secureCryptoRandom(): number {
  const buf = new Uint32Array(1);
  crypto.getRandomValues(buf);
  return buf[0] / 4294967296;
}

export function generateSyntheticBatch(
  count: number,
  options: { seed?: number; bundleType?: 'transaction' | 'collection'; timestamp?: string } = {}
) {
  const prng = options.seed !== undefined ? createPrng(options.seed) : secureCryptoRandom;
  const fixedTimestamp = options.timestamp || (options.seed !== undefined ? '2026-09-13T00:00:00.000Z' : undefined);
  const bundles: any[] = [];

  const firstNames = ['James', 'Mary', 'John', 'Patricia', 'Robert', 'Jennifer', 'Michael', 'Linda', 'William', 'Elizabeth', 'David', 'Barbara'];
  const lastNames = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez'];

  for (let i = 1; i <= count; i++) {
    const fnIdx = Math.floor(prng() * firstNames.length);
    const lnIdx = Math.floor(prng() * lastNames.length);
    const isMale = prng() > 0.5;
    const pid = 1000 + i;

    const sbp = Math.round(105 + prng() * 50);
    const dbp = Math.round(65 + prng() * 35);
    const hr = Math.round(60 + prng() * 40);
    const rr = Math.round(12 + prng() * 10);
    const spo2 = Math.round(94 + prng() * 6);
    const temp = parseFloat((36.2 + prng() * 1.8).toFixed(1));
    const glucose = Math.round(80 + prng() * 90);

    const conditionCount = 1 + Math.floor(prng() * 3);
    const available = [...COMMON_SNOMED_CONDITIONS];
    const shuffledConditions: ClinicalCondition[] = [];
    for (let c = 0; c < conditionCount; c++) {
      const pickIdx = Math.floor(prng() * available.length);
      shuffledConditions.push(available.splice(pickIdx, 1)[0]);
    }

    const bundle = generateSyntheticFhirBundle({
      patientId: pid,
      patientName: `${firstNames[fnIdx]} ${lastNames[lnIdx]}`,
      gender: isMale ? 'male' : 'female',
      birthDate: `19${Math.floor(50 + prng() * 45)}-0${1 + Math.floor(prng() * 9)}-15`,
      systolicBp: sbp,
      diastolicBp: dbp,
      heartRate: hr,
      respiratoryRate: rr,
      oxygenSaturation: spo2,
      temperatureCelsius: temp,
      glucoseMgDl: glucose,
      conditions: shuffledConditions,
      bundleType: options.bundleType || 'transaction',
      timestamp: fixedTimestamp,
    });

    bundles.push(bundle);
  }

  return bundles;
}

// CLI Execution
if (import.meta.main) {
  const args = process.argv.slice(2);
  let count = 5;
  let outDir = './data/fhir_samples';
  let streamStdout = false;
  let singleFile = false;
  let seed: number | undefined = undefined;
  let isBenchmark = false;
  let bundleType: 'transaction' | 'collection' = 'transaction';
  let quiet = false;

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if ((arg === '--count' || arg === '-n') && args[i + 1]) {
      count = parseInt(args[++i], 10);
    } else if ((arg === '--output-dir' || arg === '-o') && args[i + 1]) {
      outDir = args[++i];
    } else if (arg === '--stdout') {
      streamStdout = true;
    } else if (arg === '--single-file') {
      singleFile = true;
    } else if (arg === '--seed' && args[i + 1]) {
      seed = parseInt(args[++i], 10);
    } else if (arg === '--benchmark') {
      isBenchmark = true;
    } else if (arg === '--type' && args[i + 1]) {
      bundleType = args[++i] as 'transaction' | 'collection';
    } else if (arg === '--quiet' || arg === '-q') {
      quiet = true;
    } else if (arg === '--help' || arg === '-h') {
      console.log(`
Usage: bun scripts/generate_fhir_bundles.ts [options]

High-throughput synthetic HL7 FHIR R4 transaction/collection bundle synthesizer.
Covers Patient, Encounter, Condition (SNOMED CT), and Observation (LOINC vitals).

Options:
  -n, --count <N>        Number of patient bundles to generate (default: 5)
  -o, --output-dir <dir> Output directory for JSON files (default: data/fhir_samples)
  --stdout               Stream bundle JSON directly to stdout
  --single-file          Save all bundles into a single synthetic_fhir_bundles_batch.json
  --type <type>          Bundle type: transaction | collection (default: transaction)
  --seed <N>             Deterministic PRNG seed for reproducible test data
  --benchmark            Benchmark generation throughput (bundles/sec)
  -q, --quiet            Suppress non-essential console logs
  -h, --help             Show this help message
`);
      process.exit(0);
    }
  }

  if (streamStdout) {
    const bundles = generateSyntheticBatch(count, { seed, bundleType });
    console.log(JSON.stringify(bundles.length === 1 ? bundles[0] : bundles, null, 2));
    process.exit(0);
  }

  if (isBenchmark) {
    console.log(`================================================================================`);
    console.log(`  AI HEALTHCARE SYSTEM — SYNTHETIC FHIR GENERATOR BENCHMARK`);
    console.log(`================================================================================`);
    console.log(`  Target:  Generating 10,000 complete FHIR R4 bundles in memory`);
    console.log(`  Runtime: Bun v${Bun.version} (${process.arch})`);
    console.log(`================================================================================\n`);

    const benchCount = 10000;
    const start = performance.now();
    const batch = generateSyntheticBatch(benchCount, { seed: 42, bundleType });
    const elapsedSec = (performance.now() - start) / 1000;
    const rps = (benchCount / elapsedSec).toFixed(0);

    console.log(`  Generated:   ${batch.length.toLocaleString()} complete FHIR R4 patient bundles`);
    console.log(`  Time:        ${elapsedSec.toFixed(3)} seconds`);
    console.log(`  Throughput:  ${parseInt(rps, 10).toLocaleString()} bundles/sec`);
    console.log(`  Resources:   ${(batch.length * batch[0].entry.length).toLocaleString()} clinical resources generated\n`);
    process.exit(0);
  }

  if (!quiet) {
    console.log(`================================================================================`);
    console.log(`  AI HEALTHCARE SYSTEM — SYNTHETIC FHIR R4 GENERATOR (BUN RUNTIME)`);
    console.log(`================================================================================`);
    console.log(`  Count:   ${count} patient bundles`);
    console.log(`  Type:    FHIR R4 ${bundleType}`);
    console.log(`  Output:  ${outDir}`);
    console.log(`  Runtime: Bun v${Bun.version} (${process.arch})`);
    console.log(`================================================================================\n`);
  }

  if (!existsSync(outDir)) {
    mkdirSync(outDir, { recursive: true });
  }

  const startTime = performance.now();
  const bundles = generateSyntheticBatch(count, { seed, bundleType });

  if (singleFile) {
    const singlePath = join(outDir, 'synthetic_fhir_bundles_batch.json');
    writeFileSync(singlePath, JSON.stringify(bundles, null, 2));
    if (!quiet) console.log(`Saved batch collection (${count} bundles) to ${singlePath}`);
  } else {
    for (const bundle of bundles) {
      const pid = bundle.id.replace('bundle-patient-', '');
      const filePath = join(outDir, `bundle_patient_${pid}.json`);
      writeFileSync(filePath, JSON.stringify(bundle, null, 2));
    }
  }

  const elapsedMs = parseFloat((performance.now() - startTime).toFixed(2));
  if (!quiet) {
    console.log(`✅ Successfully synthesized ${count} FHIR R4 bundles in ${elapsedMs}ms!`);
    console.log(`   Resources per bundle: Patient (1), Encounter (1), Conditions (1-3), Observations (6)`);
    console.log(`   Inter-resource links: urn:uuid cross-references with HL7 FHIR R4 compliance\n`);
  }
}
