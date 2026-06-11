
import PredictionForm from "@/components/predict/PredictionForm";
import { predictLungs } from "@/lib/api";

const LUNG_FIELDS = [
  { name: "GENDER", label: "Gender", type: "select" as const, options: [{ label: "Male", value: 1 }, { label: "Female", value: 0 }] },
  { name: "AGE", label: "Age", type: "number" as const, min: 1, max: 120 },
  { name: "SMOKING", label: "Smoking History", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
  { name: "YELLOW_FINGERS", label: "Yellow Fingers", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
  { name: "ANXIETY", label: "Anxiety", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
  { name: "PEER_PRESSURE", label: "Peer Pressure", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
  { name: "CHRONIC_DISEASE", label: "Chronic Disease", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
  { name: "FATIGUE", label: "Fatigue", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
  { name: "ALLERGY", label: "Allergy", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
  { name: "WHEEZING", label: "Wheezing", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
  { name: "ALCOHOL_CONSUMING", label: "Alcohol Consumption", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
  { name: "COUGHING", label: "Coughing", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
  { name: "SHORTNESS_OF_BREATH", label: "Shortness of Breath", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
  { name: "SWALLOWING_DIFFICULTY", label: "Swallowing Difficulty", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
  { name: "CHEST_PAIN", label: "Chest Pain", type: "select" as const, options: [{ label: "Yes", value: 1 }, { label: "No", value: 0 }] },
];

export default function LungsPage() {
  return (
    <div className="py-8">
      <PredictionForm
        title="Lung Cancer Risk Assessment"
        description="Evaluate patient lifestyle factors and reported symptoms to assess lung cancer risk probability."
        fields={LUNG_FIELDS}
        onSubmit={predictLungs}
      />
    </div>
  );
}
