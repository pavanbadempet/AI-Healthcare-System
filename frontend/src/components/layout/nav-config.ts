/**
 * TopNav menu data, types, and utility functions.
 * Extracted from TopNav.tsx to reduce the main bundle size of the layout component.
 */
import {
  LayoutDashboard, MessageSquare, Heart, Activity,
  FlaskConical, Stethoscope, Wind, User,
  CreditCard, Video, Info, ShieldCheck,
  BedDouble, Server, Settings, Plug, BrainCircuit, Smile,
} from "lucide-react";

/* ───────────────────────────────────────────────────
   MenuItem interface – Universe Dex style
   ─────────────────────────────────────────────────── */
export interface MenuItem {
  id: string;
  title: string;
  href: string;
  icon: React.ElementType;
  desc: string;
  longDesc: string;
  color: string;
  bg: string;
  borderHover: string;
  glow: string;
  gradient: string;
  highlights?: string[];
  subActions?: { title: string; href: string }[];
}

export interface MenuGroup {
  key: string;
  label: string;
  emoji: string;
  accentColor: string;
  items: MenuItem[];
  cols: number;
  routes: string[];
}

/* ───────────────────────────────────────────────────
   MEGA MENU DATA – Operations / Diagnostics / Intelligence
   ─────────────────────────────────────────────────── */
export const operationsItems: MenuItem[] = [
  {
    id: "dashboard",
    title: "Hospital Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
    desc: "See live ICU patient data & alerts",
    longDesc:
      "A simple view of the hospital rooms. Watch heart rate monitors, alert systems, and bed statuses in real-time, helping doctors and nurses coordinate patient care easily.",
    color: "text-indigo-400",
    bg: "bg-indigo-500/10",
    borderHover: "hover:border-indigo-500/60",
    glow: "drop-shadow-[0_0_15px_rgba(99,102,241,0.5)]",
    gradient: "bg-gradient-to-br from-indigo-950/80 via-indigo-900/20 to-black/60",
    highlights: ["Active System", "Live Alarms", "Room Views"],
    subActions: [{ title: "Open Dashboard", href: "/dashboard" }],
  },
  {
    id: "patients",
    title: "Patients List",
    href: "/patients",
    icon: User,
    desc: "View patient records and history",
    longDesc:
      "A listing of all hospital patients. Search patient names, view medical history, check their current status, and edit details from one simple list.",
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    borderHover: "hover:border-emerald-500/60",
    glow: "drop-shadow-[0_0_15px_rgba(52,211,153,0.5)]",
    gradient: "bg-gradient-to-br from-emerald-950/80 via-emerald-900/20 to-black/60",
    highlights: ["List of Patients", "Medical Records", "Patient Details"],
  },
  {
    id: "capacity",
    title: "Hospital Beds",
    href: "/capacity",
    icon: BedDouble,
    desc: "Beds in use and empty rooms",
    longDesc:
      "Manage available hospital beds. View which beds are occupied, which rooms are empty, and plan new patient admissions and discharges easily.",
    color: "text-rose-400",
    bg: "bg-rose-500/10",
    borderHover: "hover:border-rose-500/60",
    glow: "drop-shadow-[0_0_15px_rgba(244,63,94,0.5)]",
    gradient: "bg-gradient-to-br from-rose-950/80 via-rose-900/20 to-black/60",
    highlights: ["Bed Status", "Available Rooms", "Discharges"],
  },
  {
    id: "telemedicine",
    title: "Video Call",
    href: "/telemedicine",
    icon: Video,
    desc: "Talk to patients online",
    longDesc:
      "Start a secure video consultation. Talk face-to-face with remote patients, write treatment notes, and schedule digital appointments easily.",
    color: "text-cyan-400",
    bg: "bg-cyan-500/10",
    borderHover: "hover:border-cyan-500/60",
    glow: "drop-shadow-[0_0_15px_rgba(34,211,238,0.5)]",
    gradient: "bg-gradient-to-br from-cyan-950/80 via-cyan-900/20 to-black/60",
    highlights: ["Live Video Room", "Online Meeting"],
    subActions: [{ title: "Start Video Call", href: "/telemedicine" }],
  },
  {
    id: "infrastructure",
    title: "Server Status",
    href: "/infrastructure",
    icon: Server,
    desc: "Check database & network health",
    longDesc:
      "Monitor computer network connections and HL7 data feeds. Check if the hospital databases, APIs, and servers are running correctly.",
    color: "text-amber-400",
    bg: "bg-amber-500/10",
    borderHover: "hover:border-amber-500/60",
    glow: "drop-shadow-[0_0_15px_rgba(245,158,11,0.5)]",
    gradient: "bg-gradient-to-br from-amber-950/80 via-amber-900/20 to-black/60",
    highlights: ["Server Online", "Database Health", "API Gateway"],
  },
];

