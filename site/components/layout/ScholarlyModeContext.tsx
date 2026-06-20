'use client';

import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { isScholarlySource as isScholarlySrc } from '@/lib/scholarlySources';

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

export function ScholarlyModeProvider({ children }: { children: React.ReactNode }) {
  const [scholarlyMode, setScholarlyModeState] = useState(false);

  useEffect(() => {
    // Precedence: explicit ?scholarly= param > saved preference > scholarly subdomain default.
    const params = new URLSearchParams(window.location.search);
    const param = params.get('scholarly');
    if (param === 'true' || param === 'false') {
      const on = param === 'true';
      setScholarlyModeState(on);
      localStorage.setItem('scholarly-mode', String(on));
      return;
    }
    const stored = localStorage.getItem('scholarly-mode');
    if (stored === 'true' || stored === 'false') {
      setScholarlyModeState(stored === 'true');
      return;
    }
    // No explicit choice yet: scholarly.* subdomain defaults to scholarly mode ON (its purpose),
    // every other host defaults OFF. We do NOT persist this default, so the user's later toggle
    // (which does persist) always wins on subsequent visits.
    if (/(^|\.)scholarly\./i.test(window.location.hostname)) {
      setScholarlyModeState(true);
    }
  }, []);

  const setScholarlyMode = useCallback((v: boolean) => {
    setScholarlyModeState(v);
    localStorage.setItem('scholarly-mode', String(v));
  }, []);

  const isScholarlySource = useCallback((source: string | null) => isScholarlySrc(source), []);

  return (
    <ScholarlyModeContext.Provider value={{ scholarlyMode, setScholarlyMode, isScholarlySource }}>
      {children}
    </ScholarlyModeContext.Provider>
  );
}

export function useScholarlyMode() {
  return useContext(ScholarlyModeContext);
}
