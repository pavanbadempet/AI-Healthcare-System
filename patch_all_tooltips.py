import re
import os

base_path = "frontend/src/pages"

def inject_import(content, component_name, import_statement):
    if component_name not in content:
        # Find the last import
        imports = re.findall(r'^import .*;', content, re.MULTILINE)
        if imports:
            last_import = imports[-1]
            content = content.replace(last_import, f"{last_import}\n{import_statement}")
        else:
            content = f"{import_statement}\n{content}"
    return content

def add_tooltip(content, target_text, tooltip_text):
    # E.g. <span className="...">Active Encounters</span> -> 
    # <span className="...">Active Encounters <Tooltip content="..." position="top"><Activity size={12} className="inline ml-1 mb-0.5 cursor-help opacity-70 hover:opacity-100" /></Tooltip></span>
    
    # Simple replacement: look for exactly >TargetText<
    replacement = f'>{target_text} <Tooltip content="{tooltip_text}" position="top"><Activity size={{12}} className="inline ml-1 mb-0.5 cursor-help text-[var(--text-dim)] hover:text-[var(--text-primary)] transition-colors" /></Tooltip><'
    return content.replace(f'>{target_text}<', replacement)


files_to_patch = {
    "Dashboard.tsx": [
        ("Active Encounters", "Current number of patients actively receiving care or monitoring."),
        ("Inference Latency", "The time it takes for the AI models to process data and return a prediction (lower is better)."),
        ("System Load", "Current computational load on the healthcare servers.")
    ],
    "ClinicalIntelligence.tsx": [
        ("RAG Pipeline", "Retrieval-Augmented Generation: The AI searches through actual clinical protocols and guidelines before answering to ensure accuracy."),
        ("Vector Similarity", "How the AI mathematically compares patient symptoms to known disease patterns."),
        ("Confidence Score", "The mathematical certainty the AI has in its prediction, based on historical training data.")
    ],
    "FederatedLearning.tsx": [
        ("Federated Learning", "A privacy-preserving technique where the AI learns from hospital data locally without ever transferring raw patient data to a central server."),
        ("Global Weights", "The shared 'knowledge' of the AI model aggregated from multiple hospitals."),
        ("Gradient Updates", "The mathematical adjustments sent from the hospital to improve the global AI model.")
    ],
    "Capacity.tsx": [
        ("ICU Load", "Percentage of Intensive Care Unit beds currently occupied."),
        ("Triage Queue", "Patients waiting for initial assessment, sorted by medical priority.")
    ],
    "PatientDetail.tsx": [
        ("Risk Trajectory", "The projected future health risk based on historical patient telemetry.")
    ],
    "Telemedicine.tsx": [
        ("WebRTC Stream", "Secure, encrypted peer-to-peer connection used for telemedicine.")
    ]
}

for filename, patches in files_to_patch.items():
    filepath = os.path.join(base_path, filename)
    if not os.path.exists(filepath):
        print(f"Skipping {filename}")
        continue
    
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Ensure Tooltip and Activity are imported
    if "Tooltip" not in content:
        content = inject_import(content, "Tooltip", 'import Tooltip from "@/components/layout/Tooltip";')
    if "Activity" not in content:
        # Check if lucide-react import exists
        if "lucide-react" in content:
            content = re.sub(r'import\s+\{(.*?)\}\s+from\s+["\']lucide-react["\'];', r'import {\1, Activity} from "lucide-react";', content)
        else:
            content = inject_import(content, "Activity", 'import { Activity } from "lucide-react";')
            
    for target, tooltip in patches:
        content = add_tooltip(content, target, tooltip)
        
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Patched {filename}")
