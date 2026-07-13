"""
Canonical Feature Schemas for AI Healthcare Models.
This file ensures consistency between Training, Inference, and Advanced Analytics.
"""

# --- Diabetes Features (BRFSS 2015 / CDC) ---
# Canonical names used in prediction.py and schemas.py
DIABETES_FEATURES = [
    'hypertension',
    'high_chol',
    'bmi',
    'smoking_history',
    'heart_disease',
    'physical_activity',
    'general_health',
    'gender',
    'age_bucket'
]

# Mapping from raw dataset columns (e.g. Parquet) to canonical names
DIABETES_DATASET_MAP = {
    'HighBP': 'hypertension',
    'HighChol': 'high_chol',
    'BMI': 'bmi',
    'Smoker': 'smoking_history',
    'HeartDiseaseorAttack': 'heart_disease',
    'PhysActivity': 'physical_activity',
    'GenHlth': 'general_health',
    'Sex': 'gender',
    'Age': 'age_bucket'
}

# --- Heart Disease Features ---
HEART_FEATURES = [
    'age', 'sex', 'cp', 'trestbps', 'chol',
    'fbs', 'restecg', 'thalach', 'exang',
    'oldpeak', 'slope', 'ca', 'thal'
]

# --- Liver Disease Features ---
LIVER_FEATURES = [
    'Age', 'Gender', 'Total_Bilirubin', 'Direct_Bilirubin',
    'Alkaline_Phosphotase', 'Alamine_Aminotransferase',
    'Aspartate_Aminotransferase', 'Total_Proteins',
    'Albumin', 'Albumin_and_Globulin_Ratio'
]

# --- Lung Issue Features ---
LUNG_FEATURES = [
    'GENDER', 'AGE', 'SMOKING', 'YELLOW_FINGERS', 'ANXIETY',
    'PEER_PRESSURE', 'CHRONIC_DISEASE', 'FATIGUE', 'ALLERGY',
    'WHEEZING', 'ALCOHOL_CONSUMING', 'COUGHING', 'SHORTNESS_OF_BREATH',
    'SWALLOWING_DIFFICULTY', 'CHEST_PAIN'
]

# --- Kidney Disease Features ---
KIDNEY_FEATURES = [
    'age', 'bp', 'sg', 'al', 'su', 'rbc', 'pc', 'pcc', 'ba',
    'bgr', 'bu', 'sc', 'sod', 'pot', 'hemo', 'pcv', 'wc', 'rc',
    'htn', 'dm', 'cad', 'appet', 'pe', 'ane'
]
