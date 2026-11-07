import { useEffect, useRef } from 'react';
import { SkinViewer } from 'skinview3d';

/**
 * 3D-превью скина на skinview3d (Three.js): корректные UV, overlay-слой,
 * slim-модель, статичная поза анфас.
 */
export default function SkinPreview({
  base64,
  model,
  size = 180
}: {
  base64: string;
  model: 'classic' | 'slim';
  size?: number;
}) {
  const ref = useRef<HTMLCanvasElement>(null);
  const viewerRef = useRef<SkinViewer | null>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;

    const viewer = new SkinViewer({
      canvas,
      width: size,
      height: Math.round(size * 1.3),
      skin: 'data:image/png;base64,' + base64,
      model: model === 'slim' ? 'slim' : 'default',
      panorama: false
    });

    // статичная поза: камера анфас, модель по центру
    viewer.camera.position.set(0, 0, 60);
    viewer.camera.lookAt(0, 0, 0);

    viewerRef.current = viewer;
    return () => {
      viewer.dispose();
      viewerRef.current = null;
    };
  }, [base64, model, size]);

  return (
    <canvas
      ref={ref}
      style={{ width: size, height: Math.round(size * 1.3), display: 'block', margin: '0 auto' }}
    />
  );
}
