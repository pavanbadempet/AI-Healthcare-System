export interface PatientProfile {
  age: number;
  gender: string;
  weight: string;
  bloodType: string;
  allergies: string;
  history: string[];
  medications: string[];
  risks: {
    diabetes: number;
    heart: number;
    stroke: number;
  };
  recourse: string[];
  timeline: Array<{ time: string; event: string }>;
}

export const patientProfiles: Record<string, PatientProfile> = {
  "Sarah Jenkins": {
    age: 45,
    gender: "Female",
    weight: "64 kg",
    bloodType: "A+",
    allergies: "Sulfa drugs",
    history: ["No chronic illnesses", "Post-operative day 2 (Appendectomy)"],
    medications: ["Acetaminophen 500mg (PRN)", "Lactated Ringer's IV (100ml/hr)"],
    risks: { diabetes: 12, heart: 8, stroke: 5 },
    recourse: ["Maintain light walking post-op", "Hydration compliance"],
    timeline: [
      { time: "08:30 AM", event: "Vitals stable, normal sinus rhythm" },
      { time: "10:15 AM", event: "Patient ambulated 50 meters in hall" },
      { time: "02:00 PM", event: "Wound check: dressing dry & intact" },
    ],
  },
  "Marcus Thorne": {
    age: 68,
    gender: "Male",
    weight: "88 kg",
    bloodType: "O-",
    allergies: "Penicillin",
    history: ["Congestive Heart Failure", "Hypertension", "Type 2 Diabetes"],
    medications: ["Lisinopril 20mg Daily", "Metformin 1000mg BID", "Furosemide 40mg IV PRN"],
    risks: { diabetes: 82, heart: 76, stroke: 65 },
    recourse: [
      "Reduce systolic BP target to <130 mmHg",
      "Initiate low-sodium diet",
      "Daily weight tracking",
    ],
    timeline: [
      { time: "09:00 AM", event: "Complained of mild shortness of breath" },
      { time: "12:30 PM", event: "Furosemide administered IV" },
      { time: "04:15 PM", event: "SYS_ALARM_TACHY triggered (HR: 112)" },
    ],
  },
  "Linda Zhao": {
    age: 32,
    gender: "Female",
    weight: "58 kg",
    bloodType: "B+",
    allergies: "None",
    history: ["Asthma (mild intermittent)"],
    medications: ["Albuterol HFA inhaler (PRN)", "Fluticasone propionate (Daily)"],
    risks: { diabetes: 8, heart: 4, stroke: 2 },
    recourse: ["Maintain asthma action plan", "Monitor peak expiratory flow"],
    timeline: [
      { time: "07:45 AM", event: "Admitted with mild wheezing" },
      { time: "09:15 AM", event: "Nebulizer treatment completed" },
      { time: "01:30 PM", event: "Lungs clear on auscultation" },
    ],
  },
  "Robert G.": {
    age: 59,
    gender: "Male",
    weight: "92 kg",
    bloodType: "AB-",
    allergies: "Shellfish",
    history: ["Coronary Artery Disease", "Hyperlipidemia"],
    medications: ["Atorvastatin 40mg Daily", "Aspirin 81mg Daily"],
    risks: { diabetes: 42, heart: 58, stroke: 34 },
    recourse: [
      "Reduce LDL cholesterol target to <70 mg/dL",
      "Increase physical activity (150m/wk)",
    ],
    timeline: [
      { time: "08:00 AM", event: "Fasting lipid panel drawn" },
      { time: "11:00 AM", event: "Stress test scheduled for tomorrow" },
      { time: "03:45 PM", event: "ECG shows normal sinus rhythm" },
    ],
  },
};
