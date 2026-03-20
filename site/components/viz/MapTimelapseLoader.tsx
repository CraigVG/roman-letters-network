'use client';

import dynamic from 'next/dynamic';
import type { MapTimelapseProps } from '@/components/viz/map-types';

const MapTimelapse = dynamic(() => import('@/components/viz/MapTimelapse'), {
  ssr: false,
  loading: () => (
    <div
      className="w-full h-full flex items-center justify-center rounded-lg"
      style={{
        background: '#0d1829',
        minHeight: 400,
      }}
    >
      <div className="flex flex-col items-center gap-3">
        <div
          style={{
            width: 36,
            height: 36,
            border: '3px solid #2a3a5c',
            borderTopColor: 'var(--color-accent)',
            borderRadius: '50%',
            animation: 'spin 0.8s linear infinite',
          }}
        />
        <p
          className="text-sm tracking-wide"
          style={{ color: 'var(--color-accent)', fontFamily: 'var(--font-serif)' }}
        >
          Loading map...
        </p>
      </div>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  ),
});

export default function MapTimelapseLoader(props: MapTimelapseProps) {
  return <MapTimelapse {...props} wymanMode={props.wymanMode ?? false} />;
}
