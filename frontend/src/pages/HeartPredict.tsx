
import PredictionForm from "@/components/predict/PredictionForm";
import { predictHeart } from "@/lib/api";

const HEART_FIELDS = [
  { name: "age", label: "Age", type: "number" as const, min: 1, max: 120 , tooltip: "Patient's age in years" },
  { name: "sex", label: "Sex", type: "select" as const, options: [{ label: "Male", value: 1 }, { label: "Female", value: 0 }] , tooltip: "Biological sex of the patient" },
  { name: "cp", label: "Chest Pain Type", type: "select" as const, tooltip: "Type of chest pain experienced", options: [ /* tooltip: "Type of chest pain experienced" */
      { label: "Typical Angina", value: 0 },
      { label: "Atypical Angina", value: 1 },
      { label: "Non-anginal Pain", value: 2 },
      { label: "Asymptomatic", value: 3 }
  ]},
  { name: "trestbps", label: "Resting Blood Pressure", type: "number" as const, min: 50, max: 250 , tooltip: "Resting blood pressure (mm Hg). Normal: 90-120. Elevated: 120-129. High: >= 130" },
  { name: "chol", label: "Cholesterol", type: "number" as const, min: 100, max: 600 , tooltip: "Serum cholesterol (mg/dl). Normal: < 200. Borderline: 200-239. High: >= 240" },
  { name: "fbs", label: "Fasting Blood Sugar > 120 mg/dl", type: "select" as const, options: [{ label: "True", value: 1 }, { label: "False", value: 0 }] , tooltip: "Fasting blood sugar > 120 mg/dl (1 = true, 0 = false)" },
  { name: "restecg", label: "Resting ECG Results", type: "select" as const, tooltip: "Resting electrocardiographic results", options: [ /* tooltip: "Resting electrocardiographic results" */
      { label: "Normal", value: 0 },
      { label: "ST-T wave abnormality", value: 1 },
      { label: "Probable/definite left ventricular hypertrophy", value: 2 }
  ]},
  { name: "thalach", label: "Max Heart Rate", type: "number" as const, min: 60, max: 220 , tooltip: "Maximum heart rate achieved. Normal max is approx 220 minus age" },
  { name: "exang", label: "Exercise Induced Angina", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] , tooltip: "Exercise-induced angina (chest pain)" },
  { name: "oldpeak", label: "ST Depression", type: "number" as const, min: 0, max: 10, step: 0.1 , tooltip: "ST depression induced by exercise relative to rest. Normal: < 1.0" },
  { name: "slope", label: "Slope of Peak Exercise ST Segment", type: "select" as const, tooltip: "The slope of the peak exercise ST segment", options: [ /* tooltip: "The slope of the peak exercise ST segment" */
      { label: "Upsloping", value: 0 },
      { label: "Flat", value: 1 },
      { label: "Downsloping", value: 2 }
  ]},
  { name: "ca", label: "Number of Major Vessels", type: "select" as const, tooltip: "Number of major vessels (0-3) colored by fluoroscopy", options: [
      { label: "0", value: 0 }, { label: "1", value: 1 }, { label: "2", value: 2 }, { label: "3", value: 3 }, { label: "4", value: 4 }
  ] },
  { name: "thal", label: "Thalassemia", type: "select" as const, tooltip: "Thalassemia type (blood disorder)", options: [ /* tooltip: "Thalassemia type (blood disorder)" */
      { label: "Normal", value: 1 },
      { label: "Fixed Defect", value: 2 },
      { label: "Reversable Defect", value: 3 }
  ]}
];

const HEART_EXAMPLES = [
  {
    name: "Robert M., 67M",
    description: "Routine checkup. History of mild hypertension, asymptomatic.",
    records: [
      { date: "2023-01-15", type: "Annual Physical", findings: "Mild hypertension noted (140/90). Advised lifestyle changes.", data: { age: 65, sex: 1, cp: 3, trestbps: 140, chol: 220, fbs: 0, restecg: 0, thalach: 125, exang: 0, oldpeak: 0.0, slope: 0, ca: 0, thal: 1 } },
      { date: "2024-05-10", type: "Cardiology Consult", findings: "Patient reports feeling asymptomatic. Stress test ordered.", data: { age: 66, sex: 1, cp: 3, trestbps: 145, chol: 245, fbs: 0, restecg: 0, thalach: 118, exang: 0, oldpeak: 0.5, slope: 1, ca: 1, thal: 2 } },
      { date: "2025-06-22", type: "Stress Test", findings: "Exercise-induced angina present. ST depression 1.5mm.", data: { age: 67, sex: 1, cp: 0, trestbps: 160, chol: 286, fbs: 0, restecg: 0, thalach: 108, exang: 1, oldpeak: 1.5, slope: 1, ca: 3, thal: 2 } }
    ],
    data: { age: 67, sex: 1, cp: 0, trestbps: 160, chol: 286, fbs: 0, restecg: 0, thalach: 108, exang: 1, oldpeak: 1.5, slope: 1, ca: 3, thal: 2 }
  },
  {
    name: "James T., 63M",
    description: "Presents with severe atypical angina, high cholesterol, and elevated max heart rate.",
    records: [
      { date: "2023-11-05", type: "ER Visit", findings: "Presented with chest pain. EKG normal. Discharged with atypical angina diagnosis.", data: { age: 61, sex: 1, cp: 1, trestbps: 130, chol: 205, fbs: 0, restecg: 0, thalach: 140, exang: 0, oldpeak: 0.0, slope: 0, ca: 0, thal: 1 } },
      { date: "2024-02-14", type: "Lipid Panel", findings: "Cholesterol elevated at 233 mg/dL. Fasting blood sugar > 120.", data: { age: 62, sex: 1, cp: 2, trestbps: 135, chol: 233, fbs: 1, restecg: 0, thalach: 145, exang: 0, oldpeak: 1.0, slope: 0, ca: 0, thal: 1 } },
      { date: "2025-07-01", type: "Echocardiogram", findings: "No major vessel blockages (0). Normal LV function.", data: { age: 63, sex: 1, cp: 3, trestbps: 145, chol: 233, fbs: 1, restecg: 0, thalach: 150, exang: 0, oldpeak: 2.3, slope: 0, ca: 0, thal: 1 } }
    ],
    data: { age: 63, sex: 1, cp: 3, trestbps: 145, chol: 233, fbs: 1, restecg: 0, thalach: 150, exang: 0, oldpeak: 2.3, slope: 0, ca: 0, thal: 1 }
  }
];

export default function HeartPage() {
  return (
    <div className="py-8">
      <PredictionForm
        title="Heart Disease Risk Assessment"
        description="Enter the patient's cardiovascular parameters. The model evaluates 13 clinical features to predict the presence of heart disease."
        fields={HEART_FIELDS}
        onSubmit={predictHeart}
        exampleCases={HEART_EXAMPLES}
      />
    </div>
  );
}
