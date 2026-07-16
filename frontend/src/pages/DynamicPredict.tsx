import { useParams, Navigate } from "react-router-dom";
import PredictionForm from "@/components/predict/PredictionForm";
import { PREDICT_CONFIGS } from "@/lib/predictConfig";

export default function DynamicPredictPage() {
  const { modelType } = useParams<{ modelType: string }>();

  if (!modelType || !PREDICT_CONFIGS[modelType.toLowerCase()]) {
    return <Navigate to="/predict" replace />;
  }

  const config = PREDICT_CONFIGS[modelType.toLowerCase()];

  return (
    <div className="py-8">
      <PredictionForm
        title={config.title}
        description={config.description}
        fields={config.fields}
        onSubmit={config.onSubmit}
        exampleCases={config.exampleCases}
        modelName={config.modelName}
      />
    </div>
  );
}
