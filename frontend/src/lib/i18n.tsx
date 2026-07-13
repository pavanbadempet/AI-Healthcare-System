import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';

export type Language = 'en' | 'es' | 'hi' | 'te' | 'fr' | 'de' | 'zh' | 'ar';

export interface Translations {
  commandCenter: string;
  patientRegistry: string;
  engageCopilot: string;
  liveTelemetry: string;
  language: string;
  signIn: string;
  username: string;
  password: string;
  accessConsole: string;
  welcome: string;
  riskAssessment: string;
  telemedicine: string;
  infrastructure: string;
  adminConsole: string;
  logout: string;
}

const translations: Record<Language, Translations> = {
  en: {
    commandCenter: "Hospital Dashboard",
    patientRegistry: "Patients List",
    engageCopilot: "Ask AI Doctor",
    liveTelemetry: "Live Hospital Monitoring Layer",
    language: "Language",
    signIn: "Sign In",
    username: "Username",
    password: "Password",
    accessConsole: "Access Console",
    welcome: "Attending Doctor",
    riskAssessment: "AI Risk Screening",
    telemedicine: "Video Consults",
    infrastructure: "Hospital Beds",
    adminConsole: "Admin Tools",
    logout: "Log Out"
  },
  es: {
    commandCenter: "Tablero de Control",
    patientRegistry: "Lista de Pacientes",
    engageCopilot: "Preguntar al Doctor AI",
    liveTelemetry: "Capa de Monitoreo de Hospital en Vivo",
    language: "Idioma",
    signIn: "Iniciar Sesión",
    username: "Usuario",
    password: "Contraseña",
    accessConsole: "Acceder a Consola",
    welcome: "Médico de Turno",
    riskAssessment: "Evaluación de Riesgo AI",
    telemedicine: "Consultas por Video",
    infrastructure: "Camas de Hospital",
    adminConsole: "Herramientas Administrativas",
    logout: "Cerrar Sesión"
  },
  hi: {
    commandCenter: "अस्पताल डैशबोर्ड",
    patientRegistry: "मरीज़ों की सूची",
    engageCopilot: "एआई डॉक्टर से पूछें",
    liveTelemetry: "लाइव अस्पताल निगरानी प्रणाली",
    language: "भाषा",
    signIn: "लॉग इन करें",
    username: "यूज़रनेम",
    password: "पासवर्ड",
    accessConsole: "कंसोल एक्सेस करें",
    welcome: "उपस्थित चिकित्सक",
    riskAssessment: "एआई जोखिम जांच",
    telemedicine: "वीडियो कॉल परामर्श",
    infrastructure: "अस्पताल बेड",
    adminConsole: "प्रशासनिक टूल्स",
    logout: "लॉग आउट"
  },
  te: {
    commandCenter: "ఆసుపత్రి డాష్‌బోర్డ్",
    patientRegistry: "రోగుల జాబితా",
    engageCopilot: "AI డాక్టర్‌ని అడగండి",
    liveTelemetry: "లైవ్ హాస్పిటల్ పర్యవేక్షణ",
    language: "భాష",
    signIn: "సైన్ ఇన్",
    username: "యూజర్‌నేమ్",
    password: "పాస్‌వర్డ్",
    accessConsole: "కన్సోల్ యాక్సెస్",
    welcome: "హాజరైన డాక్టర్",
    riskAssessment: "AI ప్రమాద అంచనా",
    telemedicine: "వీడియో కన్సల్టేషన్",
    infrastructure: "ఆసుపత్రి పడకలు",
    adminConsole: "అడ్మిన్ టూల్స్",
    logout: "లాగ్ అవుట్"
  },
  fr: {
    commandCenter: "Tableau de Bord",
    patientRegistry: "Liste des Patients",
    engageCopilot: "Demander au Docteur IA",
    liveTelemetry: "Surveillance de l'Hôpital",
    language: "Langue",
    signIn: "Se Connecter",
    username: "Nom d'utilisateur",
    password: "Mot de passe",
    accessConsole: "Accéder à la Console",
    welcome: "Médecin Traitant",
    riskAssessment: "Évaluation des Risques IA",
    telemedicine: "Consultations Vidéo",
    infrastructure: "Lits d'Hôpital",
    adminConsole: "Outils d'Administration",
    logout: "Se Déconnecter"
  },
  de: {
    commandCenter: "Krankenhaus-Dashboard",
    patientRegistry: "Patientenliste",
    engageCopilot: "KI-Arzt Fragen",
    liveTelemetry: "Live-Krankenhausüberwachung",
    language: "Sprache",
    signIn: "Anmelden",
    username: "Benutzername",
    password: "Passwort",
    accessConsole: "Konsole Aufrufen",
    welcome: "Behandelnder Arzt",
    riskAssessment: "KI-Risikobewertung",
    telemedicine: "Video-Konsultationen",
    infrastructure: "Krankenhausbetten",
    adminConsole: "Verwaltungstools",
    logout: "Abmelden"
  },
  zh: {
    commandCenter: "医院仪表板",
    patientRegistry: "患者列表",
    engageCopilot: "询问 AI 医生",
    liveTelemetry: "实时医院监控",
    language: "语言",
    signIn: "登录",
    username: "用户名",
    password: "密码",
    accessConsole: "访问控制台",
    welcome: "主治医生",
    riskAssessment: "AI 风险评估",
    telemedicine: "视频咨询",
    infrastructure: "病床",
    adminConsole: "管理工具",
    logout: "登出"
  },
  ar: {
    commandCenter: "لوحة تحكم المستشفى",
    patientRegistry: "قائمة المرضى",
    engageCopilot: "اسأل طبيب الذكاء الاصطناعي",
    liveTelemetry: "مراقبة المستشفى المباشرة",
    language: "اللغة",
    signIn: "تسجيل الدخول",
    username: "اسم المستخدم",
    password: "كلمة المرور",
    accessConsole: "الوصول إلى وحدة التحكم",
    welcome: "الطبيب المعالج",
    riskAssessment: "تقييم المخاطر بالذكاء الاصطناعي",
    telemedicine: "استشارات الفيديو",
    infrastructure: "أسرة المستشفى",
    adminConsole: "أدوات الإدارة",
    logout: "تسجيل الخروج"
  }
};

interface LanguageContextProps {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: Translations;
}

const LanguageContext = createContext<LanguageContextProps | undefined>(undefined);

export function LanguageProvider({ children }: { children: ReactNode }) {
  // Try to load language from localStorage or default to English
  const [language, setLanguageState] = useState<Language>(() => {
    const saved = localStorage.getItem('app-language') as Language;
    const validLanguages = ['en', 'es', 'hi', 'te', 'fr', 'de', 'zh', 'ar'];
    if (validLanguages.includes(saved)) {
      return saved;
    }
    return 'en';
  });

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem('app-language', lang);
    document.documentElement.lang = lang;
  };

  useEffect(() => {
    document.documentElement.lang = language;
  }, [language]);

  const t = translations[language];

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useTranslation() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useTranslation must be used within a LanguageProvider');
  }
  return context;
}
