import re
import os

files_to_update = {
    "DiabetesPredict.tsx": {
        "gender": 'tooltip: "Biological sex of the patient"',
        "age_bucket": 'tooltip: "Age group bracket"',
        "hypertension": 'tooltip: "Has the patient been diagnosed with hypertension (high blood pressure)?"',
        "high_chol": 'tooltip: "Has the patient been diagnosed with high cholesterol?"',
        "bmi": 'tooltip: "Body Mass Index. Normal: 18.5-24.9. Overweight: 25-29.9. Obese: >= 30"',
        "smoking_history": 'tooltip: "Does the patient have a history of smoking?"',
        "heart_disease": 'tooltip: "Has the patient had a heart attack or coronary heart disease?"',
        "physical_activity": 'tooltip: "Has the patient engaged in physical activity in the past 30 days?"',
        "general_health": 'tooltip: "Patient\'s self-reported general health"'
    },
    "HeartPredict.tsx": {
        "age": 'tooltip: "Patient\'s age in years"',
        "sex": 'tooltip: "Biological sex of the patient"',
        "cp": 'tooltip: "Type of chest pain experienced"',
        "trestbps": 'tooltip: "Resting blood pressure (mm Hg). Normal: 90-120. Elevated: 120-129. High: >= 130"',
        "chol": 'tooltip: "Serum cholesterol (mg/dl). Normal: < 200. Borderline: 200-239. High: >= 240"',
        "fbs": 'tooltip: "Fasting blood sugar > 120 mg/dl (1 = true, 0 = false)"',
        "restecg": 'tooltip: "Resting electrocardiographic results"',
        "thalach": 'tooltip: "Maximum heart rate achieved. Normal max is approx 220 minus age"',
        "exang": 'tooltip: "Exercise-induced angina (chest pain)"',
        "oldpeak": 'tooltip: "ST depression induced by exercise relative to rest. Normal: < 1.0"',
        "slope": 'tooltip: "The slope of the peak exercise ST segment"',
        "ca": 'tooltip: "Number of major vessels (0-3) colored by fluoroscopy"',
        "thal": 'tooltip: "Thalassemia type (blood disorder)"'
    },
    "KidneyPredict.tsx": {
        "age": 'tooltip: "Patient\'s age in years"',
        "bp": 'tooltip: "Blood Pressure (mm/Hg). Normal: 90-120. Elevated: 120-129. High: >= 130"',
        "sg": 'tooltip: "Specific Gravity. Normal range: 1.002 - 1.030"',
        "al": 'tooltip: "Albumin in urine. Normal: 0. Scale: 0-5"',
        "su": 'tooltip: "Sugar in urine. Normal: 0. Scale: 0-5"',
        "bgr": 'tooltip: "Blood Glucose Random (mgs/dl). Normal: 70-140"',
        "bu": 'tooltip: "Blood Urea (mgs/dl). Normal: 7-20"',
        "sc": 'tooltip: "Serum Creatinine (mgs/dl). Normal: 0.74-1.35"',
        "sod": 'tooltip: "Sodium (mEq/L). Normal: 135-145"',
        "pot": 'tooltip: "Potassium (mEq/L). Normal: 3.6-5.2"',
        "hemo": 'tooltip: "Hemoglobin (gms). Normal: 12.0-17.2"',
        "pcv": 'tooltip: "Packed Cell Volume (%). Normal: 36-50%"',
        "wc": 'tooltip: "White Blood Cell Count (cells/cumm). Normal: 4500-11000"',
        "rc": 'tooltip: "Red Blood Cell Count (millions/cmm). Normal: 4.2-6.1"'
    },
    "LiverPredict.tsx": {
        "Age": 'tooltip: "Patient\'s age in years"',
        "Gender": 'tooltip: "Biological sex of the patient"',
        "Total_Bilirubin": 'tooltip: "Total Bilirubin (mg/dL). Normal: 0.1-1.2"',
        "Direct_Bilirubin": 'tooltip: "Direct Bilirubin (mg/dL). Normal: < 0.3"',
        "Alkaline_Phosphotase": 'tooltip: "Alkaline Phosphatase (IU/L). Normal: 44-147"',
        "Alamine_Aminotransferase": 'tooltip: "ALT (U/L). Normal: 7-56"',
        "Aspartate_Aminotransferase": 'tooltip: "AST (U/L). Normal: 10-40"',
        "Total_Proteins": 'tooltip: "Total Proteins (g/dL). Normal: 6.0-8.3"',
        "Albumin": 'tooltip: "Albumin (g/dL). Normal: 3.4-5.4"',
        "Albumin_and_Globulin_Ratio": 'tooltip: "A/G Ratio. Normal: 1.1-2.5"'
    }
}

base_path = "frontend/src/pages"

for file_name, tooltips in files_to_update.items():
    full_path = os.path.join(base_path, file_name)
    if not os.path.exists(full_path):
        continue
    
    with open(full_path, "r", encoding="utf-8") as f:
        content = f.read()

    # We will use regex to find `{ name: "FIELD_NAME", ... }` and append/replace tooltip
    for field, tooltip_str in tooltips.items():
        # Match `{ name: "field", ... }`
        # Because the fields might span multiple lines, or end with }, we need a clever replace
        # We can look for `name: "field"` and replace the end of that object before the `}`
        # But some objects are single line, some are multi line.
        # Actually, simpler: replace `name: "field"` with `name: "field", tooltip: "..."`
        # But we must be careful not to duplicate if tooltip already exists.
        
        # Remove existing tooltip for this field if any (basic regex)
        # We will just do a simple replacement for known formats.
        
        # Find the line containing `name: "field"`
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if f'name: "{field}"' in line:
                # If it already has tooltip: "...", remove it
                line = re.sub(r',\s*tooltip:\s*"[^"]+"', '', line)
                # Now add the new tooltip right after the label
                # Wait, adding it at the end before `}` is safer
                if line.endswith('},'):
                    line = line[:-2] + f', {tooltip_str} }},'
                elif line.endswith('}'):
                    line = line[:-1] + f', {tooltip_str} }}'
                elif '},' in line:
                    # Single line with options
                    # e.g. { name: "sex", label: "Sex", ..., options: [...] }
                    line = re.sub(r'\]\s*\}\,', f'], {tooltip_str} }},', line)
                    line = re.sub(r'\]\s*\}', f'], {tooltip_str} }}', line)
                else:
                    # Multiline start
                    # { name: "cp", label: "Chest Pain Type", type: "select" as const, options: [
                    line = line + f' /* {tooltip_str} */' # Will inject inside the options... wait, better not.
                    # Just insert after `type: "number" as const` or similar.
                    line = re.sub(r'(type:\s*"[^"]+"\s*as\s*const)', r'\1, ' + tooltip_str, line)
                
                lines[i] = line
        content = '\n'.join(lines)
    
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("Tooltips added.")
