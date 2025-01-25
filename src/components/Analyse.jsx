import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import styled from 'styled-components';
import SubjectDetails from './SubjectDetails';
import { api } from '../utils/api';

// Styled Components
const TypewriterContainer = styled(motion.span)`
  .letter {
    display: inline-block;
  }

  .typing-cursor {
    user-select: none;
    animation: blink 0.5s step-end infinite;
  }

  @keyframes blink {
    from, to { opacity: 1; }
    50% { opacity: 0; }
  }
`;

const SkeletonPulse = styled.div`
  @keyframes pulse {
    0% { opacity: 1; }
    50% { opacity: 0.4; }
    100% { opacity: 1; }
  }
  animation: pulse 1.5s ease-in-out infinite;
`;

const PageHeader = styled(motion.div)`
  margin: 0 0 2rem;
  padding-top: 1rem;
  position: relative;
  text-align: center;

  h1 {
    font-size: 1.6rem;
    font-weight: 700;
    letter-spacing: -0.5px;
    text-transform: uppercase;
  }

  @media (min-width: 768px) {
    h1 {
      font-size: 2rem;
    }
  }

  @media (min-width: 1024px) {
    h1 {
      font-size: 2.2rem;
    }
  }

  &::after {
    content: '';
    position: absolute;
    bottom: -0.8rem;
    left: 50%;
    transform: translateX(-50%);
    width: 100px;
    height: 3px;
    border-radius: 2px;
    opacity: 0.8;
  }
`;

// Animation Variants
const fadeTransition = {
  hidden: {
    opacity: 0,
    scale: 0.95,
    filter: 'blur(10px)',
    willChange: 'opacity, transform, filter'
  },
  visible: {
    opacity: 1,
    scale: 1,
    filter: 'blur(0px)',
    transition: {
      duration: 0.5,
      ease: [0.4, 0, 0.2, 1]
    }
  },
  exit: {
    opacity: 0,
    scale: 1.05,
    filter: 'blur(10px)',
    transition: {
      duration: 0.3,
      ease: [0.4, 0, 1, 1]
    }
  }
};

const cardVariants = {
  hidden: { 
    opacity: 0, 
    scale: 0.8, 
    y: 50,
    willChange: 'opacity, transform'
  },
  visible: (index) => ({ 
    opacity: 1, 
    scale: 1, 
    y: 0,
    transition: {
      duration: 0.5,
      delay: index * 0.1,
      type: "spring",
      stiffness: 100,
      damping: 20,
      mass: 0.5
    }
  })
};

// Custom Hook for Typewriter Effect
const useTypewriterFade = (text, speed = 40, delay = 200) => {
  const [displayText, setDisplayText] = useState('');
  const [isFinished, setIsFinished] = useState(false);

  useEffect(() => {
    let typingTimer;
    
    const startTyping = () => {
      typingTimer = setInterval(() => {
        setDisplayText(prev => {
          if (prev.length < text.length) {
            return text.slice(0, prev.length + 1);
          } else {
            clearInterval(typingTimer);
            setIsFinished(true);
            return prev;
          }
        });
      }, speed);
    };

    const delayTimer = setTimeout(() => {
      setDisplayText('');
      startTyping();
    }, delay);

    return () => {
      clearTimeout(delayTimer);
      clearInterval(typingTimer);
    };
  }, [text, speed, delay]);

  return { displayText, isFinished };
};

// TypewriterFadeText Component
const TypewriterFadeText = ({ text, delay = 0, onFinish }) => {
  const { displayText, isFinished } = useTypewriterFade(text, 40, delay);

  useEffect(() => {
    if (isFinished && onFinish) {
      onFinish();
    }
  }, [isFinished, onFinish]);

  return (
    <TypewriterContainer>
      {displayText.split('').map((char, index) => (
        <motion.span
          key={index}
          className="letter"
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{
            duration: 0.15,
            ease: "easeOut"
          }}
        >
          {char === ' ' ? '\u00A0' : char}
        </motion.span>
      ))}
      {!isFinished && (
        <motion.span
          className="typing-cursor"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{
            duration: 0.5,
            repeat: Infinity,
            repeatType: "reverse"
          }}
        >
          |
        </motion.span>
      )}
    </TypewriterContainer>
  );
};

