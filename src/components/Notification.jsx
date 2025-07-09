import React from 'react';
import { FaInfoCircle, FaCheckCircle, FaExclamationTriangle, FaExclamationCircle } from 'react-icons/fa';

const Notification = ({ message, type = 'info' }) => { // Default type is 'info'
  if (!message) {
    return null; // Don't render anything if there's no message
  }

  const getIcon = () => {
    switch (type) {
      case 'success':
        return <FaCheckCircle />;
      case 'warning':
        return <FaExclamationTriangle />;
      case 'error':
        return <FaExclamationCircle />;
      default:
        return <FaInfoCircle />;
    }
  };

  return (
    <div className={`notification ${type}`}>
      <span className="notification-icon">{getIcon()}</span>
      <span className="notification-message">{message}</span>
    </div>
  );
};

export default Notification;