export const diagnosticsItems: MenuItem[] = [
  {
    id: "heart",
    title: "Heart Risk Check",
    href: "/predict/heart",
    icon: Heart,
    desc: "Check heart health using AI",
    longDesc:
      "Enter a patient's vital signals and lab values to predict heart disease risk. The smart AI helper uses historical datasets to calculate potential risks instantly.",
    color: "text-rose-400",
    bg: "bg-rose-500/10",
    borderHover: "hover:border-rose-500/60",
    glow: "drop-shadow-[0_0_15px_rgba(244,63,94,0.5)]",
    gradient: "bg-gradient-to-br from-rose-950/80 via-rose-900/20 to-black/60",
    highlights: ["Heart Disease Test", "Easy Input", "Instant Risk Check"],
    subActions: [{ title: "Run Heart Check", href: "/predict/heart" }],
  },
  {
    id: "lungs",
    title: "Lung Risk Check",
    href: "/predict/lungs",
    icon: Wind,
    desc: "Check lung capacity & asthma risk",
    longDesc:
      "Evaluate patient respiratory details. Enter lung test results to calculate asthma, COPD, and other breathing difficulties risks using AI models.",
    color: "text-sky-400",
    bg: "bg-sky-500/10",
    borderHover: "hover:border-sky-500/60",
    glow: "drop-shadow-[0_0_15px_rgba(56,189,248,0.5)]",
    gradient: "bg-gradient-to-br from-sky-950/80 via-sky-900/20 to-black/60",
    highlights: ["Lung Test", "Breathing Analysis", "Asthma Checking"],
  },
  {
    id: "liver",
    title: "Liver Risk Check",
    href: "/predict/liver",
    icon: FlaskConical,
    desc: "Check liver health and markers",
    longDesc:
      "Enter blood test values to evaluate liver condition. The AI checks enzyme levels to detect potential liver damage or issues in simple percentages.",
    color: "text-amber-400",
    bg: "bg-amber-500/10",
    borderHover: "hover:border-amber-500/60",
    glow: "drop-shadow-[0_0_15px_rgba(245,158,11,0.5)]",
    gradient: "bg-gradient-to-br from-amber-950/80 via-amber-900/20 to-black/60",
    highlights: ["Liver Health Test", "Enzyme Analysis", "Cirrhosis Staging"],
  },
  {
    id: "kidney",
    title: "Kidney Risk Check",
    href: "/predict/kidney",
    icon: Stethoscope,
    desc: "Check kidney failure probability",
    longDesc:
      "Evaluate chronic kidney disease stages. Enter eGFR or urea levels to check dialysis risks or renal status in seconds.",
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    borderHover: "hover:border-emerald-500/60",
    glow: "drop-shadow-[0_0_15px_rgba(52,211,153,0.5)]",
    gradient: "bg-gradient-to-br from-emerald-950/80 via-emerald-900/20 to-black/60",
    highlights: ["Kidney Health Test", "Renal Staging", "eGFR Tracking"],
  },
  {
    id: "diabetes",
    title: "Diabetes Risk Check",
    href: "/predict/diabetes",
    icon: Activity,
    desc: "Check sugar level & diabetes risk",
    longDesc:
      "Sugar level and metabolic screening. Input HbA1c and glucose values to calculate insulin resistance and diabetes risk forecasts instantly.",
    color: "text-indigo-400",
    bg: "bg-indigo-500/10",
    borderHover: "hover:border-indigo-500/60",
    glow: "drop-shadow-[0_0_15px_rgba(99,102,241,0.5)]",
    gradient: "bg-gradient-to-br from-indigo-950/80 via-indigo-900/20 to-black/60",
    highlights: ["Diabetes Risk Test", "Sugar Level Check", "HbA1c Screening"],
    subActions: [{ title: "Run Diabetes Test", href: "/predict/diabetes" }],
  },
];

