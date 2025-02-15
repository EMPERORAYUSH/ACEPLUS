import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import Notification from "./Notification";
import "./History.css";
import { api } from '../utils/api';

const pageVariants = {
  initial: {
    opacity: 0,
    y: 20
  },
  animate: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.6,
      ease: [0.22, 1, 0.36, 1]
    }
  },
  exit: {
    opacity: 0,
    y: -20,
    transition: {
      duration: 0.4
    }
  }
};

const containerVariants = {
  initial: { opacity: 0 },
  animate: {
    opacity: 1,
    transition: {
      staggerChildren: 0.05,
      delayChildren: 0.1
    }
  }
};

const itemVariants = {
  initial: { 
    opacity: 0,
    y: 20
  },
  animate: { 
    opacity: 1,
    y: 0,
    transition: {
      type: "spring",
      stiffness: 260,
      damping: 20
    }
  }
};

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
  
  const iconName = icons[subject] || 'graduation-cap';
  
  return (
    <div className="subject-icon">
      <i className={`fas fa-${iconName}`} aria-label={subject}></i>
    </div>
  );
};

const ProgressRing = ({ percentage }) => {
  const radius = 18;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;
  
  const getColor = (percentage) => {
    if (percentage >= 80) return "#22c55e";
    if (percentage >= 60) return "#eab308";
    if (percentage >= 40) return "#f97316";
    return "#ef4444";
  };

  return (
    <motion.div 
      className="progress-ring"
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ 
        type: "spring",
        stiffness: 260,
        damping: 20,
        delay: 0.1
      }}
    >
      <svg viewBox="0 0 48 48">
        <circle
          cx="24"
          cy="24"
          r={radius}
          fill="none"
          stroke="rgba(255, 255, 255, 0.1)"
          strokeWidth="3"
        />
        <motion.circle
          cx="24"
          cy="24"
          r={radius}
          fill="none"
          stroke={getColor(percentage)}
          strokeWidth="3"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset }}
          transition={{ duration: 1, ease: "easeOut" }}
          strokeLinecap="round"
          style={{
            transformOrigin: '50% 50%',
            transform: 'rotate(-90deg)'
          }}
        />
        <motion.text
          x="24"
          y="24"
          fill="white"
          fontSize="12"
          fontWeight="600"
          dominantBaseline="middle"
          textAnchor="middle"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          {Math.round(percentage)}%
        </motion.text>
      </svg>
    </motion.div>
  );
};

const StatsOverview = ({ examHistory }) => {
  const stats = {
    totalExams: examHistory.length,
    averageScore: examHistory.reduce((acc, exam) => acc + exam.percentage, 0) / examHistory.length || 0,
    totalQuestions: examHistory.reduce((acc, exam) => acc + exam.totalQuestions, 0),
    subjects: new Set(examHistory.map(exam => exam.subject)).size
  };

  return (
    <motion.div 
      className="stats-overview"
      variants={containerVariants}
      initial="initial"
      animate="animate"
    >
      <motion.div className="stat-item" variants={itemVariants}>
        <div className="stat-value">{stats.totalExams}</div>
        <div className="stat-label">Total Exams</div>
      </motion.div>
      <motion.div className="stat-item" variants={itemVariants}>
        <div className="stat-value">{Math.round(stats.averageScore)}%</div>
        <div className="stat-label">Average Score</div>
      </motion.div>
      <motion.div className="stat-item" variants={itemVariants}>
        <div className="stat-value">{stats.totalQuestions}</div>
        <div className="stat-label">Questions Answered</div>
      </motion.div>
      <motion.div className="stat-item" variants={itemVariants}>
        <div className="stat-value">{stats.subjects}</div>
        <div className="stat-label">Subjects Covered</div>
      </motion.div>
    </motion.div>
  );
};

