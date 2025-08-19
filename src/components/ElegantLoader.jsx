import React from 'react';
import { motion } from 'framer-motion';
import styled from 'styled-components';

const LoaderContainer = styled(motion.div)`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: ${props => props.fullHeight ? '100vh' : '50vh'};
  background: ${props => props.fullHeight ? 'var(--background-color, #121212)' : 'transparent'};
  position: ${props => props.fullHeight ? 'fixed' : 'relative'};
  top: ${props => props.fullHeight ? '0' : 'auto'};
  left: ${props => props.fullHeight ? '0' : 'auto'};
  right: ${props => props.fullHeight ? '0' : 'auto'};
  bottom: ${props => props.fullHeight ? '0' : 'auto'};
  z-index: ${props => props.fullHeight ? '1000' : '1'};
  width: 100%;
`;

const LoaderWrapper = styled(motion.div)`
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;,
`;

const SpinnerContainer = styled(motion.div)`
  position: relative;
  width: 80px;
  height: 80px;
`;

const OuterRing = styled(motion.div)`
  position: absolute;
  top: 0;
  left: 0;
  width: 80px;
  height: 80px;
  border: 3px solid transparent;
  border-top: 3px solid #4CAF50;
  border-right: 3px solid rgba(76, 175, 80, 0.3);
  border-radius: 50%;
`;


const InnerRing = styled(motion.div)`
  position: absolute;
  top: 10px;
  left: 10px;
  width: 60px;
  height: 60px;
  border: 2px solid transparent;
  border-top: 2px solid #2196F3;
  border-left: 2px solid rgba(33, 150, 243, 0.3);
  border-radius: 50%;,
`;

const CenterDot = styled(motion.div)`
  position: absolute;
  top: 34px;
  left: 34px;
  width: 12px;
  height: 12px;
  background: linear-gradient(135deg, #4CAF50, #2196F3);
  border-radius: 50%;
  box-shadow: 0 0 20px rgba(76, 175, 80, 0.5);
  z-index: 10;
`;

const LoadingText = styled(motion.div)`
  color: #ffffff;
  font-size: 1.2rem;
  font-weight: 500;
  text-align: center;
  letter-spacing: 0.5px;
`;

const ProgressText = styled(motion.div)`
  color: #a0aec0;
  font-size: 0.9rem;
  text-align: center;
  margin-top: 0.5rem;
`;

const FloatingDots = styled.div`
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
`;

const Dot = styled(motion.div)`
  width: 8px;
  height: 8px;
  background: linear-gradient(135deg, #4CAF50, #2196F3);
  border-radius: 50%;
`;

const ElegantLoader = ({ 
  message = "Loading...", 
  subMessage = "Please wait", 
  progress = null,
  fullHeight = false 
}) => {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: {
        duration: 0.3,
        ease: "easeOut"
      }
    },
    exit: {
      opacity: 0,
      transition: {
        duration: 0.2,
        ease: 'easeIn'
      },
    },
  };

  const wrapperVariants = {
    hidden: { 
      opacity: 0,
      y: 20,
      scale: 0.9
    },
    visible: { 
      opacity: 1,
      y: 0,
      scale: 1,
      transition: {
        duration: 0.5,
        ease: "easeOut",
        staggerChildren: 0.1
      }
    },
  };

  const outerRingVariants = {
    animate: {
      rotate: 360,
      transition: {
        duration: 2,
        ease: "linear",
        repeat: Infinity
      }
    }
  };

  const innerRingVariants = {
    animate: {
      rotate: -360,
      transition: {
        duration: 1.5,
        ease: "linear",
        repeat: Infinity
      }
    }
  };

  const centerDotVariants = {
    animate: {
      scale: [1, 1.2, 1],
      opacity: [0.7, 1, 0.7],
      transition: {
        duration: 2,
        ease: "easeInOut",
        repeat: Infinity
      }
    }
  };

  const textVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: { 
      opacity: 1, 
      y: 0,
      transition: {
        duration: 0.4,
        ease: "easeOut"
      }
    }
  };

  const dotVariants = {
    animate: (i) => ({
      y: [0, -10, 0],
      transition: {
        duration: 1.5,
        ease: "easeInOut",
        repeat: Infinity,
        delay: i * 0.2
      }
    })
  };

  return (
    <LoaderContainer 
      fullHeight={fullHeight}
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      exit="exit"
    >
      <LoaderWrapper variants={wrapperVariants}>
        <SpinnerContainer>
          <OuterRing 
            variants={outerRingVariants}
            animate="animate"
          />
          <InnerRing 
            variants={innerRingVariants} 
            animate="animate"
          />
          <CenterDot 
            variants={centerDotVariants}
            animate="animate"
          />
        </SpinnerContainer>

        <motion.div variants={textVariants}>
          <LoadingText>{message}</LoadingText>
          <ProgressText>
            {progress !== null ? `${Math.round(progress)}%` : subMessage}
          </ProgressText>
        </motion.div>

        <FloatingDots>
          {[0, 1, 2].map((i) => (
            <Dot
              key={i}
              variants={dotVariants}
              animate="animate"
              custom={i}
            />
          ))}
        </FloatingDots>
      </LoaderWrapper>
    </LoaderContainer>
  );
};

export default ElegantLoader;