export const intelligenceItems: MenuItem[] = [
  {
    id: "copilot",
    title: "Ask AI Doctor",
    href: "/chat",
    icon: MessageSquare,
    desc: "AI assistant for medical advice",
    longDesc:
      "Talk to the smart AI medical helper. Ask questions about symptoms, common drug mixtures, and healthcare guidelines. Safe, fast, and easy to chat with.",
    color: "text-purple-400",
    bg: "bg-purple-500/10",
    borderHover: "hover:border-purple-500/60",
    glow: "drop-shadow-[0_0_15px_rgba(168,85,247,0.5)]",
    gradient: "bg-gradient-to-br from-purple-950/80 via-purple-900/20 to-black/60",
    highlights: ["AI Chat Helper", "Ask Medical Questions", "Easy to Chat"],
    subActions: [
      { title: "Ask AI Doctor", href: "/chat" },
    ],
  },
  {
    id: "architecture",
    title: "Platform Info",
    href: "/about",
    icon: Info,
    desc: "Platform blueprints and documents",
    longDesc:
      "Read guides about how the hospital system runs. View technical blueprints, data flows, security guidelines, and server setups.",
    color: "text-blue-400",
    bg: "bg-blue-500/10",
    borderHover: "hover:border-blue-500/60",
    glow: "drop-shadow-[0_0_15px_rgba(59,130,246,0.5)]",
    gradient: "bg-gradient-to-br from-blue-950/80 via-blue-900/20 to-black/60",
    highlights: ["Platform Manuals", "Technical Setup", "Server Blueprints"],
  },
  {
    id: "billing",
    title: "Pricing & Bills",
    href: "/pricing",
    icon: CreditCard,
    desc: "Hospital API pricing & details",
    longDesc:
      "Check pricing tiers and computer system billing. Manage subscription rates and API token usage statistics for larger hospital integrations.",
    color: "text-indigo-400",
    bg: "bg-indigo-500/10",
    borderHover: "hover:border-indigo-500/60",
    glow: "drop-shadow-[0_0_15px_rgba(99,102,241,0.5)]",
    gradient: "bg-gradient-to-br from-indigo-950/80 via-indigo-900/20 to-black/60",
    highlights: ["Billing Plan", "Integrations Cost"],
  },
];

