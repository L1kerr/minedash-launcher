import { useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { ServerDef } from '../lib/servers';
import { api } from '../lib/api';

interface Props {
  server: ServerDef;
  bgUrl: string | null;
  bgId: string | null;
  bgFile?: string | null;
  scene: 'none' | 'heli' | 'train' | 'airship' | 'rocket';
}

/** Пиксельный вертолёт в стиле Create (canvas). */
function Helicopter() {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const cv = ref.current;
    if (!cv) return;
    const ctx = cv.getContext('2d');
    if (!ctx) return;
    const S = 12;
    const C = {
      body: '#3d4f5c', dark: '#2c3a44', light: '#546b7a',
      glass: '#7ec8e3', glassD: '#4a90b8',
      rot: '#26313a', gun: '#1c242a', stripe: '#e8a13c', skid: '#39454d'
    };
    const P = (x: number, y: number, w: number, h: number, col: string) => {
      ctx.fillStyle = col;
      ctx.fillRect(x * S, y * S, w * S, h * S);
    };
    const drawFrame = (rotPhase: number) => {
      ctx.clearRect(0, 0, cv.width, cv.height);
      P(1, 10, 6, 2, C.body);
      P(1, 12, 6, 1, C.dark);
      P(0, 8, 2, 5, C.body);
      P(0, 6, 1, 1, C.rot);
      P(0, 14, 1, 1, C.rot);
      P(7, 7, 12, 6, C.body);
      P(7, 13, 12, 2, C.dark);
      P(7, 7, 12, 1, C.light);
      P(10, 12, 7, 1, C.stripe);
      P(19, 7, 5, 5, C.glass);
      P(19, 11, 5, 1, C.glassD);
      P(24, 8, 1, 3, C.body);
      P(12, 15, 4, 2, C.gun);
      P(9, 15, 1, 3, C.skid);
      P(16, 15, 1, 3, C.skid);
      P(8, 18, 10, 1, C.skid);
      P(13, 5, 2, 2, C.rot);
      if (rotPhase === 0) P(4, 4, 22, 1, C.rot);
      else P(12, 3, 4, 2, C.rot);
    };
    let t = 0;
    drawFrame(0);
    const iv = window.setInterval(() => {
      t = (t + 1) % 4;
      drawFrame(t < 2 ? 0 : 1);
    }, 90);
    return () => window.clearInterval(iv);
  }, []);
  return <canvas ref={ref} className="heli" width={320} height={260} aria-hidden />;
}

/** Пиксельный поезд с вагонами (Create-стиль, второй вариант сцены). */
function Train() {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const cv = ref.current;
    if (!cv) return;
    const ctx = cv.getContext('2d');
    if (!ctx) return;
    const S = 12;
    const C = { loc: '#b45309', locD: '#7c2d12', tank: '#546b7a', tankD: '#39454d', wheel: '#1c242a', win: '#7ec8e3' };
    const P = (x: number, y: number, w: number, h: number, col: string) => {
      ctx.fillStyle = col;
      ctx.fillRect(x * S, y * S, w * S, h * S);
    };
    ctx.clearRect(0, 0, cv.width, cv.height);
    // рельса
    P(0, 16, 30, 1, C.wheel);
    // локомотив
    P(2, 8, 8, 6, C.loc);
    P(2, 13, 8, 2, C.locD);
    P(3, 9, 2, 2, C.win);
    P(6, 9, 2, 2, C.win);
    P(1, 6, 2, 4, C.locD);   // труба
    P(3, 7, 6, 1, '#e8a13c');
    // колёса локомотива
    P(3, 14, 2, 2, C.wheel);
    P(7, 14, 2, 2, C.wheel);
    // вагон-цистерна
    P(12, 8, 8, 6, C.tank);
    P(12, 12, 8, 2, C.tankD);
    P(14, 13, 2, 2, C.wheel);
    P(18, 13, 2, 2, C.wheel);
    // платформа с ящиками
    P(22, 11, 7, 3, C.tankD);
    P(23, 8, 2, 3, '#8a6a3b');
    P(26, 9, 2, 2, '#8a6a3b');
    P(24, 13, 2, 2, C.wheel);
    P(27, 13, 1, 2, C.wheel);
    return () => undefined;
  }, []);
  return <canvas ref={ref} className="train" width={380} height={220} aria-hidden />;
}

