
import PredictionForm from "@/components/predict/PredictionForm";
import { predictLiver } from "@/lib/api";

const LIVER_FIELDS = [
  { name: "Age", label: "Age", type: "number" as const, min: 1, max: 120 },
  { name: "Gender", label: "Gender", type: "select" as const, options: [{ label: "Male", value: 1 }, { label: "Female", value: 0 }] },
  { name: "Total_Bilirubin", label: "Total Bilirubin", type: "number" as const, min: 0, max: 80, step: 0.1, tooltip: "Total Bilirubin (mg/dL)" },
  { name: "Direct_Bilirubin", label: "Direct Bilirubin", type: "number" as const, min: 0, max: 40, step: 0.1, tooltip: "Conjugated (Direct) Bilirubin (mg/dL)" },
  { name: "Alkaline_Phosphotase", label: "Alkaline Phosphatase", type: "number" as const, min: 0, max: 2500, tooltip: "ALP (IU/L)" },
  { name: "Alamine_Aminotransferase", label: "Alamine Aminotransferase", type: "number" as const, min: 0, max: 2500, tooltip: "SGPT / ALT (IU/L)" },
  { name: "Aspartate_Aminotransferase", label: "Aspartate Aminotransferase", type: "number" as const, min: 0, max: 3000, tooltip: "SGOT / AST (IU/L)" },
  { name: "Total_Proteins", label: "Total Proteins", type: "number" as const, min: 0, max: 15, step: 0.1, tooltip: "Total Proteins (g/dL)" },
  { name: "Albumin", label: "Albumin", type: "number" as const, min: 0, max: 10, step: 0.1, tooltip: "Albumin (g/dL)" },
  { name: "Albumin_and_Globulin_Ratio", label: "A/G Ratio", type: "number" as const, min: 0, max: 5, step: 0.01, tooltip: "Albumin and Globulin Ratio" },
];

export default function LiverPage() {
  return (
    <div className="py-8">
      <PredictionForm
        title="Liver Disease Risk Assessment"
        description="Enter the patient's hepatic function panel results. The AI model analyzes liver enzymes, bilirubin, and protein levels to predict potential liver disease."
        fields={LIVER_FIELDS}
        onSubmit={predictLiver}
      />
    </div>
  );
}
