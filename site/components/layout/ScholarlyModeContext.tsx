'use client';

import { createContext, useContext, useState, useEffect, useCallback } from 'react';

interface ScholarlyModeContextType {
  scholarlyMode: boolean;
  setScholarlyMode: (v: boolean) => void;
  isScholarlySource: (translationSource: string | null) => boolean;
}

const ScholarlyModeContext = createContext<ScholarlyModeContextType>({
  scholarlyMode: false,
  setScholarlyMode: () => {},
  isScholarlySource: () => false,
});

const SCHOLARLY_SOURCES = new Set([
  'existing_newadvent',
  'existing_tertullian',
  'existing_fordham',
  'existing_celt',
  'existing_attalus',
  'existing_livius',
  'existing_rogerpearse',
]);

export function ScholarlyModeProvider({ children }: { children: React.ReactNode }) {
  const [scholarlyMode, setScholarlyModeState] = useState(false);

  useEffect(() => {
    // Check URL param first: ?scholarly=true activates scholarly mode
    const params = new URLSearchParams(window.location.search);
    if (params.get('scholarly') === 'true') {
      setScholarlyModeState(true);
      localStorage.setItem('scholarly-mode', 'true');
      return;
    }
    const stored = localStorage.getItem('scholarly-mode');
    if (stored === 'true') setScholarlyModeState(true);
  }, []);

  const setScholarlyMode = useCallback((v: boolean) => {
    setScholarlyModeState(v);
    localStorage.setItem('scholarly-mode', String(v));
  }, []);

  const isScholarlySource = useCallback((source: string | null) => {
    return source != null && SCHOLARLY_SOURCES.has(source);
  }, []);

  return (
    <ScholarlyModeContext.Provider value={{ scholarlyMode, setScholarlyMode, isScholarlySource }}>
      {children}
    </ScholarlyModeContext.Provider>
  );
}

export function useScholarlyMode() {
  return useContext(ScholarlyModeContext);
}