/** Пиксельный дирижабль (Create-стиль). */
function Airship() {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const cv = ref.current;
    if (!cv) return;
    const ctx = cv.getContext('2d');
    if (!ctx) return;
    const S = 10;
    const C = { hull: '#5a6672', hullD: '#3e4852', hullL: '#74828e', brass: '#c4963e', brassD: '#8c6628', glass: '#7ec8e3', prop: '#26313a', rope: '#8a6a3b' };
    const P = (x: number, y: number, w: number, h: number, col: string) => {
      ctx.fillStyle = col;
      ctx.fillRect(x * S, y * S, w * S, h * S);
    };
    const drawFrame = (propPhase: number) => {
      ctx.clearRect(0, 0, cv.width, cv.height);
      // оболочка дирижабля
      P(4, 4, 20, 8, C.hull);
      P(6, 3, 16, 1, C.hullL);
      P(6, 12, 16, 1, C.hullD);
      P(2, 6, 2, 4, C.hull);
      P(24, 6, 3, 4, C.hullD);
      // полосы
      P(4, 7, 20, 1, C.brass);
      P(4, 9, 20, 1, C.brassD);
      // хвостовое оперение
      P(25, 4, 3, 2, C.hullD);
      P(25, 10, 3, 2, C.hullD);
      // гондола
      P(9, 14, 8, 4, C.brassD);
      P(9, 14, 8, 1, C.brass);
      P(10, 15, 2, 2, C.glass);
      P(14, 15, 2, 2, C.glass);
      // тросы
      P(10, 12, 1, 2, C.rope);
      P(15, 12, 1, 2, C.rope);
      // винт сзади
      P(28, 7, 1, 2, C.prop);
      if (propPhase === 0) { P(29, 5, 1, 6, C.prop); }
      else { P(29, 7, 2, 2, C.prop); }
    };
    let t = 0;
    drawFrame(0);
    const iv = window.setInterval(() => {
      t = (t + 1) % 4;
      drawFrame(t < 2 ? 0 : 1);
    }, 110);
    return () => window.clearInterval(iv);
  }, []);
  return <canvas ref={ref} className="heli" width={320} height={200} aria-hidden />;
}

/** Пиксельная ракета. */
function Rocket() {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const cv = ref.current;
    if (!cv) return;
    const ctx = cv.getContext('2d');
    if (!ctx) return;
    const S = 11;
    const C = { body: '#c8ccd2', bodyD: '#9aa0a8', nose: '#e05252', fin: '#2f6fed', glass: '#7ec8e3', flame: '#ffb040', flameC: '#ff7020' };
    const P = (x: number, y: number, w: number, h: number, col: string) => {
      ctx.fillStyle = col;
      ctx.fillRect(x * S, y * S, w * S, h * S);
    };
    const drawFrame = (flamePhase: number) => {
      ctx.clearRect(0, 0, cv.width, cv.height);
      // нос
      P(8, 1, 4, 2, C.nose);
      P(7, 3, 6, 2, C.nose);
      // корпус
      P(7, 5, 6, 10, C.body);
      P(7, 5, 1, 10, C.bodyD);
      // иллюминатор
      P(9, 7, 2, 2, C.glass);
      // полоса
      P(7, 11, 6, 1, C.fin);
      // стабилизаторы
      P(5, 12, 2, 4, C.fin);
      P(13, 12, 2, 4, C.fin);
      // сопло
      P(8, 15, 4, 1, C.bodyD);
      // пламя
      if (flamePhase === 0) {
        P(8, 16, 4, 3, C.flame);
        P(9, 19, 2, 2, C.flameC);
      } else {
        P(8, 16, 4, 4, C.flame);
        P(9, 20, 2, 3, C.flameC);
        P(10, 23, 1, 1, C.flame);
      }
    };
    let t = 0;
    drawFrame(0);
    const iv = window.setInterval(() => {
      t = (t + 1) % 2;
      drawFrame(t);
    }, 140);
    return () => window.clearInterval(iv);
  }, []);
  return <canvas ref={ref} className="heli" width={240} height={280} aria-hidden />;
}

