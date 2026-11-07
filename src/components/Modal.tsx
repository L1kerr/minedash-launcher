import { ReactNode } from 'react';
import * as Dialog from '@radix-ui/react-dialog';
import { X } from 'lucide-react';
import { motion } from 'framer-motion';

export default function Modal({
  title,
  onClose,
  children,
  wide,
  xwide
}: {
  title: string;
  onClose: () => void;
  children: ReactNode;
  wide?: boolean;
  xwide?: boolean;
}) {
  return (
    <Dialog.Root open onOpenChange={(o) => !o && onClose()}>
      <Dialog.Portal>
        <Dialog.Overlay asChild forceMount>
          <motion.div
            className="modal-veil"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.18 }}
          />
        </Dialog.Overlay>
        <Dialog.Content asChild forceMount>
          <div className="modal-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.96, y: 12 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.97, y: 8 }}
            transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
            className={'modal' + (wide ? ' wide' : '') + (xwide ? ' xwide' : '')}
          >
            <div className="modal-head">
              <Dialog.Title className="modal-title">{title}</Dialog.Title>
              <Dialog.Close asChild>
                <button className="icon-btn modal-close" aria-label="Закрыть">
                  <X size={12} strokeWidth={1.4} />
                </button>
              </Dialog.Close>
            </div>
            <div className="modal-body">{children}</div>
          </motion.div>
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  );
}
