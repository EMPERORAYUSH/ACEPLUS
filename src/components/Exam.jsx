import React, { useState, useRef, useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import styled from "styled-components";
import { motion, AnimatePresence } from "framer-motion";
import { FaBook, FaSearch, FaTimes, FaSpinner, FaGraduationCap, FaFlask, FaGlobeAmericas, FaChevronDown } from "react-icons/fa";
import './exam.css';
import { api } from '../utils/api';

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
  const [subjects] = useState([
    { value: "Math", label: "Mathematics", icon: FaGraduationCap, color: "#4facfe" },
    { value: "Science", label: "Science", icon: FaFlask, color: "#00f2fe" },
    { value: "SS", label: "Social Studies", icon: FaGlobeAmericas, color: "#6c63ff" },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [isLessonsLoading, setIsLessonsLoading] = useState(false);
  const [notification, setNotification] = useState("");
  const [showLessonsPopup, setShowLessonsPopup] = useState(false);
  const [showErrorPopup, setShowErrorPopup] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedLessons, setSelectedLessons] = useState([]);
  const navigate = useNavigate();
  const searchInputRef = useRef(null);
  const lessonsDisplayRef = useRef(null);

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
      // Lock body scroll
      document.body.classList.add('select-menu-open');
    } else {
      // Unlock body scroll
      document.body.classList.remove('select-menu-open');
    }

    return () => {
      document.body.classList.remove('select-menu-open');
    };
  }, [showLessonsPopup, lessons]);

  // Keyboard support for lessons modal
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (!showLessonsPopup) return;

      if (e.key === 'Escape') {
        setShowLessonsPopup(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [showLessonsPopup]);

  const fetchLessons = async () => {
    try {
      // Set skeleton options
      setAvailableLessons(
        Array(5).fill().map((_, index) => `skeleton-${index}`),
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
        : [...prev, lesson],
    );
  };

  const handleSelectAll = () => {
    const nonSkeletonLessons = filteredLessons.filter(lesson => !lesson.startsWith('skeleton-'));
    setSelectedLessons(nonSkeletonLessons);
  };

  const handleClearAll = () => {
    setSelectedLessons([]);
  };

  const handleDone = () => {
    setLessons(selectedLessons.map(value => ({ value, label: value })));
    setShowLessonsPopup(false);
  };

  const removeLesson = (lessonToRemove) => {
    setLessons(prev => prev.filter(lesson => lesson.value !== lessonToRemove));
  };

  const filteredLessons = availableLessons.filter(lesson =>
    lesson.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  const nonSkeletonFilteredLessons = filteredLessons.filter(lesson => !lesson.startsWith('skeleton-'));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setNotification("");

    try {
      const examData = await api.createExam({
        userId: localStorage.getItem("user_id"),
        subject: subject,
        lessons: lessons.map((l) => l.value),
      });

      navigate(`/exam/g/${examData["exam-id"]}`);
    } catch (error) {
      setNotification("Failed to create an exam. Please try again.");
      setShowErrorPopup(true);
      setTimeout(() => {
        setNotification("");
        setShowErrorPopup(false);
      }, 5000);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLessonsDisplayKeyDown = (e) => {
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault();
      if (subject) {
        setShowLessonsPopup(true);
      }
    }
  };

  const getSubjectIcon = (subjectValue) => {
    const subjectData = subjects.find(s => s.value === subjectValue);
    return subjectData ? subjectData.icon : FaBook;
  };

  const getSubjectColor = (subjectValue) => {
    const subjectData = subjects.find(s => s.value === subjectValue);
    return subjectData ? subjectData.color : "#4facfe";
  };

  return (
    <ExamContainer className="exam-page">
      <motion.div className="exam-card">
        {notification && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="notification"
            role="status"
            aria-live="polite"
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
              role="dialog"
              aria-modal="true"
              aria-labelledby="error-title"
            >
              <h3 id="error-title">Exam Creation Failed</h3>
              <p>{notification || "Economics section will be fixed in 5 minutes. Please try again later."}</p>
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
          aria-busy={isLoading}
        >
          <div className="form-group">
            <label htmlFor="subject">
              Subject<span className="required-field">*</span>
            </label>
            <div className="subject-select-container">
              <select
                id="subject"
                value={subject}
                onChange={handleSubjectChange}
                required
                className="subject-select"
              >
                <option value="">Choose your subject</option>
                {subjects.map((sub) => (
                  <option key={sub.value} value={sub.value}>
                    {sub.label}
                  </option>
                ))}
              </select>
              <div className="subject-select-icon">
                {subject ? (
                  React.createElement(getSubjectIcon(subject), {
                    style: { color: getSubjectColor(subject) },
                  })
                ) : (
                  <FaChevronDown />
                )}
              </div>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="lessons">
              <span>Lessons</span>
              <span className="required-field">*</span>
            </label>
            <div
              ref={lessonsDisplayRef}
              className="lessons-display"
              onClick={() => subject && setShowLessonsPopup(true)}
              onKeyDown={handleLessonsDisplayKeyDown}
              tabIndex={subject ? 0 : -1}
              role="button"
              aria-expanded={showLessonsPopup}
              aria-controls="lessons-popup"
              aria-label={`Selected lessons: ${lessons.length > 0 ? lessons.map(l => l.value).join(', ') : 'none'}`}
            >
              {lessons.length > 0 ? (
                lessons.map(lesson => (
                  <span
                    key={lesson.value}
                    className="lesson-tag"
                  >
                    {lesson.value}
                    <button
                      type="button"
                      className="lesson-tag-remove"
                      onClick={(e) => {
                        e.stopPropagation();
                        removeLesson(lesson.value);
                      }}
                      aria-label={`Remove ${lesson.value}`}
                    >
                      <FaTimes />
                    </button>
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
          >
            {isLoading ? (
              <motion.span
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="submit-button-loading"
              >
                <FaSpinner className="submit-button-spinner" />
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
              id="lessons-popup"
              className="lessons-popup"
              initial={{ scale: 0.95 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0.95 }}
              onClick={e => e.stopPropagation()}
              role="dialog"
              aria-modal="true"
              aria-labelledby="lessons-popup-title"
            >
              <div className="lessons-popup-header">
                <h3 id="lessons-popup-title" className="lessons-popup-title">
                  <span className="lessons-popup-title-icon">
                    <FaBook />
                  </span>
                  Select Lessons
                </h3>
                <button
                  className="lessons-popup-close"
                  onClick={() => setShowLessonsPopup(false)}
                  aria-label="Close lessons selection"
                >
                  <FaTimes />
                </button>
              </div>

              <div className="lessons-popup-content">
                <div className="lessons-popup-search">
                  <FaSearch className="lessons-popup-search-icon" />
                  <input
                    ref={searchInputRef}
                    type="text"
                    placeholder="Search lessons..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>

                <div className="lessons-popup-actions">
                  <button
                    type="button"
                    className="lessons-popup-action-btn"
                    onClick={handleSelectAll}
                    disabled={nonSkeletonFilteredLessons.length === 0}
                  >
                    Select All ({nonSkeletonFilteredLessons.length})
                  </button>
                  <button
                    type="button"
                    className="lessons-popup-action-btn"
                    onClick={handleClearAll}
                    disabled={selectedLessons.length === 0}
                  >
                    Clear All
                  </button>
                </div>

                <div className="lessons-grid">
                  {filteredLessons.length === 0 ? (
                    <div className="lessons-empty-state">
                      <p>No lessons found matching your search.</p>
                    </div>
                  ) : (
                    filteredLessons.map((lesson) => (
                      <div
                        key={lesson}
                        className={`lesson-item ${
                          lesson.startsWith('skeleton-') ? 'skeleton'
                            : selectedLessons.includes(lesson) ? 'selected' : ''
                        }`}
                        onClick={() => !lesson.startsWith('skeleton-') && toggleLesson(lesson)}
                        onKeyDown={(e) => {
                          if ((e.key === ' ' || e.key === 'Enter') && !lesson.startsWith('skeleton-')) {
                            e.preventDefault();
                            toggleLesson(lesson);
                          }
                        }}
                        tabIndex={lesson.startsWith('skeleton-') ? -1 : 0}
                        role={lesson.startsWith('skeleton-') ? undefined : "checkbox"}
                        aria-checked={lesson.startsWith('skeleton-') ? undefined : selectedLessons.includes(lesson)}
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
                    ))
                  )}
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
  );
};

export default Exam;