/** Пиксельный истребитель (Create-стиль, анимация пламени). */
function Jet() {
  const ref = useRef<HTMLCanvasElement>(null);
  useEffect(() => {
    const cv = ref.current;
    if (!cv) return;
    const ctx = cv.getContext('2d');
    if (!ctx) return;
    const S = 10;
    const C = {
      body: '#8a95a3', bodyD: '#5c6672', bodyL: '#b0bac6',
      nose: '#3d4f5c', glass: '#7ec8e3', glassD: '#4a90b8',
      wing: '#4a5560', wingD: '#333d47', tail: '#3d4f5c',
      stripe: '#e8a13c', flame: '#ffb040', flameC: '#ff7020', flameW: '#ffe0a0'
    };
    const P = (x: number, y: number, w: number, h: number, col: string) => {
      ctx.fillStyle = col;
      ctx.fillRect(x * S, y * S, w * S, h * S);
    };
    const drawFrame = (flamePhase: number) => {
      ctx.clearRect(0, 0, cv.width, cv.height);
      // нос
      P(26, 7, 2, 2, C.nose);
      // фюзеляж
      P(6, 6, 20, 4, C.body);
      P(6, 5, 18, 1, C.bodyL);
      P(6, 10, 18, 1, C.bodyD);
      // кабина
      P(20, 6, 4, 2, C.glass);
      P(20, 8, 4, 1, C.glassD);
      // полоса
      P(8, 8, 16, 1, C.stripe);
      // крылья
      P(10, 3, 8, 2, C.wing);
      P(10, 11, 8, 2, C.wing);
      P(12, 2, 4, 1, C.wingD);
      P(12, 13, 4, 1, C.wingD);
      // хвост
      P(4, 4, 3, 2, C.tail);
      P(4, 10, 3, 2, C.tail);
      P(2, 5, 2, 6, C.tail);
      // сопло
      P(4, 7, 2, 2, C.bodyD);
      // пламя (анимация)
      if (flamePhase === 0) {
        P(1, 7, 3, 2, C.flame);
        P(0, 7, 1, 2, C.flameC);
      } else if (flamePhase === 1) {
        P(0, 7, 4, 2, C.flame);
        P(-1, 7, 1, 2, C.flameW);
      } else {
        P(2, 7, 2, 2, C.flame);
        P(1, 7, 1, 2, C.flameW);
      }
    };
    let t = 0;
    drawFrame(0);
    const iv = window.setInterval(() => {
      t = (t + 1) % 3;
      drawFrame(t);
    }, 80);
    return () => window.clearInterval(iv);
  }, []);
  return <canvas ref={ref} className="heli" width={300} height={170} aria-hidden />;
}

