import { createContext, useContext, useState, type ReactNode, useEffect } from "react";

export type Language = "en" | "th";

interface LanguageContextType {
  language: Language;
  toggleLanguage: () => void;
  setLanguage: (lang: Language) => void;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>(() => {
    // Initialize from localStorage or default to English
    const saved = localStorage.getItem('pytalk_language');
    return (saved === 'en' || saved === 'th') ? saved : 'en';
  });

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem('pytalk_language', lang);
  };

  const toggleLanguage = () => {
    const newLang: Language = language === 'en' ? 'th' : 'en';
    setLanguage(newLang);
  };

  // Persist language on change
  useEffect(() => {
    localStorage.setItem('pytalk_language', language);
  }, [language]);

  return (
    <LanguageContext.Provider value={{ language, toggleLanguage, setLanguage }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used within LanguageProvider");
  }
  return context;
}
