import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import styled from 'styled-components';
import { FaCoins } from 'react-icons/fa';

const PopupOverlay = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
`;

const PopupContent = styled(motion.div)`
  background: #1c1c1c;
  border-radius: 16px;
  padding: 2.5rem;
  width: 90%;
  max-width: 380px;
  text-align: center;
  border: 1px solid #4a90e2;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  position: relative;
`;

const Sparkles = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  overflow: hidden;
`;

const Sparkle = styled(motion.div)`
  position: absolute;
  background: #fdd835;
  border-radius: 50%;
`;

const Title = styled.h2`
  color: #4a90e2;
  margin-bottom: 1.5rem;
  font-size: 1.8rem;
`;

const CoinsDisplay = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  color: #fdd835;
  font-size: 3rem;
  font-weight: bold;
  margin-bottom: 2rem;
`;

const Message = styled.p`
  color: #e0e0e0;
  font-size: 1.1rem;
  line-height: 1.6;
`;

const CoinsEarnedPopup = ({ coins, onClose }) => {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    if (coins > 0) {
      setIsOpen(true);
      const timer = setTimeout(() => {
        handleClose();
      }, 3000); // Auto-close after 3 seconds
      return () => clearTimeout(timer);
    }
  }, [coins]);

  const handleClose = () => {
    setIsOpen(false);
    if (onClose) {
      onClose();
    }
  };

  const sparkleVariants = {
    initial: { scale: 0, opacity: 0 },
    animate: (i) => ({
      scale: [0, 1.2, 0],
      opacity: [0, 1, 0],
      transition: {
        duration: 1.5,
        delay: i * 0.1,
        repeat: Infinity,
        repeatDelay: 2
      }
    })
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <PopupOverlay
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={handleClose}
        >
          <PopupContent
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 25 }}
          >
            <Sparkles>
              {[...Array(15)].map((_, i) => (
                <Sparkle
                  key={i}
                  custom={i}
                  variants={sparkleVariants}
                  initial="initial"
                  animate="animate"
                  style={{
                    top: `${Math.random() * 100}%`,
                    left: `${Math.random() * 100}%`,
                    width: `${Math.random() * 6 + 2}px`,
                    height: `${Math.random() * 6 + 2}px`,
                  }}
                />
              ))}
            </Sparkles>
            <Title>You've Earned Coins!</Title>
            <CoinsDisplay>
              <FaCoins /> +{coins}
            </CoinsDisplay>
            <Message>Keep up the great work!</Message>
          </PopupContent>
        </PopupOverlay>
      )}
    </AnimatePresence>
  );
};

export default CoinsEarnedPopup;