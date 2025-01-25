import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';

function UpdatePopup({ isOpen, onClose, updates }) {
  const renderChange = (change) => {
    if (typeof change === 'string') {
      return <strong>{change}</strong>;
    }
    return <strong>{change.title}</strong>;
  };

  return (
    <AnimatePresence mode="wait">
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="update-popup-overlay"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.95, y: 20, opacity: 0 }}
            animate={{ 
              scale: 1, 
              y: 0, 
              opacity: 1,
              transition: { 
                type: "spring",
                stiffness: 300,
                damping: 30 
              }
            }}
            exit={{ 
              scale: 0.95,
              opacity: 0,
              transition: { 
                duration: 0.15,
                ease: "easeOut"
              }
            }}
            className="update-popup"
            onClick={e => e.stopPropagation()}
          >
            <h2>What's New</h2>
            {updates.map((update, index) => (
              <motion.div
                key={update.version}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="version-info"
              >
                <div className="flex justify-between items-center mb-2">
                  <h3 className="text-lg font-semibold">
                    Version {update.version}
                  </h3>
                  <span className="text-sm text-gray-400">{update.date}</span>
                </div>
                <ul className="changes-list">
                  {update.changes.map((change, idx) => (
                    <motion.li
                      key={idx}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 + idx * 0.05 }}
                    >
                      <div className="change-item">
                        <div className="change-title">
                          <span className="bullet">•</span>
                          {renderChange(change)}
                        </div>
                        {typeof change === 'object' && change.description && (
                          <motion.p
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: index * 0.1 + idx * 0.05 + 0.1 }}
                            className="change-description"
                          >
                            {change.description}
                          </motion.p>
                        )}
                      </div>
                    </motion.li>
                  ))}
                </ul>
              </motion.div>
            ))}
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="update-popup-button"
              onClick={onClose}
            >
              Got it!
            </motion.button>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default UpdatePopup;