export const clinosItems: MenuItem[] = [
  {
    id: "smart_app_registry",
    title: "App Registry",
    href: "/apps",
    icon: Plug,
    desc: "Register and launch SMART apps",
    longDesc: "Pluggable SMART on FHIR application sandbox allowing clinicians to integrate third-party web apps securely.",
    color: "text-sky-400",
    bg: "bg-sky-500/10",
    borderHover: "hover:border-sky-500/60",
    glow: "drop-shadow-[0_0_15px_rgba(56,189,248,0.5)]",
    gradient: "bg-gradient-to-br from-sky-950/80 via-sky-900/20 to-black/60",
    highlights: ["SMART on FHIR", "Secure Sandbox"],
  },
  {
    id: "federated_learning",
    title: "Federated Mesh",
    href: "/federated",
    icon: ShieldCheck,
    desc: "Privacy-preserving model retraining",
    longDesc: "Differential-privacy sync bridge to run distributed ML training across hospital nodes without exposing patient PII.",
    color: "text-purple-400",
    bg: "bg-purple-500/10",
    borderHover: "hover:border-purple-500/60",
    glow: "drop-shadow-[0_0_15px_rgba(168,85,247,0.5)]",
    gradient: "bg-gradient-to-br from-purple-950/80 via-purple-900/20 to-black/60",
    highlights: ["Local DP", "Privacy Budget", "Audits"],
  },
  {
    id: "clinical_intelligence",
    title: "Clinical Intelligence",
    href: "/intelligence",
    icon: BrainCircuit,
    desc: "Real-time alerts and explainable AI",
    longDesc: "Command center for real-time vitals alerting, AI clinician insights, and SHAP feature importance explainability reports.",
    color: "text-indigo-400",
    bg: "bg-indigo-500/10",
    borderHover: "hover:border-indigo-500/60",
    glow: "drop-shadow-[0_0_15px_rgba(99,102,241,0.5)]",
    gradient: "bg-gradient-to-br from-indigo-950/80 via-indigo-900/20 to-black/60",
    highlights: ["Alert Engine", "SHAP Explanations", "AI Narrative"],
  },
  {
    id: "cara_companion",
    title: "Cara Companion",
    href: "/companion",
    icon: Smile,
    desc: "Empathetic patient health companion",
    longDesc: "Warm, friendly patient companion for daily symptom check-ins, flare tracking, biometrics logging, and supportive AI health conversations.",
    color: "text-orange-400",
    bg: "bg-orange-500/10",
    borderHover: "hover:border-orange-500/60",
    glow: "drop-shadow-[0_0_15px_rgba(251,146,60,0.5)]",
    gradient: "bg-gradient-to-br from-orange-950/80 via-rose-900/20 to-black/60",
    highlights: ["Symptom Diary", "Flare Tracker", "Companion Chat"],
  },
];

/* ───────────────────────────────────────────────────
   COMMAND PALETTE items
   ─────────────────────────────────────────────────── */
export const COMMAND_ITEMS = [
  { label: "Hospital Dashboard", href: "/dashboard", category: "Operations", desc: "View live ICU patient room monitors and alert systems", icon: LayoutDashboard },
  { label: "Patients List & Records", href: "/patients", category: "Operations", desc: "Search patient names and check medical records", icon: User },
  { label: "Hospital Beds & Wards", href: "/capacity", category: "Operations", desc: "Track empty rooms, occupied beds, and ward maps", icon: BedDouble },
  { label: "Video Consultations Call", href: "/telemedicine", category: "Operations", desc: "Talk face-to-face with remote patients online", icon: Video },
  { label: "Server Status & Health", href: "/infrastructure", category: "Operations", desc: "Check network connection feeds and database syncs", icon: Server },
  { label: "Heart Disease Risk Test", href: "/predict/heart", category: "Diagnostics AI", desc: "Enter details to check heart condition using AI", icon: Heart },
  { label: "Lung Disease Risk Test", href: "/predict/lungs", category: "Diagnostics AI", desc: "Enter breathing details to check asthma or COPD", icon: Wind },
  { label: "Liver Failure Risk Test", href: "/predict/liver", category: "Diagnostics AI", desc: "Check blood values for potential liver issues", icon: FlaskConical },
  { label: "Kidney Disease Risk Test", href: "/predict/kidney", category: "Diagnostics AI", desc: "Staging and dialysis probability assessment", icon: Stethoscope },
  { label: "Diabetes Risk Test", href: "/predict/diabetes", category: "Diagnostics AI", desc: "Sugar level insulin resistance screening", icon: Activity },
  { label: "Ask AI Doctor / Chat Assistant", href: "/chat", category: "Intelligence", desc: "Type medical questions to the smart AI helper", icon: MessageSquare },
  { label: "Platform Documents & Info", href: "/about", category: "Intelligence", desc: "Read platform manuals and server setup blueprints", icon: Info },
  { label: "Pricing & API Billing Details", href: "/pricing", category: "Intelligence", desc: "Hospital pricing plans and usage details", icon: CreditCard },
  { label: "User Profile Settings", href: "/profile", category: "Account", desc: "View your user name, email, and preferences", icon: Settings },
  { label: "Administrative Tools Panel", href: "/admin", category: "Admin", desc: "Doctor credentials, audit logs, and security levels", icon: ShieldCheck },
  { label: "SMART App Registry", href: "/apps", category: "ClinOS", desc: "Register and launch third-party SMART apps", icon: Plug },
  { label: "Federated Privacy Mesh", href: "/federated", category: "ClinOS", desc: "Privacy-preserving distributed model sync bridge", icon: ShieldCheck },
  { label: "Clinical Intelligence Command Center", href: "/intelligence", category: "ClinOS", desc: "Real-time vitals alerts and explainable AI SHAP report", icon: BrainCircuit },
  { label: "Cara Health Companion", href: "/companion", category: "ClinOS", desc: "Warm symptom tracker, flare diary, and empathetic AI companion", icon: Smile },
];

