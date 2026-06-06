import React, { createContext, useContext, useState, ReactNode, useEffect } from 'react';

export type Language = 'en' | 'es' | 'hi';

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
    commandCenter: "Command Center",
    patientRegistry: "Patient Registry",
    engageCopilot: "Engage Copilot",
    liveTelemetry: "Live Hospital Workflow Layer",
    language: "Language",
    signIn: "Sign In",
    username: "Username",
    password: "Password",
    accessConsole: "Access Console",
    welcome: "Attending",
    riskAssessment: "Predictive Diagnostics",
    telemedicine: "Telemedicine Scheduler",
    infrastructure: "Capacity Board",
    adminConsole: "Admin Panel",
    logout: "Log Out"
  },
  es: {
    commandCenter: "Centro de Comando",
    patientRegistry: "Registro de Pacientes",
    engageCopilot: "Activar Copiloto",
    liveTelemetry: "Capa de Flujo de Trabajo Hospitalario en Vivo",
    language: "Idioma",
    signIn: "Iniciar Sesión",
    username: "Usuario",
    password: "Contraseña",
    accessConsole: "Acceder a Consola",
    welcome: "Atendiendo",
    riskAssessment: "Diagnósticos Predictivos",
    telemedicine: "Agenda de Telemedicina",
    infrastructure: "Panel de Capacidad",
    adminConsole: "Panel de Control",
    logout: "Cerrar Sesión"
  },
  hi: {
    commandCenter: "कमांड सेंटर",
    patientRegistry: "मरीज़ों की सूची",
    engageCopilot: "एआई को-पायलट सक्रिय करें",
    liveTelemetry: "लाइव अस्पताल कार्यप्रवाह परत",
    language: "भाषा",
    signIn: "लॉग इन करें",
    username: "यूज़रनेम",
    password: "पासवर्ड",
    accessConsole: "कंसोल एक्सेस करें",
    welcome: "उपस्थित चिकित्सक",
    riskAssessment: "पूर्वानुमानित निदान",
    telemedicine: "टेलीमेडिसिन शेड्यूलर",
    infrastructure: "क्षमता बोर्ड",
    adminConsole: "प्रशासन कंसोल",
    logout: "लॉग आउट"
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
    const saved = localStorage.getItem('app-language');
    if (saved === 'en' || saved === 'es' || saved === 'hi') {
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
