import { HeatmapTimelapse } from '@/components/viz/HeatmapTimelapse';
import { Suspense } from 'react';

export default function HeatmapPage() {
  return (
    <Suspense fallback={null}>
      <HeatmapTimelapse />
    </Suspense>
  );
}
