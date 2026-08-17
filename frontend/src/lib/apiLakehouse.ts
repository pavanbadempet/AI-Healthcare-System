import { apiFetch } from './apiCore';

export interface OmopPatientPayload {
  patient_id: string;
  year_of_birth: number;
  gender: string;
  conditions: string[];
  medications: string[];
  vitals: Record<string, unknown>;
}

export interface OmopTransformResult {
  PERSON: Record<string, unknown>;
  VISIT_OCCURRENCE: Record<string, unknown>;
  CONDITION_OCCURRENCE: Record<string, unknown>[];
  DRUG_EXPOSURE: Record<string, unknown>[];
  MEASUREMENT: Record<string, unknown>[];
}

export interface QualityAuditResult {
  summary: {
    total_records: number;
    clean_records: number;
    quarantined_records: number;
    pass_rate: number;
  };
  clean_sample: Record<string, unknown>[];
  quarantined_sample: Record<string, unknown>[];
}

export interface DeltaCommitLog {
  version: number;
  timestamp: string;
  operation: string;
  operation_parameters: Record<string, unknown>;
  user_metadata?: string;
  read_version?: number;
}

export interface LakehouseSqlResult {
  columns: string[];
  rows: Record<string, unknown>[];
  total_count: number;
  execution_time_ms: number;
}

export interface AgenticBiResult {
  question: string;
  generated_sql: string;
  result: Record<string, unknown>[];
  insights: string;
  confidence: number;
}

export function transformToOmop(payload: OmopPatientPayload): Promise<OmopTransformResult> {
  return apiFetch('/lakehouse/omop/transform', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export function auditDataQuality(records: Record<string, unknown>[]): Promise<QualityAuditResult> {
  return apiFetch('/lakehouse/quality/audit', {
    method: 'POST',
    body: JSON.stringify({ records }),
  });
}

export function getDeltaHistory(tableName: string = 'workspace.healthcare_silver.patients'): Promise<DeltaCommitLog[]> {
  return apiFetch(`/lakehouse/delta/history?table_name=${encodeURIComponent(tableName)}`);
}

export function queryDeltaTimeTravel(
  tableName: string = 'workspace.healthcare_silver.patients',
  targetVersion: number = 0
): Promise<{ table_name: string; version: number; data: Record<string, unknown>[]; row_count: number }> {
  return apiFetch('/lakehouse/delta/time-travel', {
    method: 'POST',
    body: JSON.stringify({ table_name: tableName, target_version: targetVersion }),
  });
}

export function executeLakehouseSql(sql: string): Promise<LakehouseSqlResult> {
  return apiFetch('/api/v1/data-platform/sql/execute', {
    method: 'POST',
    body: JSON.stringify({ sql }),
  });
}

export function askAgenticBi(question: string): Promise<AgenticBiResult> {
  return apiFetch('/api/v1/data-platform/bi/ask', {
    method: 'POST',
    body: JSON.stringify({ question }),
  });
}
