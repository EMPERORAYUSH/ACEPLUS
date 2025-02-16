import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import Notification from "./Notification";
import "./History.css";
import { api } from '../utils/api';

const SubjectIcon = ({ subject }) => {
  const icons = {
    Math: "calculator",
    Science: "flask", 
    English: "book",
    SS: "globe-americas",
    Physics: "atom",
    Chemistry: "vial",
    Biology: "dna",
    History: "landmark",
    Geography: "mountain",
    Computer: "laptop-code"
  };
  
  // No need to lowercase since we're matching exact API values
  const iconName = icons[subject] || 'graduation-cap';
  
  return (
    <div className="subject-icon">
      <i className={`fas fa-${iconName}`} aria-label={subject}></i>
    </div>
  );
};

const ProgressRing = ({ percentage }) => {
  const radius = 15;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;
  
  // Get color based on percentage
  const getColor = (percentage) => {
    if (percentage >= 80) return "#4CAF50";      // Green for excellent
    if (percentage >= 60) return "#FFC107";      // Yellow for good
    if (percentage >= 40) return "#FF9800";      // Orange for average
    return "#FF5252";                            // Red for needs improvement
  };

  const color = getColor(percentage);
  
  return (
    <div className="progress-ring">
      <svg viewBox="0 0 36 36">
        {/* Background circle */}
        <circle
          cx="18"
          cy="18"
          r={radius}
          fill="none"
          stroke="rgba(255, 255, 255, 0.1)"
          strokeWidth="3"
        />
        {/* Progress circle */}
        <circle
          cx="18"
          cy="18"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="3"
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          style={{
            transform: 'rotate(-90deg)',
            transformOrigin: '50% 50%',
            transition: 'stroke-dashoffset 0.5s ease-in-out'
          }}
        />
        {/* Percentage text */}
        <text
          x="18"
          y="18"
          fill="white"
          fontSize="10"
          fontWeight="bold"
          dominantBaseline="middle"
          textAnchor="middle"
        >
          {Math.round(percentage)}%
        </text>
      </svg>
    </div>
  );
};

const HistoryCard = ({ exam, onClick }) => {
  const formatDate = (dateString) => {
    try {
      // Split the date string into components
      const [day, month, year] = dateString.split('-');
      // Create date object (month - 1 because months are 0-indexed)
      const date = new Date(year, month - 1, day);
      
      if (isNaN(date.getTime())) {
        return 'Invalid date';
      }
      
      // Format as relative time if less than 7 days old
      const now = new Date();
      const diffTime = Math.abs(now - date);
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      
      if (diffDays <= 7) {
        if (diffDays === 0) return 'Today';
        if (diffDays === 1) return 'Yesterday';
        return `${diffDays} days ago`;
      }
      
      // Otherwise format as date
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch (error) {
      console.error('Date parsing error:', error);
      return 'Invalid date';
    }
  };

  return (
    <motion.div
      className="exam-card"
      onClick={() => onClick(exam["exam-id"])}
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      whileHover={{ 
        scale: 1.02,
        y: -5,
        boxShadow: "0 8px 20px rgba(0, 0, 0, 0.3)",
        transition: {
          type: "spring",
          stiffness: 200,
          damping: 25
        },
        "@media (max-width: 768px)": {
          scale: 1.01,  // Smaller scale effect on mobile
          y: -2,  // Smaller lift effect
          boxShadow: "0 4px 12px rgba(0, 0, 0, 0.2)"  // Subtler shadow
        }
      }}
      whileTap={{ scale: 0.98 }}
      layout="position"
      transition={{
        layout: {
          type: "spring",
          stiffness: 200,
          damping: 25
        }
      }}
      style={{
        touchAction: "pan-x pan-y"  // Improve touch behavior
      }}
    >
      <div className="exam-card-header">
        <div className="subject-icon">
          <SubjectIcon subject={exam.subject} />
        </div>
        <div className="exam-info">
          <h3>{exam.subject}</h3>
          <span className="exam-date">{formatDate(exam.date)}</span>
        </div>
        <ProgressRing percentage={Math.round(exam.percentage)} />
      </div>
      <div className="exam-card-details">
        <div className="detail-grid">
          <div className="detail-item">
            <span className="detail-label">Questions</span>
            <span className="detail-value">{exam.totalQuestions}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Correct</span>
            <span className="detail-value">{exam.score}</span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Lessons</span>
            <span className="detail-value">
              {Array.isArray(exam.lessons) ? exam.lessons.length : exam.lessons}
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

const HistoryCardSkeleton = () => (
  <div className="exam-card skeleton">
    <div className="exam-card-header">
      <div className="subject-icon skeleton-circle"></div>
      <div className="exam-info">
        <div className="skeleton-text"></div>
        <div className="skeleton-text"></div>
      </div>
      <div className="skeleton-circle"></div>
    </div>
    <div className="exam-card-details">
      <div className="detail-grid">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="detail-item">
            <div className="skeleton-text"></div>
            <div className="skeleton-text"></div>
          </div>
        ))}
      </div>
    </div>
  </div>
);

