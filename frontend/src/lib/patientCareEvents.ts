export const PATIENT_CARE_EVENTS_UPDATED = "patient-care-events-updated";

export interface PatientCareEventsUpdatedDetail {
  patientId: number;
}

export function notifyPatientCareEventsUpdated(patientId: number) {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent<PatientCareEventsUpdatedDetail>(
    PATIENT_CARE_EVENTS_UPDATED,
    { detail: { patientId } }
  ));
}

export function patientCareEventMatches(event: Event, patientId: number) {
  const detail = (event as CustomEvent<PatientCareEventsUpdatedDetail>).detail;
  return detail?.patientId === patientId;
}