/* ───────────────────────────────────────────────────
   Menu group definitions used by nav tabs
   ─────────────────────────────────────────────────── */
export const MENU_GROUPS: MenuGroup[] = [
  {
    key: "operations",
    label: "Operations",
    emoji: "🛰️",
    accentColor: "text-indigo-400 data-[state=open]:text-indigo-400",
    items: operationsItems,
    cols: 2,
    routes: ["/dashboard", "/patients", "/capacity", "/telemedicine", "/infrastructure"],
  },
  {
    key: "diagnostics",
    label: "Diagnostics AI",
    emoji: "🧬",
    accentColor: "text-rose-400 data-[state=open]:text-rose-400",
    items: diagnosticsItems,
    cols: 2,
    routes: ["/predict/heart", "/predict/lungs", "/predict/liver", "/predict/kidney", "/predict/diabetes"],
  },
  {
    key: "intelligence",
    label: "Intelligence",
    emoji: "⚡",
    accentColor: "text-purple-400 data-[state=open]:text-purple-400",
    items: intelligenceItems,
    cols: 1,
    routes: ["/chat", "/about", "/pricing"],
  },
  {
    key: "clinos",
    label: "ClinOS",
    emoji: "🚀",
    accentColor: "text-sky-400 data-[state=open]:text-sky-400",
    items: clinosItems,
    cols: 2,
    routes: ["/apps", "/federated", "/intelligence", "/companion"],
  },
];

/* ───────────────────────────────────────────────────
   Icon style helper for command palette + mobile
   ─────────────────────────────────────────────────── */
export function getIconStyles(color: string) {
  switch (color) {
    case "indigo": return "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 group-hover:bg-indigo-500/20 group-hover:text-indigo-300";
    case "emerald": return "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 group-hover:bg-emerald-500/20 group-hover:text-emerald-300";
    case "rose": return "bg-rose-500/10 text-rose-400 border border-rose-500/20 group-hover:bg-rose-500/20 group-hover:text-rose-300";
    case "cyan": return "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 group-hover:bg-cyan-500/20 group-hover:text-cyan-300";
    case "amber": return "bg-amber-500/10 text-amber-400 border border-amber-500/20 group-hover:bg-amber-500/20 group-hover:text-amber-300";
    case "sky": return "bg-sky-500/10 text-sky-400 border border-sky-500/20 group-hover:bg-sky-500/20 group-hover:text-sky-300";
    case "purple": return "bg-purple-500/10 text-purple-400 border border-purple-500/20 group-hover:bg-purple-500/20 group-hover:text-purple-300";
    case "blue": return "bg-blue-500/10 text-blue-400 border border-blue-500/20 group-hover:bg-blue-500/20 group-hover:text-blue-300";
    default: return "bg-white/5 text-white/70 border border-white/10";
  }
}

/* Map item color string (e.g. "rose") to the simple key for getIconStyles */
export function colorKeyFromMenuItem(item: { color?: string }): string {
  const c = (item as MenuItem).color ?? "";
  if (c.includes("indigo")) return "indigo";
  if (c.includes("emerald")) return "emerald";
  if (c.includes("rose")) return "rose";
  if (c.includes("cyan")) return "cyan";
  if (c.includes("amber")) return "amber";
  if (c.includes("sky")) return "sky";
  if (c.includes("purple")) return "purple";
  if (c.includes("blue")) return "blue";
  return "";
}
