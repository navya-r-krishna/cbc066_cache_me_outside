import React from 'react';
import { useApp } from '../../context/AppContext';
import { CheckCircle2, AlertCircle, Info, AlertTriangle, X } from 'lucide-react';

export function ToastContainer() {
  const { toasts, removeToast } = useApp();

  if (toasts.length === 0) return null;

  return (
    <div className="toast-container" aria-live="polite">
      {toasts.map((toast) => {
        let Icon = Info;
        let toastClass = 'toast-info';

        if (toast.type === 'success') {
          Icon = CheckCircle2;
          toastClass = 'toast-success';
        } else if (toast.type === 'error') {
          Icon = AlertCircle;
          toastClass = 'toast-error';
        } else if (toast.type === 'warning') {
          Icon = AlertTriangle;
          toastClass = 'toast-warning';
        }

        return (
          <div key={toast.id} className={`toast-item ${toastClass}`}>
            <Icon size={18} style={{ flexShrink: 0, marginTop: 2 }} />
            <div className="toast-body">
              <div className="toast-title">{toast.title}</div>
              {toast.message && <div className="toast-message">{toast.message}</div>}
            </div>
            <button
              className="toast-close-btn"
              onClick={() => removeToast(toast.id)}
              aria-label="Dismiss notification"
            >
              <X size={15} />
            </button>
          </div>
        );
      })}
    </div>
  );
}