/** Анимированные эффекты поверх фона (CSS-слои). */
function BgFx({ bgId }: { bgId: string | null }) {
  if (!bgId) return null;
  const key = bgId.replace(/^[ub]:/, '').replace('.png', '');
  switch (key) {
    case 'space':
      return (
        <div className="fx fx-space" aria-hidden>
          {Array.from({ length: 24 }).map((_, i) => (
            <span key={i} className="fx-star" style={{
              left: `${(i * 37 + 13) % 100}%`,
              top: `${(i * 53 + 7) % 100}%`,
              animationDelay: `${(i % 8) * 0.4}s`,
              animationDuration: `${2 + (i % 5) * 0.6}s`,
            }} />
          ))}
        </div>
      );
    case 'city':
      return (
        <div className="fx fx-city" aria-hidden>
          <div className="fx-windows" />
          {Array.from({ length: 40 }).map((_, i) => (
            <span key={i} className="fx-rain" style={{
              left: `${(i * 2.5 + (i % 3)) % 100}%`,
              animationDelay: `${(i % 10) * 0.18}s`,
              animationDuration: `${0.7 + (i % 4) * 0.15}s`,
            }} />
          ))}
          <div className="fx-fog" />
        </div>
      );
    case 'volcano':
      return (
        <div className="fx fx-volcano" aria-hidden>
          <div className="fx-glow-pulse" />
          {Array.from({ length: 18 }).map((_, i) => (
            <span key={i} className="fx-spark" style={{
              left: `${42 + (i * 7) % 16}%`,
              animationDelay: `${(i % 6) * 0.5}s`,
              animationDuration: `${2.5 + (i % 4) * 0.7}s`,
            }} />
          ))}
        </div>
      );
    case 'aurora':
      return (
        <div className="fx fx-aurora" aria-hidden>
          {Array.from({ length: 4 }).map((_, i) => (
            <span key={i} className="fx-band" style={{
              left: `${12 + i * 22}%`,
              animationDelay: `${i * 1.3}s`,
              animationDuration: `${7 + i * 1.5}s`,
            }} />
          ))}
        </div>
      );
    case 'autumn':
      return (
        <div className="fx fx-autumn" aria-hidden>
          {Array.from({ length: 22 }).map((_, i) => (
            <span key={i} className="fx-leaf" style={{
              left: `${(i * 4.5 + (i % 5)) % 100}%`,
              animationDelay: `${(i % 8) * 0.9}s`,
              animationDuration: `${5 + (i % 5) * 1.2}s`,
            }} />
          ))}
        </div>
      );
    case 'desert':
      return (
        <div className="fx fx-desert" aria-hidden>
          <div className="fx-heat" />
          {Array.from({ length: 14 }).map((_, i) => (
            <span key={i} className="fx-dust" style={{
              left: `${(i * 7.3 + (i % 4)) % 100}%`,
              top: `${55 + (i % 6) * 7}%`,
              animationDelay: `${(i % 7) * 0.9}s`,
              animationDuration: `${6 + (i % 4) * 1.5}s`,
            }} />
          ))}
        </div>
      );
    case 'canyon':
      return (
        <div className="fx fx-canyon" aria-hidden>
          {Array.from({ length: 10 }).map((_, i) => (
            <span key={i} className="fx-dust" style={{
              left: `${(i * 10 + (i % 3)) % 100}%`,
              top: `${60 + (i % 5) * 8}%`,
              animationDelay: `${(i % 5) * 1.2}s`,
              animationDuration: `${8 + (i % 3) * 2}s`,
              opacity: 0.4 + (i % 3) * 0.2,
            }} />
          ))}
        </div>
      );
    case 'ruins':
      return (
        <div className="fx fx-ruins" aria-hidden>
          {Array.from({ length: 16 }).map((_, i) => (
            <span key={i} className="fx-mote" style={{
              left: `${(i * 6.4 + (i % 5)) % 100}%`,
              top: `${25 + (i % 9) * 8}%`,
              animationDelay: `${(i % 8) * 0.7}s`,
              animationDuration: `${5 + (i % 5) * 1.2}s`,
            }} />
          ))}
        </div>
      );
    case 'storm':
      return (
        <div className="fx fx-storm" aria-hidden>
          <div className="fx-flash" />
          {Array.from({ length: 50 }).map((_, i) => (
            <span key={i} className="fx-rain" style={{
              left: `${(i * 2 + (i % 4)) % 100}%`,
              animationDelay: `${(i % 12) * 0.12}s`,
              animationDuration: `${0.55 + (i % 3) * 0.12}s`,
            }} />
          ))}
        </div>
      );
    case 'forest':
      return (
        <div className="fx fx-forest" aria-hidden>
          {Array.from({ length: 5 }).map((_, i) => (
            <span key={i} className="fx-mist" style={{
              left: `${5 + i * 20}%`,
              animationDelay: `${i * 3.5}s`,
              animationDuration: `${16 + i * 3}s`,
              opacity: 0.5 + (i % 3) * 0.15,
            }} />
          ))}
        </div>
      );
    case 'meadow':
      return (
        <div className="fx fx-meadow" aria-hidden>
          {Array.from({ length: 12 }).map((_, i) => (
            <span key={i} className="fx-petal" style={{
              left: `${(i * 8.3 + (i % 3)) % 100}%`,
              animationDelay: `${(i % 7) * 1.1}s`,
              animationDuration: `${7 + (i % 4) * 1.5}s`,
            }} />
          ))}
        </div>
      );
    case 'lake':
      return (
        <div className="fx fx-lake" aria-hidden>
          {Array.from({ length: 14 }).map((_, i) => (
            <span key={i} className="fx-shimmer" style={{
              left: `${(i * 7.5) % 100}%`,
              top: `${55 + (i % 5) * 8}%`,
              animationDelay: `${(i % 6) * 0.6}s`,
              animationDuration: `${2.5 + (i % 3)}s`,
            }} />
          ))}
        </div>
      );
    case 'mountains':
      return (
        <div className="fx fx-mountains" aria-hidden>
          {Array.from({ length: 18 }).map((_, i) => (
            <span key={i} className="fx-bird" style={{
              left: `${(i * 13 + 8) % 90}%`,
              top: `${12 + (i % 5) * 6}%`,
              animationDelay: `${(i % 9) * 0.8}s`,
              animationDuration: `${14 + (i % 5) * 2}s`,
            }} />
          ))}
        </div>
      );
    case 'sunrise':
      return (
        <div className="fx fx-sunrise" aria-hidden>
          {Array.from({ length: 7 }).map((_, i) => (
            <span key={i} className="fx-bird" style={{
              left: `${20 + i * 9}%`,
              top: `${18 + (i % 4) * 7}%`,
              animationDelay: `${i * 1.2}s`,
              animationDuration: `${11 + i}s`,
            }} />
          ))}
        </div>
      );
    case 'swamp':
      return (
        <div className="fx fx-swamp" aria-hidden>
          {Array.from({ length: 20 }).map((_, i) => (
            <span key={i} className="fx-firefly" style={{
              left: `${(i * 5.2 + (i % 4)) % 100}%`,
              top: `${30 + (i % 8) * 8}%`,
              animationDelay: `${(i % 10) * 0.5}s`,
              animationDuration: `${3 + (i % 5) * 0.8}s`,
            }} />
          ))}
          {Array.from({ length: 3 }).map((_, i) => (
            <span key={'m' + i} className="fx-mist" style={{
              left: `${10 + i * 30}%`,
              animationDelay: `${i * 4}s`,
              animationDuration: `${20 + i * 4}s`,
            }} />
          ))}
        </div>
      );
    case 'winter':
      return (
        <div className="fx fx-winter" aria-hidden>
          {Array.from({ length: 60 }).map((_, i) => (
            <span key={i} className="fx-snow" style={{
              left: `${(i * 1.7 + (i % 3) * 0.4) % 100}%`,
              animationDelay: `${(i % 15) * 0.4}s`,
              animationDuration: `${4 + (i % 5)}s`,
              width: 2 + (i % 3),
              height: 2 + (i % 3),
            }} />
          ))}
        </div>
      );
    case 'birch':
      return (
        <div className="fx fx-birch" aria-hidden>
          {Array.from({ length: 10 }).map((_, i) => (
            <span key={i} className="fx-leaf" style={{
              left: `${(i * 10 + (i % 5)) % 100}%`,
              animationDelay: `${(i % 9) * 0.8}s`,
              animationDuration: `${6 + (i % 5) * 1.4}s`,
              background: '#9cc46a',
            }} />
          ))}
        </div>
      );
    default:
      return null;
  }
}

