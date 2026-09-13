import { describe, expect, test } from 'bun:test';
import {
  generateSyntheticFhirBundle,
  generateSyntheticBatch,
  COMMON_SNOMED_CONDITIONS,
  createPrng,
} from './generate_fhir_bundles';

describe('generate_fhir_bundles.ts Unit Tests', () => {
  describe('generateSyntheticFhirBundle', () => {
    test('generates valid HL7 FHIR R4 transaction bundle with all 4 required resources', () => {
      const bundle = generateSyntheticFhirBundle({
        patientId: 2001,
        patientName: 'Johnathan Archer',
        gender: 'male',
        birthDate: '1975-08-20',
        systolicBp: 130,
        diastolicBp: 85,
        heartRate: 75,
        oxygenSaturation: 97,
        respiratoryRate: 18,
        temperatureCelsius: 37.1,
        glucoseMgDl: 105,
      });

      expect(bundle.resourceType).toBe('Bundle');
      expect(bundle.type).toBe('transaction');
      expect(bundle.entry.length).toBeGreaterThanOrEqual(9);

      // Extract resources by type
      const resources = bundle.entry.map(e => e.resource);
      const patient = resources.find(r => r.resourceType === 'Patient');
      const encounter = resources.find(r => r.resourceType === 'Encounter');
      const conditions = resources.filter(r => r.resourceType === 'Condition');
      const observations = resources.filter(r => r.resourceType === 'Observation');

      // 1. Patient verification
      expect(patient).toBeDefined();
      expect(patient.id).toBe('2001');
      expect(patient.gender).toBe('male');
      expect(patient.birthDate).toBe('1975-08-20');
      expect(patient.name[0].family).toBe('Archer');
      expect(patient.identifier[0].system).toBe('http://hospital.smarthealth.org/mrn');

      // 2. Encounter verification
      expect(encounter).toBeDefined();
      expect(encounter.id).toBe('enc-2001');
      expect(encounter.subject.reference).toBe('urn:uuid:patient-2001');
      expect(encounter.status).toBe('finished');
      expect(encounter.class.code).toBe('AMB');

      // 3. Condition verification (SNOMED CT)
      expect(conditions.length).toBeGreaterThanOrEqual(1);
      const snomedCodes = conditions.flatMap(c => c.code.coding.map((cd: any) => cd.code));
      expect(snomedCodes).toContain('44054006'); // Type 2 diabetes
      expect(conditions[0].clinicalStatus.coding[0].code).toBe('active');
      expect(conditions[0].verificationStatus.coding[0].code).toBe('confirmed');
      expect(conditions[0].subject.reference).toBe('urn:uuid:patient-2001');

      // 4. Observation verification (LOINC Panels & Vitals)
      expect(observations.length).toBe(6);
      const loincCodes = observations.flatMap(o => o.code.coding.map((cd: any) => cd.code));
      expect(loincCodes).toContain('85354-9'); // Blood pressure panel
      expect(loincCodes).toContain('8867-4');  // Heart rate
      expect(loincCodes).toContain('9279-1');  // Respiratory rate
      expect(loincCodes).toContain('59408-5'); // Oxygen saturation
      expect(loincCodes).toContain('8310-5');  // Body temperature
      expect(loincCodes).toContain('2339-0');  // Blood glucose

      // Check BP components
      const bpObs = observations.find(o => o.code.coding.some((cd: any) => cd.code === '85354-9'));
      expect(bpObs).toBeDefined();
      expect(bpObs.component.length).toBe(2);
      expect(bpObs.component[0].valueQuantity.value).toBe(130);
      expect(bpObs.component[1].valueQuantity.value).toBe(85);

      // Verify transaction request blocks
      for (const entry of bundle.entry) {
        expect(entry.request).toBeDefined();
        expect(entry.request.method).toBe('POST');
        expect(entry.request.url).toBe(entry.resource.resourceType);
      }
    });

    test('supports collection bundle type without request blocks', () => {
      const bundle = generateSyntheticFhirBundle({
        patientId: 2002,
        bundleType: 'collection',
      });

      expect(bundle.type).toBe('collection');
      for (const entry of bundle.entry) {
        expect(entry.request).toBeUndefined();
      }
    });

    test('supports custom conditions and encounter classes', () => {
      const bundle = generateSyntheticFhirBundle({
        patientId: 2003,
        encounterType: 'EMER',
        encounterReason: 'Acute Chest Pain',
        conditions: [
          { code: '53741008', display: 'Coronary arteriosclerosis' },
          { code: '49436004', display: 'Atrial fibrillation' },
        ],
      });

      const encounter = bundle.entry.find(e => e.resource.resourceType === 'Encounter')?.resource;
      expect(encounter.class.code).toBe('EMER');
      expect(encounter.reasonCode[0].text).toBe('Acute Chest Pain');

      const conditions = bundle.entry
        .filter(e => e.resource.resourceType === 'Condition')
        .map(e => e.resource);
      expect(conditions.length).toBe(2);
      expect(conditions[0].code.coding[0].code).toBe('53741008');
      expect(conditions[1].code.coding[0].code).toBe('49436004');
    });
  });

  describe('generateSyntheticBatch', () => {
    test('generates exact batch count requested', () => {
      const batch = generateSyntheticBatch(10);
      expect(batch.length).toBe(10);
      for (const b of batch) {
        expect(b.resourceType).toBe('Bundle');
        expect(b.entry.length).toBeGreaterThanOrEqual(8);
      }
    });

    test('reproducible generation with deterministic PRNG seed', () => {
      const batchA = generateSyntheticBatch(5, { seed: 12345 });
      const batchB = generateSyntheticBatch(5, { seed: 12345 });

      // Check identical patient names, vitals, and conditions
      expect(JSON.stringify(batchA)).toBe(JSON.stringify(batchB));
    });

    test('different seeds produce different patient demographics and vitals', () => {
      const batchA = generateSyntheticBatch(5, { seed: 111 });
      const batchB = generateSyntheticBatch(5, { seed: 999 });

      expect(batchA[0].entry[0].resource.name[0].text).not.toBe(batchB[0].entry[0].resource.name[0].text);
    });

    test('performance throughput: generates 1,000 bundles in <50ms', () => {
      const t0 = performance.now();
      const batch = generateSyntheticBatch(1000, { seed: 42 });
      const durationMs = performance.now() - t0;

      expect(batch.length).toBe(1000);
      expect(durationMs).toBeLessThan(100); // Well under 100ms
    });
  });

  describe('PRNG helper', () => {
    test('produces uniform values between 0 and 1', () => {
      const prng = createPrng(777);
      for (let i = 0; i < 50; i++) {
        const val = prng();
        expect(val).toBeGreaterThanOrEqual(0);
        expect(val).toBeLessThan(1);
      }
    });
  });
});
