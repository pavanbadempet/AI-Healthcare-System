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
