import React, { useState, useRef, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import styled from "styled-components";
import { motion, AnimatePresence } from "framer-motion";
import { FaBook, FaSearch, FaTimes } from "react-icons/fa";
import './exam.css';
import { api } from '../utils/api';

export const ProgressBar = styled.div`
  position: fixed;
  top: 50px;
  left: 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(to right, #4facfe 0%, #00f2fe 100%);
  transform-origin: 0 50%;
  transform: scaleX(${(props) => props.progress / 100});
  transition:
    transform 0.1s ease,
    top 0.3s ease;
  z-index: 1000;
  .header-hidden & {
    top: 0;
  }
`;

const SkeletonOption = styled.div`
  height: 20px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: loading 1.5s infinite;
  border-radius: 2px;
  margin: 5px 0;

  @keyframes loading {
    0% {
      background-position: 200% 0;
    }
    100% {
      background-position: -200% 0;
    }
  }
`;

export const ExamSkeletonLoading = ({ progress }) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <ProgressBar progress={progress} />
      <div className="exam-skeleton-container">
        {[1, 2, 3, 4].map((item) => (
          <motion.div
            key={item}
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: item * 0.1 }}
            className="exam-skeleton-card"
          >
            <div className="exam-skeleton-question"></div>
            <div className="exam-skeleton-options">
              <div className="exam-skeleton-option"></div>
              <div className="exam-skeleton-option"></div>
              <div className="exam-skeleton-option"></div>
              <div className="exam-skeleton-option"></div>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
};

const ExamContainer = styled.div`
  -webkit-tap-highlight-color: transparent;
  * {
    -webkit-tap-highlight-color: transparent;
  }
`;

const ErrorPopup = styled(motion.div)`
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1100;
  max-width: 400px;
  width: 90%;
  text-align: center;

  h3 {
    margin: 0 0 15px;
    color: #e74c3c;
  }

  p {
    margin: 0 0 20px;
    color: #666;
  }

  button {
    background: #3498db;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.2s;

    &:hover {
      background: #2980b9;
    }
  }
`;

const Exam = () => {
  const location = useLocation();
  const [subject, setSubject] = useState(location.state?.subject || "");
  const [lessons, setLessons] = useState([]);
  const [availableLessons, setAvailableLessons] = useState([]);
  const [subjects] = useState(["Math", "Science", "SS"]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLessonsLoading, setIsLessonsLoading] = useState(false);
  const [notification, setNotification] = useState("");
  const [showSkeletonLoading, setShowSkeletonLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [showLessonsPopup, setShowLessonsPopup] = useState(false);
  const [showErrorPopup, setShowErrorPopup] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedLessons, setSelectedLessons] = useState([]);
  const navigate = useNavigate();
  const progressInterval = useRef(null);
  const startTimeRef = useRef(null);
  const lastProgressRef = useRef(0);

  useEffect(() => {
    if (location.state?.subject) {
      setSubject(location.state.subject);
    }
  }, [location.state]);

  useEffect(() => {
    if (subject && !availableLessons.length) {
      setIsLessonsLoading(true);
      fetchLessons();
    }
  }, [subject]);

  useEffect(() => {
    // Initialize selected lessons when popup opens
    if (showLessonsPopup) {
      setSelectedLessons(lessons.map(l => l.value));
    }
  }, [showLessonsPopup]);

  const fetchLessons = async () => {
    try {
      // Set skeleton options
      setAvailableLessons(
        Array(5).fill().map((_, index) => `skeleton-${index}`)
      );
      
      const data = await api.getLessons(subject);
      
      // Delay to show skeleton for a moment
      setTimeout(() => {
        setAvailableLessons(data);
        setIsLessonsLoading(false);
      }, 1000);
    } catch (error) {
      console.error("Error fetching lessons:", error);
      setNotification("Failed to fetch lessons. Please try again.");
      setIsLessonsLoading(false);
    }
  };

  const handleSubjectChange = (e) => {
    const selectedSubject = e.target.value;
    setSubject(selectedSubject);
    setAvailableLessons([]);
    setLessons([]);
    setSelectedLessons([]);
  };

  const toggleLesson = (lesson) => {
    setSelectedLessons(prev => 
      prev.includes(lesson) 
        ? prev.filter(l => l !== lesson)
        : [...prev, lesson]
    );
  };

  const handleDone = () => {
    setLessons(selectedLessons.map(value => ({ value, label: value })));
    setShowLessonsPopup(false);
  };

  const filteredLessons = availableLessons.filter(lesson => 
    lesson.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setNotification("");
    setShowSkeletonLoading(true);
    setProgress(0);
    startTimeRef.current = Date.now();
    lastProgressRef.current = 0;

    const updateProgress = () => {
      const elapsedTime = Date.now() - startTimeRef.current;
      const newProgress = Math.min((elapsedTime / 1000) * 100, 100);

      if (newProgress > lastProgressRef.current) {
        setProgress(newProgress);
        lastProgressRef.current = newProgress;
      }
    };

    progressInterval.current = setInterval(updateProgress, 5);

    try {
      const examData = await api.createExam({
        userId: localStorage.getItem("user_id"),
        subject: subject,
        lessons: lessons.map((l) => l.value),
      });

      clearInterval(progressInterval.current);
      setProgress(100);
      navigate(`/exam/g/${examData["exam-id"]}`);
    } catch (error) {
      setNotification("Failed to create an exam. Please try again.");
      setShowErrorPopup(true);
      setTimeout(() => {
        setNotification("");
        setShowErrorPopup(false);
      }, 5000);
    } finally {
      clearInterval(progressInterval.current);
      setIsLoading(false);
      setShowSkeletonLoading(false);
    }
  };

  return (
    <AnimatePresence mode="wait">
      {showSkeletonLoading ? (
        <ExamSkeletonLoading progress={progress} />
      ) : (
        <ExamContainer className="exam-page">
          <motion.div className="exam-card">
            {notification && (
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="notification"
              >
                {notification}
              </motion.div>
            )}
            
            {/* Error Popup */}
            <AnimatePresence>
              {showErrorPopup && (
                <ErrorPopup
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                >
                  <h3>Exam Creation Failed</h3>
                  <p>Economics section will be fixed in 5 minutes. Please try again later.</p>
                  <button onClick={() => setShowErrorPopup(false)}>Close</button>
                </ErrorPopup>
              )}
            </AnimatePresence>

            <motion.h2
              className="exam-title"
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              Create New Exam
            </motion.h2>
            <motion.form
              onSubmit={handleSubmit}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.3 }}
            >
              <div className="form-group">
                <label htmlFor="subject">
                  Subject
                  <span className="required-field">*</span>
                </label>
                <select
                  id="subject"
                  value={subject}
                  onChange={handleSubjectChange}
                  required
                >
                  <option value="">Select a subject</option>
                  {subjects.map((sub) => (
                    <option key={sub} value={sub}>
                      {sub}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="lessons">
                  <span>Lessons</span>
                  <span className="required-field">*</span>
                  <span className="tip-badge">
                    You can select multiple lessons
                  </span>
                </label>
                <div 
                  className="lessons-display"
                  onClick={() => subject && setShowLessonsPopup(true)}
                >
                  {lessons.length > 0 ? (
                    lessons.map(lesson => (
                      <span
                        key={lesson.value}
                        className="lesson-tag"
                      >
                        {lesson.value}
                      </span>
                    ))
                  ) : (
                    <span className="lessons-placeholder">
                      {subject ? "Click to select lessons" : "Select a subject first"}
                    </span>
                  )}
                </div>
              </div>

              <motion.button
                type="submit"
                className="submit-button"
                disabled={isLoading || !subject || lessons.length === 0}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                {isLoading ? (
                  <motion.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                  >
                    Creating Exam...
                  </motion.span>
                ) : (
                  "Create Exam"
                )}
              </motion.button>
            </motion.form>
          </motion.div>

          {/* Lessons Selection Popup */}
          <AnimatePresence>
            {showLessonsPopup && (
              <motion.div 
                className="lessons-popup-overlay"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setShowLessonsPopup(false)}
              >
                <motion.div 
                  className="lessons-popup"
                  initial={{ scale: 0.95 }}
                  animate={{ scale: 1 }}
                  exit={{ scale: 0.95 }}
                  onClick={e => e.stopPropagation()}
                >
                  <div className="lessons-popup-header">
                    <h3 className="lessons-popup-title">
                      <span className="lessons-popup-title-icon">
                        <FaBook />
                      </span>
                      Select Lessons
                    </h3>
                    <button 
                      className="lessons-popup-close"
                      onClick={() => setShowLessonsPopup(false)}
                    >
                      <FaTimes />
                    </button>
                  </div>

                  <div className="lessons-popup-content">
                    <div className="lessons-popup-search">
                      <FaSearch className="lessons-popup-search-icon" />
                      <input
                        type="text"
                        placeholder="Search lessons..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                      />
                    </div>

                    <div className="lessons-grid">
                      {filteredLessons.map((lesson) => (
                        <div
                          key={lesson}
                          className={`lesson-item ${
                            lesson.startsWith('skeleton-') 
                              ? 'skeleton'
                              : selectedLessons.includes(lesson) ? 'selected' : ''
                          }`}
                          onClick={() => !lesson.startsWith('skeleton-') && toggleLesson(lesson)}
                        >
                          {lesson.startsWith('skeleton-') ? (
                            <div className="lesson-skeleton-content">
                              <div className="lesson-skeleton-text"></div>
                              <div className="lesson-skeleton-checkbox"></div>
                            </div>
                          ) : (
                            <>
                              <span className="lesson-item-text">{lesson}</span>
                              <div className="lesson-item-checkbox" />
                            </>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="lessons-popup-footer">
                    <span className="selected-count">
                      {selectedLessons.length} lesson{selectedLessons.length !== 1 ? 's' : ''} selected
                    </span>
                    <button 
                      className="lessons-popup-btn lessons-popup-btn-secondary"
                      onClick={() => setShowLessonsPopup(false)}
                    >
                      Cancel
                    </button>
                    <button 
                      className="lessons-popup-btn lessons-popup-btn-primary"
                      onClick={handleDone}
                    >
                      Done
                    </button>
                  </div>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>
        </ExamContainer>
      )}
    </AnimatePresence>
  );
};

export default Exam;
