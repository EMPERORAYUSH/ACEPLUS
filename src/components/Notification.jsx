import React from 'react';

const Notification = ({ message, type = 'info' }) => { // Default type is 'info'
  if (!message) {
    return null; // Don't render anything if there's no message
  }

  return (
    <div className={`notification ${type}`}> 
      {message}
    </div>
  );
};

export default Notification;