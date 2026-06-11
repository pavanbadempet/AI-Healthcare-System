
import PredictionForm from "@/components/predict/PredictionForm";
import { predictDiabetes } from "@/lib/api";

const DIABETES_FIELDS = [
  { name: "gender", label: "Gender", type: "select" as const, options: [{ label: "Male", value: 1 }, { label: "Female", value: 0 }] },
  { name: "age_bucket", label: "Age Group", type: "select" as const, options: [
    { label: "18-24", value: 1 }, { label: "25-29", value: 2 }, { label: "30-34", value: 3 },
    { label: "35-39", value: 4 }, { label: "40-44", value: 5 }, { label: "45-49", value: 6 },
    { label: "50-54", value: 7 }, { label: "55-59", value: 8 }, { label: "60-64", value: 9 },
    { label: "65-69", value: 10 }, { label: "70-74", value: 11 }, { label: "75-79", value: 12 },
    { label: "80+", value: 13 }
  ]},
  { name: "hypertension", label: "Hypertension", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
  { name: "high_chol", label: "High Cholesterol", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
  { name: "bmi", label: "BMI", type: "number" as const, min: 10, max: 70, step: 0.1 },
  { name: "smoking_history", label: "Smoker", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
  { name: "heart_disease", label: "Heart Disease/Attack", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
  { name: "physical_activity", label: "Physical Activity (past 30 days)", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
  { name: "general_health", label: "General Health", type: "select" as const, options: [
    { label: "Excellent", value: 1 }, { label: "Very Good", value: 2 }, { label: "Good", value: 3 }, { label: "Fair", value: 4 }, { label: "Poor", value: 5 }
  ]},
];

export default function DiabetesPage() {
  return (
    <div className="py-8">
      <PredictionForm
        title="Diabetes Risk Assessment"
        description="Enter the patient's vitals and laboratory results below. The ML model will analyze the data against the Pima Indians Diabetes Database patterns to predict the onset of diabetes."
        fields={DIABETES_FIELDS}
        onSubmit={predictDiabetes}
      />
    </div>
  );
}
