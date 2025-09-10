import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import './UnsubmittedExamPopup.css';
import { api } from '../utils/api';
import { useNavigate } from 'react-router-dom';
import Notification from './Notification';
import { FaBook, FaClipboardList, FaTrash, FaPlay, FaExclamationTriangle, FaClock, FaQuestionCircle } from 'react-icons/fa';

const formatDate = (dateString) => {
  try {
    const date = new Date(dateString.replace(/\s/, 'T'));
    return date.toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch (e) {
    return dateString;
  }
};

const UnsubmittedExamPopup = ({ isOpen, onClose, unsubmittedExams = [], onExamDeleted }) => {
  const navigate = useNavigate();
  const [deletingExam, setDeletingExam] = useState(null);
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [notification, setNotification] = useState(null);

  const handleContinueExam = (examId) => {
    onClose();
    navigate(`/exam/g/${examId}`);
  };

  const handleDeleteClick = (examId) => {
    setDeletingExam(examId);
    setTimeout(() => {
      setShowDeleteConfirmation(true);
    }, 1000);
  };

  const handleDeleteCancel = () => {
    setDeletingExam(null);
    setShowDeleteConfirmation(false);
  };

  const handleDeleteConfirm = async () => {
    try {
      await api.deleteUnsubmittedExam(deletingExam);
      if (onExamDeleted) {
        onExamDeleted(deletingExam);
      }
      setNotification({
        message: 'Exam deleted successfully',
        type: 'success'
      });
    } catch (error) {
      console.error('Failed to delete exam:', error);
      setNotification({
        message: 'Failed to delete exam',
        type: 'error'
      });
    } finally {
      setDeletingExam(null);
      setShowDeleteConfirmation(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="unsubmitted-popup-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3, ease: "easeInOut" }}
          onClick={onClose}
        >
          <motion.div
            className="unsubmitted-popup-content"
            initial={{ scale: 0.9, y: 30, opacity: 0 }}
            animate={{
              scale: 1,
              y: 0,
              opacity: 1,
              transition: { duration: 0.4, ease: "easeOut" }
            }}
            exit={{
              scale: 0.95,
              opacity: 0,
              transition: { duration: 0.3, ease: "easeIn" }
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <button className="unsubmitted-popup-close-button" onClick={onClose}>&times;</button>

            <motion.h2
              className="unsubmitted-exam-header"
              initial={{ y: -20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.2, ease: "easeOut" }}
            >
              Resume your exams
            </motion.h2>

            {unsubmittedExams.length === 0 ? (
              <motion.div className="unsubmitted-exam-no-exams-message">
                Great! You have no unsubmitted exams in the past 7 days.
              </motion.div>
            ) : (
              <AnimatePresence>
                {unsubmittedExams.map((exam, index) => (
                  <motion.div
                    className="unsubmitted-exam-card"
                    key={exam['exam-id']}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -20 }}
                    transition={{
                      duration: 0.4,
                      delay: index * 0.1,
                      ease: "easeOut"
                    }}
                  >
                    <div className="unsubmitted-exam-header-container">
                      <div>
                        <h3 className="unsubmitted-exam-title">
                          {exam.test_name || `${exam.subject} - ${exam.lessons.join(', ')}`}
                        </h3>
                      </div>
                    </div>

                    <div className="unsubmitted-exam-details">
                      <div className="detail-row">
                        <FaBook style={{ marginRight: '0.5rem', color: 'var(--blue-400)' }} />
                        <strong>Subject:</strong> <span className="highlight">{exam.subject}</span>
                      </div>
                      <div className="detail-row">
                        <FaQuestionCircle style={{ marginRight: '0.5rem', color: 'var(--blue-400)' }} />
                        <strong>Questions:</strong> <span className="highlight">{exam.question_count}</span>
                      </div>
                      <div className="detail-row">
                        <FaClock style={{ marginRight: '0.5rem', color: 'var(--blue-400)' }} />
                        <strong>Created:</strong> <span className="highlight">{formatDate(exam.timestamp)}</span>
                      </div>
                      {exam.test ? (
                        <div className="detail-row">
                          <FaClipboardList style={{ marginRight: '0.5rem', color: 'var(--blue-400)' }} />
                          <strong>Type:</strong> <span className="highlight">Test Exam</span>
                        </div>
                      ) : (
                        <div className="detail-row">
                          <FaBook style={{ marginRight: '0.5rem', color: 'var(--blue-400)' }} />
                          <strong>Lessons:</strong> <span className="highlight">{exam.lessons.join(', ')}</span>
                        </div>
                      )}
                    </div>

                    {showDeleteConfirmation && deletingExam === exam['exam-id'] && (
                      <motion.div
                        className="unsubmitted-exam-delete-confirmation"
                        initial={{ height: 0, opacity: 0, scale: 0.8 }}
                        animate={{ height: 'auto', opacity: 1, scale: 1 }}
                        exit={{ height: 0, opacity: 0, scale: 0.8 }}
                        transition={{ duration: 0.3, ease: "easeInOut" }}
                      >
                        <p><FaExclamationTriangle style={{ marginRight: '0.5rem' }} /> This action is <strong>irreversible</strong>!</p>
                        <div className="unsubmitted-exam-confirm-cancel-buttons">
                          <motion.button className="unsubmitted-exam-cancel-delete-button" onClick={handleDeleteCancel}>
                            Cancel
                          </motion.button>
                          <motion.button className="unsubmitted-exam-confirm-delete-button" onClick={handleDeleteConfirm}>
                            Delete Now
                          </motion.button>
                        </div>
                      </motion.div>
                    )}

                    {!showDeleteConfirmation && (
                      <div className="unsubmitted-exam-action-buttons">
                        <motion.button
                          className="unsubmitted-exam-continue-button"
                          onClick={() => handleContinueExam(exam['exam-id'])}
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                        >
                          <FaPlay /> Resume
                        </motion.button>
                        <motion.button
                          className="unsubmitted-exam-delete-button"
                          onClick={() => handleDeleteClick(exam['exam-id'])}
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                          disabled={deletingExam !== null}
                        >
                          <FaTrash /> Discard
                        </motion.button>
                      </div>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>
            )}

            {notification && (
              <Notification
                message={notification.message}
                type={notification.type}
                onClose={() => setNotification(null)}
              />
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default UnsubmittedExamPopup;