const FilterTab = ({ subject, active, onClick }) => (
  <motion.button
    className={`filter-tab ${active ? 'active' : ''}`}
    onClick={onClick}
    whileHover={{ 
      scale: 1.05,
      transition: {
        type: "spring",
        stiffness: 200,
        damping: 20
      }
    }}
    whileTap={{ scale: 0.95 }}
    initial={{ opacity: 0, scale: 0.95 }}
    animate={{ 
      opacity: 1,
      scale: 1,
      transition: {
        type: "spring",
        stiffness: 200,
        damping: 25,
        mass: 1
      }
    }}
  >
    <SubjectIcon subject={subject} />
    <span>{subject}</span>
  </motion.button>
);

const History = () => {
  const [examHistory, setExamHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('All');
  const navigate = useNavigate();

  useEffect(() => {
    const fetchExamHistory = async () => {
      try {
        const data = await api.getUserExams();
        setExamHistory(data);
      } catch (error) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchExamHistory();
  }, [navigate]);

  const handleExamClick = (examId) => {
    navigate(`/exam/results/${examId}`);
  };

  const filteredExams = examHistory.filter(exam => {
    if (filter === 'All') return true;
    return exam.subject === filter;  // Exact match with API subject
  });

  const subjects = ['All', ...new Set(examHistory.map(exam => exam.subject))];

  return (
    <motion.div 
      className="history-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <motion.div 
        className="history-header"
        initial={{ y: -20 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1>Your Learning Journey</h1>
        {!loading && examHistory.length > 0 && (
          <div className="filter-tabs">
            {subjects.map(subject => (
              <FilterTab
                key={subject}
                subject={subject}
                active={filter === subject}
                onClick={() => setFilter(subject)}
              />
            ))}
          </div>
        )}
      </motion.div>

      {error && <Notification message={error} />}

      <AnimatePresence mode="wait">
        <motion.div 
          className="exam-grid"
          layout="position"
          style={{ overflow: "hidden" }}
          transition={{
            layout: {
              type: "spring",
              stiffness: 200,
              damping: 25,
              mass: 1
            }
          }}
        >
          {loading ? (
            Array(6).fill().map((_, index) => (
              <HistoryCardSkeleton key={`skeleton-${index}`} />
            ))
          ) : examHistory.length > 0 ? (
            <AnimatePresence mode="popLayout">
              {filteredExams
                .slice()
                .reverse()
                .map((exam, index) => (
                  <motion.div
                    key={`${exam["exam-id"]}-${index}`}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ 
                      opacity: 1,
                      scale: 1,
                      transition: {
                        type: "spring",
                        stiffness: 200,
                        damping: 25,
                        mass: 1,
                        delay: index * 0.03
                      }
                    }}
                    exit={{ 
                      opacity: 0,
                      scale: 0.95,
                      transition: {
                        duration: 0.2,
                        ease: "easeInOut"
                      }
                    }}
                    layout="position"
                    transition={{
                      layout: {
                        type: "spring",
                        stiffness: 200,
                        damping: 25,
                        mass: 1
                      }
                    }}
                    style={{ 
                      width: "100%",
                      height: "100%",
                      position: "relative"
                    }}
                  >
                    <HistoryCard
                      exam={exam}
                      onClick={handleExamClick}
                    />
                  </motion.div>
                ))}
            </AnimatePresence>
          ) : (
            <motion.div 
              className="empty-state"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              transition={{ type: "spring", duration: 0.6 }}
            >
              <div className="empty-state-icon">
                <i className="fas fa-graduation-cap"></i>
              </div>
              <h2>Start Your Learning Journey</h2>
              <p>Take your first exam to see your progress here!</p>
            </motion.div>
          )}
        </motion.div>
      </AnimatePresence>
    </motion.div>
  );
};

export default History;
