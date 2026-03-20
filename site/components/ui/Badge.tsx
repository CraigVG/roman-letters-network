'use client';

import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';

const topicColors: Record<string, { bg: string; text: string; darkBg: string; darkText: string }> = {
  barbarian_invasion: { bg: '#fde8e8', text: '#991b1b', darkBg: '#3b1010', darkText: '#fca5a5' },
  theology:           { bg: '#ede9fe', text: '#5b21b6', darkBg: '#1e1040', darkText: '#c4b5fd' },
  friendship:         { bg: '#fef3c7', text: '#92400e', darkBg: '#302010', darkText: '#fcd34d' },
  church_politics:    { bg: '#dbeafe', text: '#1e40af', darkBg: '#101830', darkText: '#93c5fd' },
  heresy:             { bg: '#fce7f3', text: '#9d174d', darkBg: '#301020', darkText: '#f9a8d4' },
  monasticism:        { bg: '#d1fae5', text: '#065f46', darkBg: '#0a2018', darkText: '#6ee7b7' },
  imperial_politics:  { bg: '#fee2e2', text: '#b91c1c', darkBg: '#2a1010', darkText: '#fca5a5' },
  philosophy:         { bg: '#e0e7ff', text: '#3730a3', darkBg: '#121830', darkText: '#a5b4fc' },
  pastoral:           { bg: '#ecfccb', text: '#3f6212', darkBg: '#141e08', darkText: '#bef264' },
  legal:              { bg: '#f3e8ff', text: '#6b21a8', darkBg: '#1a1030', darkText: '#d8b4fe' },
  exile:              { bg: '#fef9c3', text: '#854d0e', darkBg: '#282008', darkText: '#fde047' },
  patronage:          { bg: '#cffafe', text: '#155e75', darkBg: '#082028', darkText: '#67e8f9' },
  education:          { bg: '#f0fdf4', text: '#166534', darkBg: '#082010', darkText: '#86efac' },
  consolation:        { bg: '#fff7ed', text: '#9a3412', darkBg: '#281810', darkText: '#fdba74' },
  travel:             { bg: '#f0f9ff', text: '#075985', darkBg: '#081828', darkText: '#7dd3fc' },
};

const fallback = { bg: '#f5f5f4', text: '#44403c', darkBg: '#1c1917', darkText: '#a8a29e' };

interface BadgeProps {
  topic: string;
  className?: string;
}

export function Badge({ topic, className = '' }: BadgeProps) {
  const [mounted, setMounted] = useState(false);
  const { resolvedTheme } = useTheme();

  useEffect(() => {
    setMounted(true);
  }, []);

  const colors = topicColors[topic] || fallback;
  const label = topic.replace(/_/g, ' ');
  const isDark = mounted && resolvedTheme === 'dark';

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium
        leading-tight whitespace-nowrap ${className}`}
      style={{
        backgroundColor: isDark ? colors.darkBg : colors.bg,
        color: isDark ? colors.darkText : colors.text,
      }}
    >
      {label}
    </span>
  );
}
