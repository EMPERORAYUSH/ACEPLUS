import React from 'react';
import { motion } from 'framer-motion';
import { FaCopy } from 'react-icons/fa';

const CopyableExamId = ({ examId }) => {
  const handleCopy = () => {
    navigator.clipboard.writeText(examId);
    const notification = document.createElement('div');
    notification.textContent = 'Exam ID copied!';
    notification.style.position = 'fixed';
    notification.style.bottom = '20px';
    notification.style.left = '50%';
    notification.style.transform = 'translateX(-50%)';
    notification.style.backgroundColor = '#4CAF50';
    notification.style.color = 'white';
    notification.style.padding = '10px 20px';
    notification.style.borderRadius = '5px';
    notification.style.zIndex = '1000';
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 2000);
  };

  return (
    <motion.div 
      style={{ 
        display: 'flex',
        alignItems: 'center',
        gap: '8px'
      }}
    >
      <motion.div 
        style={{
          cursor: 'pointer',
          padding: '8px 12px',
          backgroundColor: 'rgba(255, 255, 255, 0.05)',
          color: '#ffffff',
          borderRadius: '8px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          userSelect: 'all',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          fontSize: '1rem',
          fontFamily: 'monospace'
        }}
        whileHover={{ 
          scale: 1.02,
          backgroundColor: 'rgba(255, 255, 255, 0.08)',
          border: '1px solid rgba(255, 255, 255, 0.2)'
        }}
        whileTap={{ scale: 0.98 }}
        onClick={handleCopy}
        title="Click to copy exam ID"
      >
        <span>{examId}</span>
        <FaCopy style={{ fontSize: '0.9rem', opacity: 0.7 }} />
      </motion.div>
    </motion.div>
  );
};

export default CopyableExamId;
