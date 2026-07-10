
import PredictionForm from "@/components/predict/PredictionForm";
import { predictDiabetes } from "@/lib/api";

const DIABETES_FIELDS = [
  { name: "gender", label: "Gender", type: "select" as const, options: [{ label: "Male", value: 1 }, { label: "Female", value: 0 }] , tooltip: "Biological sex of the patient" },
  { name: "age_bucket", label: "Age Group", type: "select" as const, tooltip: "Age group bracket", options: [ /* tooltip: "Age group bracket" */
    { label: "18-24", value: 1 }, { label: "25-29", value: 2 }, { label: "30-34", value: 3 },
    { label: "35-39", value: 4 }, { label: "40-44", value: 5 }, { label: "45-49", value: 6 },
    { label: "50-54", value: 7 }, { label: "55-59", value: 8 }, { label: "60-64", value: 9 },
    { label: "65-69", value: 10 }, { label: "70-74", value: 11 }, { label: "75-79", value: 12 },
    { label: "80+", value: 13 }
  ]},
  { name: "hypertension", label: "Hypertension", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] , tooltip: "Has the patient been diagnosed with hypertension (high blood pressure)?" },
  { name: "high_chol", label: "High Cholesterol", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] , tooltip: "Has the patient been diagnosed with high cholesterol?" },
  { name: "bmi", label: "BMI", type: "number" as const, min: 10, max: 70, step: 0.1 , tooltip: "Body Mass Index. Normal: 18.5-24.9. Overweight: 25-29.9. Obese: >= 30" },
  { name: "smoking_history", label: "Smoker", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] , tooltip: "Does the patient have a history of smoking?" },
  { name: "heart_disease", label: "Heart Disease/Attack", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] , tooltip: "Has the patient had a heart attack or coronary heart disease?" },
  { name: "physical_activity", label: "Physical Activity (past 30 days)", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] , tooltip: "Has the patient engaged in physical activity in the past 30 days?" },
  { name: "general_health", label: "General Health", type: "select" as const, tooltip: "Patient's self-reported general health", options: [ /* tooltip: "Patient's self-reported general health" */
    { label: "Excellent", value: 1 }, { label: "Very Good", value: 2 }, { label: "Good", value: 3 }, { label: "Fair", value: 4 }, { label: "Poor", value: 5 }
  ]},
];

const DIABETES_EXAMPLES = [
  {
    name: "Sarah W., 55F",
    description: "Annual physical. High BMI and cholesterol, but no cardiac history. Poor general health.",
    records: [
      { date: "2023-04-12", type: "Annual Physical", findings: "Patient reports feeling poorly generally. BMI calculated at 40." },
      { date: "2024-05-18", type: "Lab Results", findings: "High cholesterol noted. Blood pressure slightly elevated." },
      { date: "2025-08-05", type: "Follow-up", findings: "No improvement in BMI. Continues to report poor general health. Advised diet plan." }
    ],
    data: { hypertension: 1, high_chol: 1, bmi: 40, smoking_history: 1, heart_disease: 0, physical_activity: 0, general_health: 5, gender: 0, age_bucket: 9 }
  },
  {
    name: "Michael K., 58M",
    description: "Follow-up post myocardial infarction. Sedentary lifestyle with multiple comorbidities.",
    records: [
      { date: "2022-11-20", type: "Cardiology", findings: "Admitted for myocardial infarction. Stent placed successfully." },
      { date: "2024-03-10", type: "Primary Care", findings: "Patient remains sedentary. Hypertension and hyperlipidemia remain uncontrolled." },
      { date: "2025-06-15", type: "Follow-up", findings: "BMI 30. Patient complains of general malaise and poor health." }
    ],
    data: { hypertension: 1, high_chol: 1, bmi: 30, smoking_history: 1, heart_disease: 1, physical_activity: 0, general_health: 5, gender: 0, age_bucket: 9 }
  }
];

export default function DiabetesPage() {
  return (
    <div className="py-8">
      <PredictionForm
        title="Diabetes Risk Assessment"
        description="Enter the patient's vitals and laboratory results below. The ML model will analyze the data against the Pima Indians Diabetes Database patterns to predict the onset of diabetes."
        fields={DIABETES_FIELDS}
        onSubmit={predictDiabetes}
        exampleCases={DIABETES_EXAMPLES}
      />
    </div>
  );
}
