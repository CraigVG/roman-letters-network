'use client';

import { Component, type ReactNode } from 'react';
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

/* ── Error Boundary ─────────────────────────────────────────────────── */

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

class MapErrorBoundary extends Component<
  { children: ReactNode },
  ErrorBoundaryState
> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          className="flex items-center justify-center w-full h-full"
          style={{ background: '#0a1628', minHeight: 360 }}
        >
          <div className="flex flex-col items-center gap-4 max-w-md text-center px-6">
            <p
              style={{
                color: 'var(--color-accent)',
                fontSize: '1.1em',
                letterSpacing: 1,
                fontFamily: 'var(--font-serif)',
              }}
            >
              Map failed to load
            </p>
            <p style={{ color: '#8899aa', fontSize: '0.85em', lineHeight: 1.5 }}>
              This may be caused by your browser not supporting WebGL, an
              ad-blocker interfering with map tiles, or a temporary network
              issue.
            </p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="px-4 py-2 rounded-lg text-sm font-medium text-white transition-colors hover:opacity-90"
              style={{ backgroundColor: 'var(--color-accent)' }}
            >
              Try again
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

/* ── Loader ─────────────────────────────────────────────────────────── */

export default function RomanMapLoader(props: MapTimelapseProps) {
  return (
    <MapErrorBoundary>
      <RomanMap {...props} />
    </MapErrorBoundary>
  );
}
