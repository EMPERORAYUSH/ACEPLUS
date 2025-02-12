import React from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { IoClose } from 'react-icons/io5';

const PopupOverlay = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  z-index: 9998;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  @media (min-width: 769px) {
    display: none;
  }
`;

const PopupContent = styled(motion.div)`
  position: relative;
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0);
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
  border-top-left-radius: 20px;
  border-top-right-radius: 20px;
  padding: 1.5rem;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.3);
  z-index: 9999;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  max-height: 90vh;
  overflow-y: auto;
  
  .drag-handle {
    width: 40px;
    height: 4px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 2px;
    margin: -0.5rem auto 1rem;
  }
  .popup-title {
    text-align: center;
    margin: 0 0 1rem;
    font-size: 1.25rem;
    font-weight: 600;
    color: #fff;
    padding: 0 2rem; /* Make space for close button */
  }
`;

const CloseButton = styled(motion.button)`
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.8);
  z-index: 10000;
  
  &:hover {
    color: #fff;
  }
  
  svg {
    width: 24px;
    height: 24px;
  }
`;

const MobilePopup = ({ isOpen, onClose, children, title }) => {
  return (
    <AnimatePresence>
      {isOpen && (
        <PopupOverlay
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
        >
          <PopupContent
            initial={{ y: "100%" }}
            animate={{ y: 0 }}
            exit={{ y: "100%" }}
            transition={{
              type: "spring",
              damping: 25,
              stiffness: 300
            }}
            drag="y"
            dragConstraints={{ top: 0 }}
            dragElastic={0.2}
            onDragEnd={(e, { offset, velocity }) => {
              if (offset.y > 200 || velocity.y > 300) {
                onClose();
              }
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="drag-handle" />
            <CloseButton
              onClick={onClose}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              <IoClose />
            </CloseButton>
            {title && (
              <motion.h2
                className="popup-title"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                {title}
              </motion.h2>
            )}
            {children}
          </PopupContent>
        </PopupOverlay>
      )}
    </AnimatePresence>
  );
};

export default MobilePopup;