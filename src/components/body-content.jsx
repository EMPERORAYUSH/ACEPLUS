import React, { useEffect, useState } from 'react';

import Notification from './Notification';
import { Navigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import styled from 'styled-components';
import UpdatePopup from './UpdatePopup';
import LeaderboardPopup from './LeaderboardPopup';
import { api } from '../utils/api';

// Styled Components for skeleton loading
const SkeletonPulse = styled.div`
  .skeleton {
    background: transparent;
  }
  `;

// Animation variants
const cardVariants = {
  hidden: { 
    opacity: 0, 
    scale: 0.8, 
    y: 50 
  },
  visible: (index) => ({ 
    opacity: 1, 
    scale: 1, 
    y: 0,
    transition: {
      duration: 0.8,
      delay: index * 0.2,
      type: "spring",
      stiffness: 100,
      damping: 15
    }
  })
};

const fadeTransition = {
  hidden: {
    opacity: 0,
    scale: 0.95,
    filter: 'blur(10px)',
  },
  visible: {
    opacity: 1,
    scale: 1,
    filter: 'blur(0px)',
    transition: {
      duration: 0.5,
      ease: "easeOut"
    }
  },
  exit: {
    opacity: 0,
    scale: 1.05,
    filter: 'blur(10px)',
    transition: {
      duration: 0.3,
      ease: "easeIn"
    }
  }
};

// Skeleton Card Component
const SkeletonCard = () => (
  <SkeletonPulse>
    <div className="card skeleton">
      <div className="skeleton-title"></div>
      <div className="skeleton-value"></div>
    </div>
  </SkeletonPulse>
);

function Content() {
  const initialCardData = [
    { title: "Total Exams Attempted", value: "NA" },
    { title: "Total Marks Attempted", value: "NA" },
    { title: "Total Marks Gained", value: "NA" },
    { title: "Average Percentage", value: "NA" },
  ];

  const [cardData, setCardData] = useState(initialCardData);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showUpdatePopup, setShowUpdatePopup] = useState(false);
  const [updates, setUpdates] = useState([]);
  const [showLeaderboardPopup, setShowLeaderboardPopup] = useState(false);
  const [leaderboardData, setLeaderboardData] = useState(null);
  const [animateNumbers, setAnimateNumbers] = useState(false);

  useEffect(() => {
    const handleAnimateCards = () => {
      setTimeout(() => {
        setAnimateNumbers(true);
      }, 1500);
    };

    window.addEventListener('animateCards', handleAnimateCards);
    return () => window.removeEventListener('animateCards', handleAnimateCards);
  }, []);

  const checkForUpdates = async () => {
    try {
      const data = await api.getUpdates();
      if (data && data.version) {
        const lastSeenUpdate = localStorage.getItem('lastSeenUpdate');
        if (!lastSeenUpdate || lastSeenUpdate !== data.version) {
          setUpdates([data]);
          setShowUpdatePopup(true);
        }
      }
    } catch (error) {
      console.error('Failed to fetch updates:', error);
    }
  };

  const handleClosePopup = () => {
    if (updates.length > 0) {
      localStorage.setItem('lastSeenUpdate', updates[0].version);
    }
    setShowUpdatePopup(false);
  };

  const fetchLeaderboard = async () => {
    try {
      const data = await api.getLeaderboard();
      const storedLeaderboard = localStorage.getItem('leaderboardData');
      
      if (!storedLeaderboard || JSON.stringify(data) !== storedLeaderboard) {
        setLeaderboardData(data);
        setShowLeaderboardPopup(true);
        localStorage.setItem('leaderboardData', JSON.stringify(data));
      }
    } catch (error) {
      console.error('Failed to fetch leaderboard:', error);
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      try {
        if (!localStorage.getItem('token')) {
          throw new Error('Unauthorized');
        }

        const data = await api.getOverviewStats();
        let formattedData;
        
        if (data && data.subjects) {
          const subjects = Object.values(data.subjects);
          const totalExams = subjects.reduce((acc, curr) => acc + (curr.exams_given || 0), 0);
          const totalMarks = subjects.reduce((acc, curr) => acc + ((curr.exams_given || 0) * 100), 0);
          const totalGained = subjects.reduce((acc, curr) => acc + ((curr.average_percentage || 0) * (curr.exams_given || 0)), 0);
          const avgPercentage = subjects.length > 0 ? 
            subjects.reduce((acc, curr) => acc + (curr.average_percentage || 0), 0) / subjects.length : 0;

          formattedData = [
            { title: "Total Exams Attempted", value: totalExams },
            { title: "Total Marks Attempted", value: totalMarks },
            { title: "Total Marks Gained", value: totalGained.toFixed(0) },
            { title: "Average Percentage", value: avgPercentage.toFixed(2) + "%" },
          ];
        } else {
          formattedData = [
            { title: "Total Exams Attempted", value: 0 },
            { title: "Total Marks Attempted", value: 0 },
            { title: "Total Marks Gained", value: 0 },
            { title: "Average Percentage", value: "0.00%" },
          ];
        }
        
        setCardData(formattedData);
        await checkForUpdates();
        await fetchLeaderboard();
      } catch (error) {
        setError(error.message);
        if (error.message === 'Unauthorized access') {
          Navigate('/login');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleCloseLeaderboard = () => {
    setShowLeaderboardPopup(false);
    window.dispatchEvent(new Event('animateCards'));
  };

  return (
    <>
      <UpdatePopup
        isOpen={showUpdatePopup}
        onClose={() => {
          handleClosePopup();
          if (leaderboardData) {
            setShowLeaderboardPopup(true);
          }
        }}
        updates={updates}
      />
      {leaderboardData && (
        <LeaderboardPopup
          isOpen={showLeaderboardPopup}
          onClose={handleCloseLeaderboard}
          leaderboardData={leaderboardData}
          updatePopupOpen={showUpdatePopup}
        />
      )}
      <motion.div 
        className="content"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1 }}
      >
        {error && <Notification message={error} type="error" />}
        <div className="container">
          {cardData.map((card, index) => (
            <motion.div
              key={index}
              className="card"
              variants={cardVariants}
              initial="hidden"
              animate="visible"
              custom={index}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <AnimatePresence mode="wait">
                {loading ? (
                  <motion.div
                    key="skeleton"
                    initial="hidden"
                    animate="hidden"
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
                  >
                    <div className="info-text">{card.title}</div>
                    <motion.div 
                      className="number"
                      initial={{ scale: animateNumbers ? 0 : 1, opacity: animateNumbers ? 0 : 1 }}
                      animate={{ scale: 1, opacity: 1 }}
                      transition={{
                        type: "spring",
                        stiffness: 200,
                        damping: 12,
                        delay: index * 0.1
                      }}
                    >
                      {card.value}
                    </motion.div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </>
  );
}

export default Content;