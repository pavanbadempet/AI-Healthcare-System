
import PredictionForm from "@/components/predict/PredictionForm";
import { predictHeart } from "@/lib/api";

const HEART_FIELDS = [
  { name: "age", label: "Age", type: "number" as const, min: 1, max: 120 },
  { name: "sex", label: "Sex", type: "select" as const, options: [{ label: "Male", value: 1 }, { label: "Female", value: 0 }] },
  { name: "cp", label: "Chest Pain Type", type: "select" as const, options: [
      { label: "Typical Angina", value: 0 },
      { label: "Atypical Angina", value: 1 },
      { label: "Non-anginal Pain", value: 2 },
      { label: "Asymptomatic", value: 3 }
  ]},
  { name: "trestbps", label: "Resting Blood Pressure", type: "number" as const, min: 50, max: 250, tooltip: "Resting blood pressure (in mm Hg on admission to the hospital)" },
  { name: "chol", label: "Cholesterol", type: "number" as const, min: 100, max: 600, tooltip: "Serum cholesterol in mg/dl" },
  { name: "fbs", label: "Fasting Blood Sugar > 120 mg/dl", type: "select" as const, options: [{ label: "True", value: 1 }, { label: "False", value: 0 }] },
  { name: "restecg", label: "Resting ECG Results", type: "select" as const, options: [
      { label: "Normal", value: 0 },
      { label: "ST-T wave abnormality", value: 1 },
      { label: "Probable/definite left ventricular hypertrophy", value: 2 }
  ]},
  { name: "thalach", label: "Max Heart Rate", type: "number" as const, min: 60, max: 220, tooltip: "Maximum heart rate achieved" },
  { name: "exang", label: "Exercise Induced Angina", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
  { name: "oldpeak", label: "ST Depression", type: "number" as const, min: 0, max: 10, step: 0.1, tooltip: "ST depression induced by exercise relative to rest" },
  { name: "slope", label: "Slope of Peak Exercise ST Segment", type: "select" as const, options: [
      { label: "Upsloping", value: 0 },
      { label: "Flat", value: 1 },
      { label: "Downsloping", value: 2 }
  ]},
  { name: "ca", label: "Number of Major Vessels", type: "select" as const, options: [
      { label: "0", value: 0 }, { label: "1", value: 1 }, { label: "2", value: 2 }, { label: "3", value: 3 }, { label: "4", value: 4 }
  ], tooltip: "Number of major vessels (0-3) colored by fluoroscopy" },
  { name: "thal", label: "Thalassemia", type: "select" as const, options: [
      { label: "Normal", value: 1 },
      { label: "Fixed Defect", value: 2 },
      { label: "Reversable Defect", value: 3 }
  ]}
];

export default function HeartPage() {
  return (
    <div className="py-8">
      <PredictionForm
        title="Heart Disease Risk Assessment"
        description="Enter the patient's cardiovascular parameters. The model evaluates 13 clinical features to predict the presence of heart disease."
        fields={HEART_FIELDS}
        onSubmit={predictHeart}
      />
    </div>
  );
}
