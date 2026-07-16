import { 
  predictDiabetes, 
  predictHeart, 
  predictLiver, 
  predictKidney, 
  predictLungs 
} from "@/lib/api";

export interface FieldOption {
  label: string;
  value: number;
}

export interface PredictionField {
  name: string;
  label: string;
  type: "number" | "select";
  min?: number;
  max?: number;
  step?: number;
  tooltip?: string;
  options?: FieldOption[];
}

export interface ExampleRecord {
  date: string;
  type: string;
  findings: string;
  data?: Record<string, number>;
}

export interface ExampleCase {
  name: string;
  description: string;
  records: ExampleRecord[];
  data: Record<string, number>;
}

export interface ModelConfig {
  title: string;
  description: string;
  fields: PredictionField[];
  onSubmit: (data: any) => Promise<any>;
  exampleCases: ExampleCase[];
  modelName: string;
}

export const PREDICT_CONFIGS: Record<string, ModelConfig> = {
  diabetes: {
    title: "Diabetes Risk Assessment",
    description: "Enter the patient's vitals and laboratory results below. The ML model will analyze the data against the Pima Indians Diabetes Database patterns to predict the onset of diabetes.",
    modelName: "diabetes",
    onSubmit: predictDiabetes,
    fields: [
      { name: "gender", label: "Gender", type: "select", options: [{ label: "Male", value: 1 }, { label: "Female", value: 0 }] , tooltip: "Biological sex of the patient" },
      { name: "age_bucket", label: "Age Group", type: "select", tooltip: "Age group bracket", options: [
        { label: "18-24", value: 1 }, { label: "25-29", value: 2 }, { label: "30-34", value: 3 },
        { label: "35-39", value: 4 }, { label: "40-44", value: 5 }, { label: "45-49", value: 6 },
        { label: "50-54", value: 7 }, { label: "55-59", value: 8 }, { label: "60-64", value: 9 },
        { label: "65-69", value: 10 }, { label: "70-74", value: 11 }, { label: "75-79", value: 12 },
        { label: "80+", value: 13 }
      ]},
      { name: "hypertension", label: "Hypertension", type: "select", options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] , tooltip: "Has the patient been diagnosed with hypertension (high blood pressure)?" },
      { name: "high_chol", label: "High Cholesterol", type: "select", options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] , tooltip: "Has the patient been diagnosed with high cholesterol?" },
      { name: "bmi", label: "BMI", type: "number", min: 10, max: 70, step: 0.1 , tooltip: "Body Mass Index. Normal: 18.5-24.9. Overweight: 25-29.9. Obese: >= 30" },
      { name: "smoking_history", label: "Smoker", type: "select", options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] , tooltip: "Does the patient have a history of smoking?" },
      { name: "heart_disease", label: "Heart Disease/Attack", type: "select", options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] , tooltip: "Has the patient had a heart attack or coronary heart disease?" },
      { name: "physical_activity", label: "Physical Activity (past 30 days)", type: "select", options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] , tooltip: "Has the patient engaged in physical activity in the past 30 days?" },
      { name: "general_health", label: "General Health", type: "select", tooltip: "Patient's self-reported general health", options: [
        { label: "Excellent", value: 1 }, { label: "Very Good", value: 2 }, { label: "Good", value: 3 }, { label: "Fair", value: 4 }, { label: "Poor", value: 5 }
      ]},
    ],
    exampleCases: [
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
    ]
  },
  heart: {
    title: "Heart Disease Risk Assessment",
    description: "Enter the patient's cardiovascular parameters. The model evaluates 13 clinical features to predict the presence of heart disease.",
    modelName: "heart",
    onSubmit: predictHeart,
    fields: [
      { name: "age", label: "Age", type: "number", min: 1, max: 120 , tooltip: "Patient's age in years" },
      { name: "sex", label: "Sex", type: "select", options: [{ label: "Male", value: 1 }, { label: "Female", value: 0 }] , tooltip: "Biological sex of the patient" },
      { name: "cp", label: "Chest Pain Type", type: "select", tooltip: "Type of chest pain experienced", options: [
          { label: "Typical Angina", value: 0 },
          { label: "Atypical Angina", value: 1 },
          { label: "Non-anginal Pain", value: 2 },
          { label: "Asymptomatic", value: 3 }
      ]},
      { name: "trestbps", label: "Resting Blood Pressure", type: "number", min: 50, max: 250 , tooltip: "Resting blood pressure (mm Hg). Normal: 90-120. Elevated: 120-129. High: >= 130" },
      { name: "chol", label: "Cholesterol", type: "number", min: 100, max: 600 , tooltip: "Serum cholesterol (mg/dl). Normal: < 200. Borderline: 200-239. High: >= 240" },
      { name: "fbs", label: "Fasting Blood Sugar > 120 mg/dl", type: "select", options: [{ label: "True", value: 1 }, { label: "False", value: 0 }] , tooltip: "Fasting blood sugar > 120 mg/dl (1 = true, 0 = false)" },
      { name: "restecg", label: "Resting ECG Results", type: "select", tooltip: "Resting electrocardiographic results", options: [
          { label: "Normal", value: 0 },
          { label: "ST-T wave abnormality", value: 1 },
          { label: "Probable/definite left ventricular hypertrophy", value: 2 }
      ]},
      { name: "thalach", label: "Max Heart Rate", type: "number", min: 60, max: 220 , tooltip: "Maximum heart rate achieved. Normal max is approx 220 minus age" },
      { name: "exang", label: "Exercise Induced Angina", type: "select", options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] , tooltip: "Exercise-induced angina (chest pain)" },
      { name: "oldpeak", label: "ST Depression", type: "number", min: 0, max: 10, step: 0.1 , tooltip: "ST depression induced by exercise relative to rest. Normal: < 1.0" },
      { name: "slope", label: "Slope of Peak Exercise ST Segment", type: "select", tooltip: "The slope of the peak exercise ST segment", options: [
          { label: "Upsloping", value: 0 },
          { label: "Flat", value: 1 },
          { label: "Downsloping", value: 2 }
      ]},
      { name: "ca", label: "Number of Major Vessels", type: "select", tooltip: "Number of major vessels (0-4) colored by fluoroscopy", options: [
          { label: "0", value: 0 }, { label: "1", value: 1 }, { label: "2", value: 2 }, { label: "3", value: 3 }, { label: "4", value: 4 }
      ] },
      { name: "thal", label: "Thalassemia", type: "select", tooltip: "Thalassemia type (blood disorder)", options: [
          { label: "Normal", value: 1 },
          { label: "Fixed Defect", value: 2 },
          { label: "Reversable Defect", value: 3 }
      ]}
    ],
    exampleCases: [
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
    ]
  },
  liver: {
    title: "Liver Disease Risk Assessment",
    description: "Enter the patient's hepatic function panel results. The AI model analyzes liver enzymes, bilirubin, and protein levels to predict potential liver disease.",
    modelName: "liver",
    onSubmit: predictLiver,
    fields: [
      { name: "Age", label: "Age", type: "number", min: 1, max: 120 , tooltip: "Patient's age in years" },
      { name: "Gender", label: "Gender", type: "select", options: [{ label: "Male", value: 1 }, { label: "Female", value: 0 }] , tooltip: "Biological sex of the patient" },
      { name: "Total_Bilirubin", label: "Total Bilirubin", type: "number", min: 0, max: 80, step: 0.1 , tooltip: "Total Bilirubin (mg/dL). Normal: 0.1-1.2" },
      { name: "Direct_Bilirubin", label: "Direct Bilirubin", type: "number", min: 0, max: 40, step: 0.1 , tooltip: "Direct Bilirubin (mg/dL). Normal: < 0.3" },
      { name: "Alkaline_Phosphotase", label: "Alkaline Phosphatase", type: "number", min: 0, max: 2500 , tooltip: "Alkaline Phosphatase (IU/L). Normal: 44-147" },
      { name: "Alamine_Aminotransferase", label: "Alamine Aminotransferase", type: "number", min: 0, max: 2500 , tooltip: "ALT (U/L). Normal: 7-56" },
      { name: "Aspartate_Aminotransferase", label: "Aspartate Aminotransferase", type: "number", min: 0, max: 3000 , tooltip: "AST (U/L). Normal: 10-40" },
      { name: "Total_Proteins", label: "Total Proteins", type: "number", min: 0, max: 15, step: 0.1 , tooltip: "Total Proteins (g/dL). Normal: 6.0-8.3" },
      { name: "Albumin", label: "Albumin", type: "number", min: 0, max: 10, step: 0.1 , tooltip: "Albumin (g/dL). Normal: 3.4-5.4" },
      { name: "Albumin_and_Globulin_Ratio", label: "A/G Ratio", type: "number", min: 0, max: 5, step: 0.01 , tooltip: "A/G Ratio. Normal: 1.1-2.5" },
    ],
    exampleCases: [
      {
        name: "Thomas D., 17M",
        description: "Routine adolescent checkup. Normal liver enzymes and bilirubin levels.",
        records: [
          { date: "2023-01-10", type: "Pediatrics", findings: "Healthy 14-year-old. No major issues." },
          { date: "2024-05-22", type: "Sports Physical", findings: "Cleared for high school athletics." },
          { date: "2025-06-11", type: "Annual Physical", findings: "Liver enzymes within normal limits. A/G Ratio 1.2." }
        ],
        data: { Age: 17, Gender: 1, Total_Bilirubin: 0.9, Direct_Bilirubin: 0.3, Alkaline_Phosphotase: 202, Alamine_Aminotransferase: 22, Aspartate_Aminotransferase: 19, Total_Proteins: 7.4, Albumin: 4.1, Albumin_and_Globulin_Ratio: 1.2 }
      },
      {
        name: "Patricia L., 65F",
        description: "Fatigue and mild jaundice. Low albumin and inverted A/G ratio.",
        records: [
          { date: "2023-10-15", type: "Primary Care", findings: "Patient complains of prolonged fatigue. Initial labs ordered." },
          { date: "2024-02-28", type: "Hepatology", findings: "Mild jaundice observed. Alkaline Phosphatase elevated at 187." },
          { date: "2025-07-05", type: "Follow-up", findings: "Albumin remains low (3.3). Advised further imaging and biopsy." }
        ],
        data: { Age: 65, Gender: 0, Total_Bilirubin: 0.7, Direct_Bilirubin: 0.1, Alkaline_Phosphotase: 187, Alamine_Aminotransferase: 16, Aspartate_Aminotransferase: 18, Total_Proteins: 6.8, Albumin: 3.3, Albumin_and_Globulin_Ratio: 0.9 }
      }
    ]
  },
  kidney: {
    title: "Chronic Kidney Disease Assessment",
    description: "Enter the patient's urinalysis and comprehensive metabolic panel results. The AI will evaluate 24 indicators to predict Chronic Kidney Disease.",
    modelName: "kidney",
    onSubmit: predictKidney,
    fields: [
      { name: "age", label: "Age", type: "number", min: 1, max: 120 , tooltip: "Patient's age in years" },
      { name: "bp", label: "Blood Pressure", type: "number", min: 50, max: 200 , tooltip: "Blood Pressure (mm/Hg). Normal: 90-120. Elevated: 120-129. High: >= 130" },
      { name: "sg", label: "Specific Gravity", type: "select", tooltip: "Specific Gravity. Normal range: 1.002 - 1.030", options: [
          { label: "1.005", value: 1.005 }, { label: "1.010", value: 1.010 }, 
          { label: "1.015", value: 1.015 }, { label: "1.020", value: 1.020 }, { label: "1.025", value: 1.025 }
      ]},
      { name: "al", label: "Albumin", type: "select", tooltip: "Albumin in urine. Normal: 0. Scale: 0-5", options: [
          { label: "0", value: 0 }, { label: "1", value: 1 }, { label: "2", value: 2 }, { label: "3", value: 3 }, { label: "4", value: 4 }, { label: "5", value: 5 }
      ]},
      { name: "su", label: "Sugar", type: "select", tooltip: "Sugar in urine. Normal: 0. Scale: 0-5", options: [
          { label: "0", value: 0 }, { label: "1", value: 1 }, { label: "2", value: 2 }, { label: "3", value: 3 }, { label: "4", value: 4 }, { label: "5", value: 5 }
      ]},
      { name: "rbc", label: "Red Blood Cells", type: "select", options: [{ label: "Normal", value: 1 }, { label: "Abnormal", value: 0 }] },
      { name: "pc", label: "Pus Cell", type: "select", options: [{ label: "Normal", value: 1 }, { label: "Abnormal", value: 0 }] },
      { name: "pcc", label: "Pus Cell Clumps", type: "select", options: [{ label: "Present", value: 1 }, { label: "Not Present", value: 0 }] },
      { name: "ba", label: "Bacteria", type: "select", options: [{ label: "Present", value: 1 }, { label: "Not Present", value: 0 }] },
      { name: "bgr", label: "Blood Glucose Random", type: "number", min: 0, max: 500 , tooltip: "Blood Glucose Random (mgs/dl). Normal: 70-140" },
      { name: "bu", label: "Blood Urea", type: "number", min: 0, max: 400 , tooltip: "Blood Urea (mgs/dl). Normal: 7-20" },
      { name: "sc", label: "Serum Creatinine", type: "number", min: 0, max: 80, step: 0.1 , tooltip: "Serum Creatinine (mgs/dl). Normal: 0.74-1.35" },
      { name: "sod", label: "Sodium", type: "number", min: 0, max: 200, step: 0.1 , tooltip: "Sodium (mEq/L). Normal: 135-145" },
      { name: "pot", label: "Potassium", type: "number", min: 0, max: 50, step: 0.1 , tooltip: "Potassium (mEq/L). Normal: 3.6-5.2" },
      { name: "hemo", label: "Hemoglobin", type: "number", min: 0, max: 25, step: 0.1 , tooltip: "Hemoglobin (gms). Normal: 12.0-17.2" },
      { name: "pcv", label: "Packed Cell Volume", type: "number", min: 0, max: 60 , tooltip: "Packed Cell Volume (%). Normal: 36-50%" },
      { name: "wc", label: "White Blood Cell Count", type: "number", min: 0, max: 30000 , tooltip: "White Blood Cell Count (cells/cumm). Normal: 4500-11000" },
      { name: "rc", label: "Red Blood Cell Count", type: "number", min: 0, max: 10, step: 0.1 , tooltip: "Red Blood Cell Count (millions/cmm). Normal: 4.2-6.1" },
      { name: "htn", label: "Hypertension", type: "select", options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
      { name: "dm", label: "Diabetes Mellitus", type: "select", options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
      { name: "cad", label: "Coronary Artery Disease", type: "select", options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
      { name: "appet", label: "Appetite", type: "select", options: [{ label: "Good", value: 1 }, { label: "Poor", value: 0 }] },
      { name: "pe", label: "Pedal Edema", type: "select", options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
      { name: "ane", label: "Anemia", type: "select", options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
    ],
    exampleCases: [
      {
        name: "Emily R., 40F",
        description: "Healthy baseline assessment. Normal GFR, no proteinuria or hematuria.",
        records: [
          { date: "2023-02-14", type: "Routine Labs", findings: "Creatinine 1.0 mg/dL, BUN 12 mg/dL. Normal kidney function." },
          { date: "2024-04-20", type: "Urinalysis", findings: "Negative for albumin and sugar. Specific gravity 1.025." },
          { date: "2025-01-10", type: "Annual Physical", findings: "Blood pressure 140/80. No signs of pedal edema. Hemoglobin 15.0." }
        ],
        data: { age: 40, bp: 80, sg: 1.025, al: 0, su: 0, rbc: 1, pc: 1, pcc: 0, ba: 0, bgr: 140, bu: 10, sc: 1.2, sod: 135, pot: 5.0, hemo: 15.0, pcv: 48, wc: 10400, rc: 4.5, htn: 0, dm: 0, cad: 0, appet: 1, pe: 0, ane: 0 }
      },
      {
        name: "William H., 48M",
        description: "Diabetic nephropathy follow-up. Elevated BUN and mild proteinuria.",
        records: [
          { date: "2022-09-05", type: "Endocrinology", findings: "Type 2 Diabetes poorly controlled. Blood glucose 150 mg/dL." },
          { date: "2024-06-12", type: "Urinalysis", findings: "Trace albuminuria detected (1+). Specific gravity 1.020." },
          { date: "2025-08-30", type: "Nephrology", findings: "BUN elevated at 36 mg/dL. Mild hypertension noted." }
        ],
        data: { age: 48, bp: 80, sg: 1.020, al: 1, su: 0, rbc: 1, pc: 1, pcc: 0, ba: 0, bgr: 121, bu: 36, sc: 1.2, sod: 138, pot: 4.4, hemo: 15.4, pcv: 44, wc: 7800, rc: 5.2, htn: 1, dm: 1, cad: 0, appet: 1, pe: 0, ane: 0 }
      }
    ]
  },
  lungs: {
    title: "Lung Cancer Risk Assessment",
    description: "Evaluate patient lifestyle factors and reported symptoms to assess lung cancer risk probability.",
    modelName: "lungs",
    onSubmit: predictLungs,
    fields: [
      { name: "GENDER", label: "Gender", type: "select", options: [{ label: "Male", value: 1 }, { label: "Female", value: 0 }] },
      { name: "AGE", label: "Age", type: "number", min: 1, max: 120 },
      { name: "SMOKING", label: "Smoking History", type: "select", options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
      { name: "YELLOW_FINGERS", label: "Yellow Fingers", type: "select", options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
      { name: "ANXIETY", label: "Anxiety", type: "select", options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
      { name: "PEER_PRESSURE", label: "Peer Pressure", type: "select", options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
      { name: "CHRONIC_DISEASE", label: "Chronic Disease", type: "select", options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
      { name: "FATIGUE", label: "Fatigue", type: "select", options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
      { name: "ALLERGY", label: "Allergy", type: "select", options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
      { name: "WHEEZING", label: "Wheezing", type: "select", options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
      { name: "ALCOHOL_CONSUMING", label: "Alcohol Consumption", type: "select", options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
      { name: "COUGHING", label: "Coughing", type: "select", options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
      { name: "SHORTNESS_OF_BREATH", label: "Shortness of Breath", type: "select", options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
      { name: "SWALLOWING_DIFFICULTY", label: "Swallowing Difficulty", type: "select", options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
      { name: "CHEST_PAIN", label: "Chest Pain", type: "select", options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
    ],
    exampleCases: [
      {
        name: "Susan M., 59F",
        description: "Non-smoker. Complains of mild fatigue but denies chest pain or chronic cough.",
        records: [
          { date: "2022-04-18", type: "Primary Care", findings: "Patient generally healthy. No history of smoking." },
          { date: "2024-09-02", type: "Urgent Care", findings: "Treated for minor seasonal allergies." },
          { date: "2025-11-20", type: "Annual Physical", findings: "Mild fatigue reported, but no wheezing or chest pain." }
        ],
        data: { GENDER: 0, AGE: 59, SMOKING: 0, YELLOW_FINGERS: 1, ANXIETY: 0, PEER_PRESSURE: 0, CHRONIC_DISEASE: 0, FATIGUE: 1, ALLERGY: 0, WHEEZING: 0, ALCOHOL_CONSUMING: 0, COUGHING: 0, SHORTNESS_OF_BREATH: 0, SWALLOWING_DIFFICULTY: 0, CHEST_PAIN: 0 }
      },
      {
        name: "Richard B., 69M",
        description: "Heavy smoker. Presents with chronic wheezing, shortness of breath, and chest pain.",
        records: [
          { date: "2023-03-14", type: "Pulmonology", findings: "Chronic smoker. Shortness of breath on exertion." },
          { date: "2024-08-25", type: "ER Visit", findings: "Acute exacerbation of chronic cough and wheezing." },
          { date: "2025-12-10", type: "Follow-up", findings: "Chest pain reported. Swallowing difficulty noted. Referred for CT." }
        ],
        data: { GENDER: 1, AGE: 69, SMOKING: 1, YELLOW_FINGERS: 1, ANXIETY: 1, PEER_PRESSURE: 0, CHRONIC_DISEASE: 0, FATIGUE: 1, ALLERGY: 0, WHEEZING: 1, ALCOHOL_CONSUMING: 1, COUGHING: 1, SHORTNESS_OF_BREATH: 1, SWALLOWING_DIFFICULTY: 1, CHEST_PAIN: 1 }
      }
    ]
  }
};
