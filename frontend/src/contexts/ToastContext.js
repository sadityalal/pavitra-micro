// frontend/src/contexts/ToastContext.js
import React, { createContext, useContext, useState } from 'react';

const ToastContext = createContext();

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

const ToastContainer = ({ toasts, removeToast }) => {
  if (!toasts || toasts.length === 0) return null;

  return (
    <div
      className="toast-container position-fixed bottom-0 end-0 p-3"
      style={{
        zIndex: 9999,
        maxWidth: '350px'
      }}
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={`toast show ${toast.type === 'error' ? 'border-danger' : toast.type === 'warning' ? 'border-warning' : toast.type === 'info' ? 'border-info' : 'border-success'}`}
          role="alert"
          style={{
            minWidth: '300px',
            marginBottom: '10px',
            borderLeft: `4px solid ${toast.type === 'error' ? '#dc3545' : toast.type === 'warning' ? '#ffc107' : toast.type === 'info' ? '#0dcaf0' : '#198754'}`
          }}
        >
          <div className="toast-header" style={{
            backgroundColor: toast.type === 'error' ? '#f8d7da' : toast.type === 'warning' ? '#fff3cd' : toast.type === 'info' ? '#d1ecf1' : '#d1e7dd',
            color: toast.type === 'error' ? '#721c24' : toast.type === 'warning' ? '#856404' : toast.type === 'info' ? '#0c5460' : '#0f5132'
          }}>
            <strong className="me-auto">
              {toast.type === 'error' ? '❌ Error' :
               toast.type === 'warning' ? '⚠️ Warning' :
               toast.type === 'info' ? 'ℹ️ Info' : '✅ Success'}
            </strong>
            <small>{toast.time}</small>
            <button
              type="button"
              className="btn-close"
              onClick={() => removeToast(toast.id)}
              aria-label="Close"
            ></button>
          </div>
          <div className="toast-body" style={{
            backgroundColor: 'white',
            color: '#212529'
          }}>
            {toast.message}
          </div>
        </div>
      ))}
    </div>
  );
};

export const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const addToast = (message, type = 'success', duration = 5000) => {
    const id = Date.now() + Math.random();
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const toast = { id, message, type, duration, time };
    setToasts(prevToasts => [...prevToasts, toast]);

    setTimeout(() => {
      removeToast(id);
    }, duration);
  };

  const removeToast = (id) => {
    setToasts(prevToasts => prevToasts.filter(toast => toast.id !== id));
  };

  const value = {
    toasts,
    addToast,
    removeToast,
    success: (message, duration) => addToast(message, 'success', duration),
    error: (message, duration) => addToast(message, 'error', duration),
    warning: (message, duration) => addToast(message, 'warning', duration),
    info: (message, duration) => addToast(message, 'info', duration)
  };

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
    </ToastContext.Provider>
  );
};