// Skeleton Card Component
const SkeletonCard = () => (
  <SkeletonPulse>
    <div className="analysis-card skeleton">
      <div className="card-icon skeleton-icon"></div>
      <div className="card-content">
        <p className="skeleton-text"></p>
        <p className="skeleton-text"></p>
        <p className="skeleton-text"></p>
      </div>
      <div className="card-button skeleton-button"></div>
    </div>
  </SkeletonPulse>
);

// Main Analysis Component
const Analysis = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [subjects, setSubjects] = useState([]);
  const [showButtons, setShowButtons] = useState({});
  const navigate = useNavigate();
  const [selectedSubject, setSelectedSubject] = useState(null);
  const [isSidebarExpanded, setIsSidebarExpanded] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await api.getOverviewStats();
        const overviewStats = data.subjects;
        const subjectData = Object.keys(overviewStats)
          .sort((a, b) => {
            if (a === 'English') return 1;
            if (b === 'English') return -1;
            return 0;
          })
          .map(subject => ({
            name: subject,
            icon: getSubjectIcon(subject),
            color: getSubjectColor(subject),
            stats: overviewStats[subject]
          }));
        setSubjects(subjectData);
      } catch (error) {
        console.error('Error fetching subjects:', error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchData();
  }, []);

  const getSubjectIcon = (subject) => {
    const icons = { Math: '📐', Science: '🧪', English: '📚', SS: '🌍' };
    return icons[subject] || '📚';
  };

  const getSubjectColor = (subject) => {
    const colors = { Math: '#4CAF50', Science: '#2196F3', English: '#FFC107', SS: '#9C27B0' };
    return colors[subject] || '#607D8B';
  };

  const handleViewDetails = (subject, event) => {
    // Get the clicked card's position and size
    const card = event.currentTarget;
    const rect = card.getBoundingClientRect();
    
    setSelectedSubject({
      ...subject,
      initialPosition: {
        top: rect.top,
        left: rect.left,
        width: rect.width,
        height: rect.height
      }
    });
  };

  const handleTypewriterFinish = (subjectName) => {
    setShowButtons(prev => ({ ...prev, [subjectName]: true }));
  };

  const handleClose = () => {
    setSelectedSubject(null);
  };

  // Add effect to listen for sidebar hover
  useEffect(() => {
    const sidebar = document.querySelector('.sidebar');
    
    const handleMouseEnter = () => setIsSidebarExpanded(true);
    const handleMouseLeave = () => setIsSidebarExpanded(false);

    if (sidebar) {
      sidebar.addEventListener('mouseenter', handleMouseEnter);
      sidebar.addEventListener('mouseleave', handleMouseLeave);
    }

    return () => {
      if (sidebar) {
        sidebar.removeEventListener('mouseenter', handleMouseEnter);
        sidebar.removeEventListener('mouseleave', handleMouseLeave);
      }
    };
  }, []);

  return (
    <motion.div 
      className="analysis-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
      style={{ willChange: 'opacity' }}
    >
      <PageHeader
        initial={{ y: -20 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1>Subject Analysis</h1>
      </PageHeader>
      <div className="card-grid">
        {(isLoading ? Array(4).fill(null) : subjects).map((subject, index) => (
          <motion.div
            key={index}
            className={`card-wrapper ${isLoading ? 'loading' : 'loaded'}`}
            variants={cardVariants}
            initial="hidden"
            animate="visible"
            custom={index}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <AnimatePresence mode="wait">
              {isLoading ? (
                <motion.div
                  key="skeleton"
                  initial="hidden"
                  animate="visible"
                  exit="exit"
                  variants={fadeTransition}
                >
                  <SkeletonCard />
                </motion.div>
              ) : (
                <motion.div
                  key="content"
                  initial="hidden"
                  animate="visible"
                  variants={fadeTransition}
                  className="analysis-card"
                  style={{ '--card-color': subject.color }}
                >
                  <motion.div 
                    className="card-icon"
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ delay: index * 0.2 + 0.3, type: "spring", stiffness: 200 }}
                  >
                    {subject.icon}
                  </motion.div>
                  <h2 className="card-title">
                    <TypewriterFadeText 
                      text={subject.name} 
                      delay={500} 
                      onFinish={() => handleTypewriterFinish(subject.name)} 
                    />
                  </h2>
                  <div className="card-content">
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.2 }}
                    >
                      <TypewriterFadeText 
                        text={`Exams: ${subject.stats.exams_given}`} 
                        delay={1500} 
                        onFinish={() => handleTypewriterFinish(subject.name)} 
                      />
                    </motion.p>
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.4 }}
                    >
                      <TypewriterFadeText 
                        text={`Average Score: ${subject.stats.average_percentage.toFixed(2)}%`}
                        delay={2500}
                        onFinish={() => handleTypewriterFinish(subject.name)}
                      />
                    </motion.p>
                    <motion.p
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.6 }}
                    >
                      <TypewriterFadeText 
                        text={`Highest Score: ${subject.stats.highest_marks}`}
                        delay={3500}
                        onFinish={() => handleTypewriterFinish(subject.name)}
                      />
                    </motion.p>
                  </div>
                  <motion.button 
                    className="card-button" 
                    onClick={(e) => handleViewDetails(subject, e)}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ 
                      opacity: showButtons[subject.name] ? 1 : 0,
                      y: showButtons[subject.name] ? 0 : 20
                    }}
                    transition={{ 
                      duration: 0.3,
                      type: "spring",
                      stiffness: 200,
                      damping: 20,
                      mass: 0.5
                    }}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    style={{ 
                      willChange: 'transform, opacity',
                      backfaceVisibility: 'hidden',
                      WebkitBackfaceVisibility: 'hidden'
                    }}
                  >
                    View Details
                  </motion.button>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>
      <AnimatePresence>
        {selectedSubject && (
          <motion.div 
            className={`subject-popup-overlay ${isSidebarExpanded ? 'sidebar-expanded' : ''}`}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleClose}
          >
            <motion.div
              className="subject-popup"
              initial={{
                position: 'fixed',
                top: selectedSubject.initialPosition.top,
                left: selectedSubject.initialPosition.left,
                width: selectedSubject.initialPosition.width,
                height: selectedSubject.initialPosition.height,
                borderRadius: '15px',
                willChange: 'transform'
              }}
              animate={{
                top: '50%',
                left: '50%',
                width: '80vw',
                height: '80vh',
                y: '-50%',
                x: '-50%',
              }}
              exit={{
                top: selectedSubject.initialPosition.top,
                left: selectedSubject.initialPosition.left,
                width: selectedSubject.initialPosition.width,
                height: selectedSubject.initialPosition.height,
                borderRadius: '15px'
              }}
              transition={{ 
                type: "spring",
                damping: 30,
                stiffness: 200,
                mass: 0.8,
                restDelta: 0.001
              }}
              style={{
                backfaceVisibility: 'hidden',
                WebkitBackfaceVisibility: 'hidden',
                perspective: 1000,
                WebkitPerspective: 1000
              }}
              onClick={e => e.stopPropagation()}
            >
              <motion.button
                className="close-button"
                onClick={handleClose}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
              >
                ��
              </motion.button>
              <div className="popup-content">
                <SubjectDetails subject={selectedSubject.name.toLowerCase()} />
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default Analysis;