const HistoryCard = ({ exam, onClick, index }) => {
  const cardRef = React.useRef(null);

  const handleMouseMove = (e) => {
    if (!cardRef.current) return;
    
    const rect = cardRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    cardRef.current.style.setProperty('--mouse-x', `${x}px`);
    cardRef.current.style.setProperty('--mouse-y', `${y}px`);
  };

  const formatDate = (dateString) => {
    try {
      const [day, month, year] = dateString.split('-');
      const date = new Date(year, month - 1, day);
      
      if (isNaN(date.getTime())) {
        return 'Invalid date';
      }
      
      const now = new Date();
      const diffTime = Math.abs(now - date);
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
      
      if (diffDays <= 7) {
        if (diffDays === 0) return 'Today';
        if (diffDays === 1) return 'Yesterday';
        return `${diffDays} days ago`;
      }
      
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
      ref={cardRef}
      className="exam-card"
      onClick={() => onClick(exam["exam-id"])}
      onMouseMove={handleMouseMove}
      variants={itemVariants}
      whileHover={{ 
        y: -4,
        transition: {
          type: "spring",
          stiffness: 400,
          damping: 25
        }
      }}
      whileTap={{ scale: 0.98 }}
      initial={{ opacity: 0, y: 20 }}
      animate={{ 
        opacity: 1, 
        y: 0,
        transition: {
          delay: index * 0.05
        }
      }}
    >
      <div className="exam-card-header">
        <SubjectIcon subject={exam.subject} />
        <div className="exam-info">
          <h3>
            {exam.subject}
          </h3>
          <span className="exam-date">
            {formatDate(exam.date)}
          </span>
        </div>
        <ProgressRing percentage={exam.percentage} />
      </div>
      <div className="exam-card-details">
        <div className="detail-grid">
          <div className="detail-item">
            <span className="detail-label">Questions</span>
            <motion.span 
              className="detail-value"
              initial={{ scale: 1 }}
              whileHover={{ scale: 1.1 }}
            >
              {exam.totalQuestions}
            </motion.span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Correct</span>
            <motion.span 
              className="detail-value"
              initial={{ scale: 1 }}
              whileHover={{ scale: 1.1 }}
            >
              {exam.score}
            </motion.span>
          </div>
          <div className="detail-item">
            <span className="detail-label">Lessons</span>
            <motion.span 
              className="detail-value"
              initial={{ scale: 1 }}
              whileHover={{ scale: 1.1 }}
            >
              {Array.isArray(exam.lessons) ? exam.lessons.length : exam.lessons}
            </motion.span>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

const HistoryCardSkeleton = () => (
  <motion.div 
    className="exam-card skeleton"
    variants={itemVariants}
  >
    <div className="exam-card-header">
      <div className="skeleton-circle"></div>
      <div className="exam-info" style={{ flex: 1 }}>
        <div className="skeleton-text" style={{ width: '60%' }}></div>
        <div className="skeleton-text" style={{ width: '40%' }}></div>
      </div>
      <div className="skeleton-circle"></div>
    </div>
    <div className="exam-card-details">
      <div className="detail-grid">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="detail-item">
            <div className="skeleton-text" style={{ width: '70%' }}></div>
            <div className="skeleton-text" style={{ width: '40%' }}></div>
          </div>
        ))}
      </div>
    </div>
  </motion.div>
);

const FilterTab = ({ subject, active, onClick }) => (
  <motion.button
    className={`filter-tab ${active ? 'active' : ''}`}
    onClick={onClick}
    whileHover={{ 
      y: -2,
      transition: {
        type: "spring",
        stiffness: 400,
        damping: 17
      }
    }}
    whileTap={{ scale: 0.95 }}
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
  }, []);

  const handleExamClick = (examId) => {
    navigate(`/exam/results/${examId}`);
  };

  const filteredExams = examHistory.filter(exam => {
    if (filter === 'All') return true;
    return exam.subject === filter;
  });

  const subjects = ['All', ...new Set(examHistory.map(exam => exam.subject))];

  return (
    <motion.div 
      className="history-container"
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
    >
      <motion.div 
        className="history-header"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      >
        <h1>Your Learning Journey</h1>
      </motion.div>

      {!loading && examHistory.length > 0 && (
        <>
          <StatsOverview examHistory={examHistory} />
          <motion.div 
            className="filter-tabs"
            variants={containerVariants}
            initial="initial"
            animate="animate"
          >
            {subjects.map((subject, index) => (
              <motion.div
                key={subject}
                variants={itemVariants}
                custom={index}
              >
                <FilterTab
                  subject={subject}
                  active={filter === subject}
                  onClick={() => setFilter(subject)}
                />
              </motion.div>
            ))}
          </motion.div>
        </>
      )}

      {error && <Notification message={error} type="error" />}

      <AnimatePresence mode="wait">
        {loading ? (
          <motion.div 
            className="exam-grid"
            variants={containerVariants}
            initial="initial"
            animate="animate"
            exit={{ opacity: 0 }}
          >
            {[...Array(6)].map((_, index) => (
              <HistoryCardSkeleton key={index} />
            ))}
          </motion.div>
        ) : examHistory.length > 0 ? (
          <motion.div 
            className="exam-grid"
            variants={containerVariants}
            initial="initial"
            animate="animate"
          >
            {filteredExams
              .slice()
              .reverse()
              .map((exam, index) => (
                <HistoryCard
                  key={exam["exam-id"]}
                  exam={exam}
                  onClick={handleExamClick}
                  index={index}
                />
              ))}
          </motion.div>
        ) : (
          <motion.div 
            className="empty-state"
            variants={itemVariants}
          >
            <motion.div 
              className="empty-state-icon"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{
                type: "spring",
                stiffness: 260,
                damping: 20
              }}
            >
              <i className="fas fa-graduation-cap"></i>
            </motion.div>
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              Start Your Learning Journey
            </motion.h2>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
            >
              Take your first exam to see your progress here!
            </motion.p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default History;
