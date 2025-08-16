import React, { useEffect, useState } from 'react';

import Notification from './Notification';
import { Navigate, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import UpdatePopup from './UpdatePopup';
import LeaderboardPopup from './LeaderboardPopup';
import { api } from '../utils/api';
import './body-content.css';

// Animation variants
const cardVariants = {
  hidden: { 
    opacity: 0, 
    scale: 0.9, 
    y: 40 
  },
  visible: (index) => ({
    opacity: 1, 
    scale: 1, 
    y: 0,
    transition: {
      duration: 0.6,
      delay: index * 0.15,
      ease: "easeOut"
    }
  })
};

const fadeTransition = {
  hidden: {
    opacity: 0,
    scale: 0.95,
    filter: 'blur(10px)'
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

function Content() {
  const initialCardData = [
    { title: "Total Exams Attempted", value: "NA" },
    { title: "Total Marks Attempted", value: "NA" },
    { title: "Total Marks Gained", value: "NA" },
    { title: "Average Percentage", value: "NA" }
  ];

  const navigate = useNavigate();
  const [cardData, setCardData] = useState(initialCardData);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showUpdatePopup, setShowUpdatePopup] = useState(false);
  const [updates, setUpdates] = useState([]);
  const [showLeaderboardPopup, setShowLeaderboardPopup] = useState(false);
  const [leaderboardData, setLeaderboardData] = useState(null);
  const [animateNumbers, setAnimateNumbers] = useState(false);
  const [currentLeaderboardId, setCurrentLeaderboardId] = useState(null);

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
      const data = await api.getLeaderboard(1, 20); 
      const storedLeaderboardId = localStorage.getItem('lastSeenLeaderboardId'); 
      const newLeaderboardId = data.leaderboard_id; 

      setCurrentLeaderboardId(newLeaderboardId);

      // Initialize leaderboard data with first page
      const filteredLeaderboard = data.leaderboard
        .filter(entry => entry.name !== 'UNKNOWN')
        .map((entry, index) => ({
          ...entry, rank: index + 1 
        })); 
      data.leaderboard = filteredLeaderboard;

      if (newLeaderboardId && newLeaderboardId !== storedLeaderboardId) {
        setLeaderboardData(data);
        setShowLeaderboardPopup(true);
      }
    } catch (error) {
      console.error('Failed to fetch leaderboard:', error);
    }
  };

  useEffect(() => {
    let isMounted = true; 
    const fetchData = async () => {
      try {
        if (!localStorage.getItem('token')) {
          throw new Error('Unauthorized');
        }

        // Call all APIs concurrently using Promise.all
        const [userStatsResponse] = await Promise.all([
          api.getOverviewStats(),
          checkForUpdates(),
          fetchLeaderboard()
        ]);

        if (userStatsResponse && userStatsResponse.version) {
          const clientVersion = localStorage.getItem('version');
          if (clientVersion !== userStatsResponse.version) {
            localStorage.clear();
            localStorage.setItem('version', userStatsResponse.version);
            navigate('/login');
            return;
          }
        }

        let formattedData;
        const overviewData = userStatsResponse.stats;

        if (overviewData && Array.isArray(overviewData) && overviewData.length > 0) {
          const stats = {
            total_exams: overviewData[0]?.total_exams,
            total_marks: overviewData[1]?.total_marks,
            marks_gained: overviewData[2]?.marks_gained,
            average_percentage: overviewData[3]?.average_percentage
          };
          formattedData = [
            { title: "Total Exams Attempted", value: stats.total_exams || 0 },
            { title: "Total Marks Attempted", value: stats.total_marks || 0 },
            { title: "Total Marks Gained", value: stats.marks_gained || 0 },
            { title: "Average Percentage", value: stats.average_percentage || "0.00%" }
          ];
        } else {
          formattedData = [
            { title: "Total Exams Attempted", value: 0 },
            { title: "Total Marks Attempted", value: 0 },
            { title: "Total Marks Gained", value: 0 },
            { title: "Average Percentage", value: "0.00%" }
          ];
        } if (isMounted) {
          setCardData(formattedData);
        }
      } catch (error) {
        if (isMounted) {
          setError(error.message);
        }
        if (error.message === 'Unauthorized access') {
          navigate('/login');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchData();

    return () => {
      isMounted = false;
    };
  }, []);

  const handleCloseLeaderboard = () => {
    setShowLeaderboardPopup(false);
    window.dispatchEvent(new Event('animateCards'));
    if (currentLeaderboardId) {
      localStorage.setItem('lastSeenLeaderboardId', currentLeaderboardId);
    }
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
          leaderboardId={currentLeaderboardId}
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
                    <div className="card skeleton">
                      <div className="skeleton-title"></div>
                      <div className="skeleton-value"></div>
                    </div>
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
                      initial={{
                        scale: animateNumbers ? 0 : 1,
                        opacity: animateNumbers ? 0 : 1
                      }}
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
