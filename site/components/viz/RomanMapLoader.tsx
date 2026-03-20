'use client';

import dynamic from 'next/dynamic';
import type { MapTimelapseProps } from './map-types';

const RomanMap = dynamic(() => import('./RomanMap'), {
  ssr: false,
  loading: () => (
    <div
      className="flex items-center justify-center w-full h-full"
      style={{ background: '#0a1628', minHeight: 360 }}
    >
      <div className="flex flex-col items-center gap-3">
        <div
          style={{
            width: 40,
            height: 40,
            border: '3px solid #2a3a5c',
            borderTopColor: 'var(--color-accent)',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
          }}
        />
        <p
          style={{
            color: 'var(--color-accent)',
            fontSize: '1.1em',
            letterSpacing: 1,
            fontFamily: 'var(--font-serif)',
          }}
        >
          Loading the Roman World...
        </p>
      </div>
    </div>
  ),
});

export default function RomanMapLoader(props: MapTimelapseProps) {
  return <RomanMap {...props} />;
}
