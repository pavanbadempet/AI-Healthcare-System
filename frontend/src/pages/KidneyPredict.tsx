
import PredictionForm from "@/components/predict/PredictionForm";
import { predictKidney } from "@/lib/api";

const KIDNEY_FIELDS = [
  { name: "age", label: "Age", type: "number" as const, min: 1, max: 120 , tooltip: "Patient's age in years" },
  { name: "bp", label: "Blood Pressure", type: "number" as const, min: 50, max: 200 , tooltip: "Blood Pressure (mm/Hg). Normal: 90-120. Elevated: 120-129. High: >= 130" },
  { name: "sg", label: "Specific Gravity", type: "select" as const, tooltip: "Specific Gravity. Normal range: 1.002 - 1.030", options: [ /* tooltip: "Specific Gravity. Normal range: 1.002 - 1.030" */
      { label: "1.005", value: 1.005 }, { label: "1.010", value: 1.010 }, 
      { label: "1.015", value: 1.015 }, { label: "1.020", value: 1.020 }, { label: "1.025", value: 1.025 }
  ]},
  { name: "al", label: "Albumin", type: "select" as const, tooltip: "Albumin in urine. Normal: 0. Scale: 0-5", options: [ /* tooltip: "Albumin in urine. Normal: 0. Scale: 0-5" */
      { label: "0", value: 0 }, { label: "1", value: 1 }, { label: "2", value: 2 }, { label: "3", value: 3 }, { label: "4", value: 4 }, { label: "5", value: 5 }
  ]},
  { name: "su", label: "Sugar", type: "select" as const, tooltip: "Sugar in urine. Normal: 0. Scale: 0-5", options: [ /* tooltip: "Sugar in urine. Normal: 0. Scale: 0-5" */
      { label: "0", value: 0 }, { label: "1", value: 1 }, { label: "2", value: 2 }, { label: "3", value: 3 }, { label: "4", value: 4 }, { label: "5", value: 5 }
  ]},
  { name: "rbc", label: "Red Blood Cells", type: "select" as const, options: [{ label: "Normal", value: 1 }, { label: "Abnormal", value: 0 }] },
  { name: "pc", label: "Pus Cell", type: "select" as const, options: [{ label: "Normal", value: 1 }, { label: "Abnormal", value: 0 }] },
  { name: "pcc", label: "Pus Cell Clumps", type: "select" as const, options: [{ label: "Present", value: 1 }, { label: "Not Present", value: 0 }] },
  { name: "ba", label: "Bacteria", type: "select" as const, options: [{ label: "Present", value: 1 }, { label: "Not Present", value: 0 }] },
  { name: "bgr", label: "Blood Glucose Random", type: "number" as const, min: 0, max: 500 , tooltip: "Blood Glucose Random (mgs/dl). Normal: 70-140" },
  { name: "bu", label: "Blood Urea", type: "number" as const, min: 0, max: 400 , tooltip: "Blood Urea (mgs/dl). Normal: 7-20" },
  { name: "sc", label: "Serum Creatinine", type: "number" as const, min: 0, max: 80, step: 0.1 , tooltip: "Serum Creatinine (mgs/dl). Normal: 0.74-1.35" },
  { name: "sod", label: "Sodium", type: "number" as const, min: 0, max: 200, step: 0.1 , tooltip: "Sodium (mEq/L). Normal: 135-145" },
  { name: "pot", label: "Potassium", type: "number" as const, min: 0, max: 50, step: 0.1 , tooltip: "Potassium (mEq/L). Normal: 3.6-5.2" },
  { name: "hemo", label: "Hemoglobin", type: "number" as const, min: 0, max: 25, step: 0.1 , tooltip: "Hemoglobin (gms). Normal: 12.0-17.2" },
  { name: "pcv", label: "Packed Cell Volume", type: "number" as const, min: 0, max: 60 , tooltip: "Packed Cell Volume (%). Normal: 36-50%" },
  { name: "wc", label: "White Blood Cell Count", type: "number" as const, min: 0, max: 30000 , tooltip: "White Blood Cell Count (cells/cumm). Normal: 4500-11000" },
  { name: "rc", label: "Red Blood Cell Count", type: "number" as const, min: 0, max: 10, step: 0.1 , tooltip: "Red Blood Cell Count (millions/cmm). Normal: 4.2-6.1" },
  { name: "htn", label: "Hypertension", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
  { name: "dm", label: "Diabetes Mellitus", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
  { name: "cad", label: "Coronary Artery Disease", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
  { name: "appet", label: "Appetite", type: "select" as const, options: [{ label: "Good", value: 1 }, { label: "Poor", value: 0 }] },
  { name: "pe", label: "Pedal Edema", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
  { name: "ane", label: "Anemia", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
];

const KIDNEY_EXAMPLES = [
  {
    name: "Healthy Profile",
    description: "Typical values for a healthy patient with normal kidney function.",
    data: { age: 40, bp: 80, sg: 1.020, al: 0, su: 0, rbc: 1, pc: 1, pcc: 0, ba: 0, bgr: 121, bu: 36, sc: 1.2, sod: 138, pot: 4.4, hemo: 15.4, pcv: 44, wc: 7800, rc: 5.2, htn: 0, dm: 0, cad: 0, appet: 1, pe: 0, ane: 0 }
  },
  {
    name: "High Risk Profile",
    description: "Typical values for a patient with severe chronic kidney disease indicators.",
    data: { age: 60, bp: 100, sg: 1.010, al: 4, su: 2, rbc: 0, pc: 0, pcc: 1, ba: 1, bgr: 210, bu: 90, sc: 6.5, sod: 125, pot: 6.8, hemo: 8.5, pcv: 25, wc: 12000, rc: 3.1, htn: 1, dm: 1, cad: 1, appet: 0, pe: 1, ane: 1 }
  }
];

export default function KidneyPage() {
  return (
    <div className="py-8">
      <PredictionForm
        title="Chronic Kidney Disease Assessment"
        description="Enter the patient's urinalysis and comprehensive metabolic panel results. The AI will evaluate 24 indicators to predict Chronic Kidney Disease."
        fields={KIDNEY_FIELDS}
        onSubmit={predictKidney}
        exampleCases={KIDNEY_EXAMPLES}
      />
    </div>
  );
}
