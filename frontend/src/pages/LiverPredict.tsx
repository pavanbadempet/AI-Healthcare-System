
import PredictionForm from "@/components/predict/PredictionForm";
import { predictLiver } from "@/lib/api";

const LIVER_FIELDS = [
  { name: "Age", label: "Age", type: "number" as const, min: 1, max: 120 , tooltip: "Patient's age in years" },
  { name: "Gender", label: "Gender", type: "select" as const, options: [{ label: "Male", value: 1 }, { label: "Female", value: 0 }] , tooltip: "Biological sex of the patient" },
  { name: "Total_Bilirubin", label: "Total Bilirubin", type: "number" as const, min: 0, max: 80, step: 0.1 , tooltip: "Total Bilirubin (mg/dL). Normal: 0.1-1.2" },
  { name: "Direct_Bilirubin", label: "Direct Bilirubin", type: "number" as const, min: 0, max: 40, step: 0.1 , tooltip: "Direct Bilirubin (mg/dL). Normal: < 0.3" },
  { name: "Alkaline_Phosphotase", label: "Alkaline Phosphatase", type: "number" as const, min: 0, max: 2500 , tooltip: "Alkaline Phosphatase (IU/L). Normal: 44-147" },
  { name: "Alamine_Aminotransferase", label: "Alamine Aminotransferase", type: "number" as const, min: 0, max: 2500 , tooltip: "ALT (U/L). Normal: 7-56" },
  { name: "Aspartate_Aminotransferase", label: "Aspartate Aminotransferase", type: "number" as const, min: 0, max: 3000 , tooltip: "AST (U/L). Normal: 10-40" },
  { name: "Total_Proteins", label: "Total Proteins", type: "number" as const, min: 0, max: 15, step: 0.1 , tooltip: "Total Proteins (g/dL). Normal: 6.0-8.3" },
  { name: "Albumin", label: "Albumin", type: "number" as const, min: 0, max: 10, step: 0.1 , tooltip: "Albumin (g/dL). Normal: 3.4-5.4" },
  { name: "Albumin_and_Globulin_Ratio", label: "A/G Ratio", type: "number" as const, min: 0, max: 5, step: 0.01 , tooltip: "A/G Ratio. Normal: 1.1-2.5" },
];

const LIVER_EXAMPLES = [
  {
    name: "Patient Record #121 (Negative)",
    description: "Actual record from the ILPD dataset (Target: 2 - Healthy)",
    data: { Age: 17, Gender: 1, Total_Bilirubin: 0.9, Direct_Bilirubin: 0.3, Alkaline_Phosphotase: 202, Alamine_Aminotransferase: 22, Aspartate_Aminotransferase: 19, Total_Proteins: 7.4, Albumin: 4.1, Albumin_and_Globulin_Ratio: 1.2 }
  },
  {
    name: "Patient Record #13 (Positive)",
    description: "Actual record from the ILPD dataset (Target: 1 - Disease)",
    data: { Age: 65, Gender: 0, Total_Bilirubin: 0.7, Direct_Bilirubin: 0.1, Alkaline_Phosphotase: 187, Alamine_Aminotransferase: 16, Aspartate_Aminotransferase: 18, Total_Proteins: 6.8, Albumin: 3.3, Albumin_and_Globulin_Ratio: 0.9 }
  }
];

export default function LiverPage() {
  return (
    <div className="py-8">
      <PredictionForm
        title="Liver Disease Risk Assessment"
        description="Enter the patient's hepatic function panel results. The AI model analyzes liver enzymes, bilirubin, and protein levels to predict potential liver disease."
        fields={LIVER_FIELDS}
        onSubmit={predictLiver}
        exampleCases={LIVER_EXAMPLES}
      />
    </div>
  );
}
