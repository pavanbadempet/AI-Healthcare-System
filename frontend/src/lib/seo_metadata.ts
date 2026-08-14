/**
 * Programmatic SEO & Schema.org JSON-LD Structured Metadata Generator.
 * Enables automatic rich snippet ranking on Google Search, Bing, and AI search engines
 * (Perplexity, ChatGPT Search) for clinical calculators, models, and digital twins.
 */

export interface MedicalSEOConfig {
  title: string;
  description: string;
  keywords: string[];
  canonicalUrl: string;
  medicalSpecialty?: string;
  conditionName?: string;
  loincCode?: string;
  snomedCode?: string;
}

export function generateMedicalJsonLd(config: MedicalSEOConfig): string {
  const schema = {
    "@context": "https://schema.org",
    "@type": "MedicalWebPage",
    "name": config.title,
    "description": config.description,
    "url": config.canonicalUrl,
    "keywords": config.keywords.join(", "),
    "about": {
      "@type": "MedicalCondition",
      "name": config.conditionName || "Clinical Risk Screening",
      "code": {
        "@type": "MedicalCode",
        "code": config.snomedCode || "386053000",
        "codingSystem": "SNOMED-CT"
      }
    },
    "mainEntity": {
      "@type": "SoftwareApplication",
      "name": "AI Healthcare System - Distributed Clinical Engine",
      "applicationCategory": "HealthApplication",
      "operatingSystem": "Web, Linux, Cloudflare Edge",
      "offers": {
        "@type": "Offer",
        "price": "0.00",
        "priceCurrency": "USD"
      }
    },
    "publisher": {
      "@type": "Organization",
      "name": "AI Healthcare System",
      "url": "https://github.com/pavanbadempet/AI-Healthcare-System"
    }
  };

  return JSON.stringify(schema, null, 2);
}

export const SEO_PRESETS: Record<string, MedicalSEOConfig> = {
  diabetes: {
    title: "Free AI Diabetes Risk Screening & Prediction Tool (CDC BRFSS)",
    description: "Instant population-level diabetes and prediabetes risk screening tool calibrated on 253,000+ CDC BRFSS epidemiological patient records with Conformal 95% Confidence Sets.",
    keywords: ["diabetes risk calculator", "AI diabetes screening", "BRFSS diabetes model", "conformal prediction diabetes", "HbA1c risk estimator"],
    canonicalUrl: "https://huggingface.co/spaces/pavanbadempet/ai-healthcare-system/#/diabetes-screening",
    conditionName: "Type 2 Diabetes Mellitus",
    snomedCode: "44054006"
  },
  cardiovascular: {
    title: "AI Cardiovascular & Heart Disease Risk Screening Calculator",
    description: "Gradient boosted 10-year cardiovascular risk screener combining Cleveland clinical markers and CDC epidemiological surveys with SHAP feature explainability.",
    keywords: ["heart disease risk calculator", "cardiovascular AI screener", "ASCVD risk tool", "Cleveland heart disease model"],
    canonicalUrl: "https://huggingface.co/spaces/pavanbadempet/ai-healthcare-system/#/cardiovascular-risk-calculator",
    conditionName: "Coronary Artery Disease",
    snomedCode: "53741008"
  },
  digitalTwin: {
    title: "10-Year Multi-Organ Clinical Digital Twin Simulator",
    description: "Simulate non-linear cross-organ disease trajectories (cardiovascular, renal eGFR, metabolic glucose, hepatic enzymes) using coupled ordinary differential equations.",
    keywords: ["clinical digital twin", "multi-organ simulation", "eGFR decay prediction", "cardio-renal metabolic modeling", "ODE health simulator"],
    canonicalUrl: "https://huggingface.co/spaces/pavanbadempet/ai-healthcare-system/#/digital-twin-trajectory",
    conditionName: "Cardiorenal Metabolic Syndrome",
    snomedCode: "73211009"
  },
  pharmacogenomics: {
    title: "CPIC Precision Pharmacogenomics & Drug Interaction Engine",
    description: "Clinical Pharmacogenetics Implementation Consortium (CPIC) guideline lookup for Warfarin, Clopidogrel, Statins, Codeine, and Fluoropyrimidines by CYP2C9, CYP2C19, CYP2D6 genotype.",
    keywords: ["CPIC guidelines tool", "pharmacogenomics calculator", "CYP2C19 clopidogrel dosing", "CYP2C9 warfarin genotype", "adverse drug event prevention"],
    canonicalUrl: "https://huggingface.co/spaces/pavanbadempet/ai-healthcare-system/#/cpic-pharmacogenomics-guide",
    conditionName: "Pharmacogenetic Drug Response",
    snomedCode: "410534003"
  },
  omopLakehouse: {
    title: "Open OHDSI OMOP CDM v5.4 Lakehouse Converter & Validator",
    description: "Convert raw clinical telemetry and EHR tables into standardized OHDSI OMOP CDM v5.4 Delta Lake tables with PySpark Spark Declarative Pipeline (SDP) quality expectation gates.",
    keywords: ["OMOP CDM v5.4 converter", "OHDSI lakehouse", "FHIR to OMOP ETL", "Delta Lake healthcare", "PySpark clinical data engineering"],
    canonicalUrl: "https://huggingface.co/spaces/pavanbadempet/ai-healthcare-system/#/omop-cdm-lakehouse-converter",
    conditionName: "Clinical Data Harmonization",
    snomedCode: "386053000"
  }
};