export default function Hero({ server, bgUrl, bgId, bgFile, scene }: Props) {
  const isVideo = bgUrl && (bgUrl.endsWith('.mp4') || bgUrl.endsWith('.webm'));
  return (
    <div className="hero">
      {bgUrl && isVideo && (
        <motion.video
          key={bgUrl}
          className="hero-bg"
          src={bgUrl}
          autoPlay
          loop
          muted
          playsInline
          draggable={false}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.45 }}
        />
      )}
      {bgUrl && !isVideo && (
        <motion.img
          key={bgUrl}
          className="hero-bg"
          src={bgUrl}
          alt=""
          draggable={false}
          onError={(e) => {
            if (bgFile) {
              api.backgrounds.getDataUrl(bgFile).then((du) => {
                if (du) (e.target as HTMLImageElement).src = du;
              });
            }
          }}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.45 }}
        />
      )}
      <BgFx bgId={bgId} />
      <div className="hero-shade" />

      {/* Сцена справа: вертолёт / поезд + пунктирная траектория */}
      {scene !== 'none' && (
        <div className="hero-scene">
          {scene === 'train' && <Train />}
          {scene === 'airship' && <Airship />}
          {scene === 'rocket' && <Rocket />}
          {scene === 'jet' && <Jet />}
          {scene === 'heli' && <Helicopter />}
        </div>
      )}

      <div className="hero-copy">
        <motion.div className="hero-tag-wrap" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05, duration: 0.35 }}>
          <span className="hero-tag">{server.tag}</span>
          <span className="badge-beta">BETA</span>
        </motion.div>
        <motion.h1 initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.12, duration: 0.35 }}>
          {server.name}
        </motion.h1>
        <motion.div className="hero-sub" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.19, duration: 0.35 }}>
          {server.subtitle}
        </motion.div>
        <motion.p initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.26, duration: 0.35 }}>
          {server.description}
        </motion.p>
      </div>
    </div>
  );
}
