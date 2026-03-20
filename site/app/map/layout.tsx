import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Geographic Map & Timelapse',
  description:
    'Animated geographic map showing the flow of letters across the late Roman world from 100 to 750 AD.',
};

export default function MapLayout({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
