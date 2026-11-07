import { SERVERS } from '../lib/servers';
import { Server, LogOut } from 'lucide-react';
import * as Tooltip from '@radix-ui/react-tooltip';

const DEFAULT_SKIN_B64 = 'iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAABmElEQVR4nO3aP0vDQBgG8CcPWUTQTRwcqi7iUAQHRZwUHIt0cCp+gI76DRzERWdnZ+3QUbCjdHHp4OafwUEcREVwrFQpmmDvWhKN4Xl/S3t5Ly8pvfdy4RLAozg13nbFdzaWneev7x0H+McIcYQ4QhwhjhBHiCPEhb77vE9hYswZ9+VvXd9nuk4gxIX9dDraKv94fPOghrwjxLHff79Q2UX18Onje+ez0+41MvIk8E1SSX+kr0xsEszDJNh1e/fQ9+0vL4L4genZ+UhJ7JcmI/Ht+k2kfXV5EcmxtFZ2ltTry+c80kur2XCuC+L5z09rkf7FxZX2IPkIcYQ4QlwQr/lBDY+MRtr11Tdn/9LZkDMer9l4TQ/K5gAPQlyYdsLvQ7xbDr5hnyVCHCGOEEeIC58fvx5w0lgHpO2oMpPo/LlmwxknxBHimPUFGGOMMcYYY4wxxvy1IO2E8b3G+PsDvnja+/8+hDhCHCEuSJog7fcLBmVzQEKEOEIcIY4QR4gjxIVJEyR9v+CkuvCr+/8+hDhCHLO+gKy9AxhJZIKppq21AAAAAElFTkSuQmCC';

interface Props {
  current: string;
  onSelect: (id: string) => void;
  skinBase64: string | null;
  onProfile: () => void;
  nickname: string;
  onLogout: () => void;
}

export default function Sidebar({ current, onSelect, skinBase64, onProfile, onLogout }: Props) {
  const activeSkin = skinBase64 || DEFAULT_SKIN_B64;
  return (
    <nav className="sidebar">
      <div className="sidebar-servers">
        {SERVERS.map((s) => (
          <Tooltip.Provider key={s.id}>
            <Tooltip.Root>
              <Tooltip.Trigger asChild>
                <button
                  className={'server-chip' + (current === s.id ? ' active' : '')}
                  onClick={() => onSelect(s.id)}
                >
                  <Server size={19} strokeWidth={1.7} />
                  <i className="dot" />
                </button>
              </Tooltip.Trigger>
              <Tooltip.Portal>
                <Tooltip.Content className="side-tip" sideOffset={8}>
                  {s.name}
                  <Tooltip.Arrow className="side-tip-arrow" />
                </Tooltip.Content>
              </Tooltip.Portal>
            </Tooltip.Root>
          </Tooltip.Provider>
        ))}
      </div>
      <div className="sidebar-bottom">
        <div className="avatar-wrap">
          <button className="avatar" onClick={onProfile}>
            <span
              className="avatar-face"
              style={{
                backgroundImage: `url(data:image/png;base64,${activeSkin})`,
                backgroundSize: '800% 800%',
                backgroundPosition: '14.2857% 14.2857%'
              }}
            />
          </button>
          <button className="avatar-logout" onClick={onLogout}>
            <LogOut size={16} strokeWidth={1.8} />
          </button>
        </div>
      </div>
    </nav>
  );
}
