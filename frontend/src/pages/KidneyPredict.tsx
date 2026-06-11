
import PredictionForm from "@/components/predict/PredictionForm";
import { predictKidney } from "@/lib/api";

const KIDNEY_FIELDS = [
  { name: "age", label: "Age", type: "number" as const, min: 1, max: 120 },
  { name: "bp", label: "Blood Pressure", type: "number" as const, min: 50, max: 200, tooltip: "Blood Pressure (mm/Hg)" },
  { name: "sg", label: "Specific Gravity", type: "select" as const, options: [
      { label: "1.005", value: 1.005 }, { label: "1.010", value: 1.010 }, 
      { label: "1.015", value: 1.015 }, { label: "1.020", value: 1.020 }, { label: "1.025", value: 1.025 }
  ]},
  { name: "al", label: "Albumin", type: "select" as const, options: [
      { label: "0", value: 0 }, { label: "1", value: 1 }, { label: "2", value: 2 }, { label: "3", value: 3 }, { label: "4", value: 4 }, { label: "5", value: 5 }
  ]},
  { name: "su", label: "Sugar", type: "select" as const, options: [
      { label: "0", value: 0 }, { label: "1", value: 1 }, { label: "2", value: 2 }, { label: "3", value: 3 }, { label: "4", value: 4 }, { label: "5", value: 5 }
  ]},
  { name: "rbc", label: "Red Blood Cells", type: "select" as const, options: [{ label: "Normal", value: 1 }, { label: "Abnormal", value: 0 }] },
  { name: "pc", label: "Pus Cell", type: "select" as const, options: [{ label: "Normal", value: 1 }, { label: "Abnormal", value: 0 }] },
  { name: "pcc", label: "Pus Cell Clumps", type: "select" as const, options: [{ label: "Present", value: 1 }, { label: "Not Present", value: 0 }] },
  { name: "ba", label: "Bacteria", type: "select" as const, options: [{ label: "Present", value: 1 }, { label: "Not Present", value: 0 }] },
  { name: "bgr", label: "Blood Glucose Random", type: "number" as const, min: 0, max: 500, tooltip: "Blood Glucose Random (mgs/dl)" },
  { name: "bu", label: "Blood Urea", type: "number" as const, min: 0, max: 400, tooltip: "Blood Urea (mgs/dl)" },
  { name: "sc", label: "Serum Creatinine", type: "number" as const, min: 0, max: 80, step: 0.1, tooltip: "Serum Creatinine (mgs/dl)" },
  { name: "sod", label: "Sodium", type: "number" as const, min: 0, max: 200, step: 0.1, tooltip: "Sodium (mEq/L)" },
  { name: "pot", label: "Potassium", type: "number" as const, min: 0, max: 50, step: 0.1, tooltip: "Potassium (mEq/L)" },
  { name: "hemo", label: "Hemoglobin", type: "number" as const, min: 0, max: 25, step: 0.1, tooltip: "Hemoglobin (gms)" },
  { name: "pcv", label: "Packed Cell Volume", type: "number" as const, min: 0, max: 60, tooltip: "Packed Cell Volume" },
  { name: "wc", label: "White Blood Cell Count", type: "number" as const, min: 0, max: 30000, tooltip: "White Blood Cell Count (cells/cumm)" },
  { name: "rc", label: "Red Blood Cell Count", type: "number" as const, min: 0, max: 10, step: 0.1, tooltip: "Red Blood Cell Count (millions/cmm)" },
  { name: "htn", label: "Hypertension", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
  { name: "dm", label: "Diabetes Mellitus", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
  { name: "cad", label: "Coronary Artery Disease", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
  { name: "appet", label: "Appetite", type: "select" as const, options: [{ label: "Good", value: 1 }, { label: "Poor", value: 0 }] },
  { name: "pe", label: "Pedal Edema", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
  { name: "ane", label: "Anemia", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
];

export default function KidneyPage() {
  return (
    <div className="py-8">
      <PredictionForm
        title="Chronic Kidney Disease Assessment"
        description="Enter the patient's urinalysis and comprehensive metabolic panel results. The AI will evaluate 24 indicators to predict Chronic Kidney Disease."
        fields={KIDNEY_FIELDS}
        onSubmit={predictKidney}
      />
    </div>
  );
}
