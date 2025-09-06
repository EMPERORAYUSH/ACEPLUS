import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import styled from 'styled-components';
import { api } from '../utils/api';
import Notification from './Notification';

const PopupOverlay = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(5px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  pointer-events: all;
`;

const PopupContent = styled(motion.div)`
  background: rgba(26, 26, 26, 0.95);
  padding: 2rem;
  border-radius: 12px;
  max-width: 700px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  position: relative;
  border: 1px solid #333;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);

  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-track {
    background: #222;
    border-radius: 4px;
  }

  &::-webkit-scrollbar-thumb {
    background: #444;
    border-radius: 4px;

    &:hover {
      background: #555;
    }
  }

  @media (max-width: 768px) {
    padding: 1.5rem;
    width: 95%;
  }
`;

const Header = styled(motion.h2)`
  text-align: center;
  margin-bottom: 1.5rem;
  color: #fff;
  font-size: 1.8rem;
  text-transform: uppercase;
  letter-spacing: 2px;
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);

  @media (max-width: 768px) {
    font-size: 1.5rem;
    margin-bottom: 1.2rem;
  }
`;

const CloseButton = styled.button`
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #999;
  transition: color 0.3s;
  z-index: 1001;

  &:hover {
    color: #fff;
  }

  @media (max-width: 768px) {
    font-size: 1.2rem;
  }
`;

const ExamCard = styled(motion.div)`
  background: rgba(45, 45, 45, 0.8);
  border: 2px solid #333;
  border-radius: 10px;
  padding: 1.5rem;
  margin-bottom: 1rem;
  transition: all 0.3s ease;

  &:hover {
    border-color: #555;
    background: rgba(55, 55, 55, 0.8);
  }

  @media (max-width: 768px) {
    padding: 1rem;
  }
`;

const ExamHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.8rem;

  @media (max-width: 768px) {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
`;

const ExamTitle = styled.h3`
  color: #fff;
  margin: 0;
  font-size: 1.2rem;
  font-weight: 600;

  @media (max-width: 768px) {
    font-size: 1.1rem;
  }
`;

const ExamMeta = styled.div`
  color: #ccc;
  font-size: 0.9rem;

  @media (max-width: 768px) {
    font-size: 0.8rem;
  }
`;

const ExamDetails = styled.div`
  color: #aaa;
  font-size: 0.85rem;

  .highlight {
    color: #4dabf7;
    font-weight: 500;
  }

  @media (max-width: 768px) {
    font-size: 0.8rem;
  }
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 0.8rem;
  margin-top: 1rem;

  @media (max-width: 768px) {
    flex-direction: column;
  }
`;

const ContinueButton = styled(motion.button)`
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  padding: 0.8rem 1.5rem;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }

  @media (max-width: 768px) {
    padding: 0.7rem 1.2rem;
    font-size: 0.8rem;
  }
`;

const DeleteButton = styled(motion.button)`
  background: linear-gradient(135deg, #ff6b6b, #ee5a52);
  color: white;
  border: none;
  padding: 0.8rem 1.5rem;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(255, 107, 107, 0.3);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }

  @media (max-width: 768px) {
    padding: 0.7rem 1.2rem;
    font-size: 0.8rem;
  }
`;

const DeleteConfirmation = styled(motion.div)`
  background: rgba(255, 107, 107, 0.1);
  border: 2px solid #ff6b6b;
  border-radius: 8px;
  padding: 1.2rem;
  margin-top: 1rem;

  p {
    color: #ff6b6b;
    margin: 0 0 1rem 0;
    font-weight: 600;
  }

  @media (max-width: 768px) {
    padding: 1rem;
  }
`;

const CountdownText = styled.div`
  font-family: monospace;
  font-size: 1.2rem;
  color: #ff6b6b;
  text-align: center;
  font-weight: bold;
  margin-bottom: 1rem;

  @media (max-width: 768px) {
    font-size: 1rem;
  }
`;

const ConfirmCancelButtons = styled.div`
  display: flex;
  gap: 0.8rem;

  @media (max-width: 768px) {
    flex-direction: column;
  }
`;

const CancelDeleteButton = styled(motion.button)`
  background: #666;
  color: white;
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s;
  flex: 1;

  &:hover {
    background: #888;
  }

  @media (max-width: 768px) {
    padding: 0.7rem 0.8rem;
    font-size: 0.9rem;
  }
`;

const ConfirmDeleteButton = styled(motion.button)`
  background: #ff6b6b;
  color: white;
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s;
  flex: 1;

  &:hover {
    background: #ff4747;
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  @media (max-width: 768px) {
    padding: 0.7rem 0.8rem;
    font-size: 0.9rem;
  }
`;

const NoExamsMessage = styled(motion.div)`
  text-align: center;
  color: #999;
  padding: 2rem;
  font-style: italic;
  font-size: 1.1rem;

  @media (max-width: 768px) {
    font-size: 1rem;
    padding: 1.5rem;
  }
`;

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

const UnsubmittedExamPopup = ({ isOpen, onClose }) => {
  const [unsubmittedExams, setUnsubmittedExams] = useState([]);
  const [loading, setLoading] = useState(false);
  const [deletingExam, setDeletingExam] = useState(null);
  const [showDeleteConfirmation, setShowDeleteConfirmation] = useState(false);
  const [countdown, setCountdown] = useState(5);
  const [notification, setNotification] = useState(null);

  useEffect(() => {
    if (isOpen) {
      fetchUnsubmittedExams();
    }
  }, [isOpen]);

  const fetchUnsubmittedExams = async () => {
    try {
      setLoading(true);
      const response = await api.getUnsubmittedExams();
      setUnsubmittedExams(response.unsubmitted_exams || []);
    } catch (error) {
      console.error('Failed to fetch unsubmitted exams:', error);
      setNotification({
        message: 'Failed to load unsubmitted exams',
        type: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleContinueExam = (examId) => {
    // Navigate to exam taking page
    onClose();
    window.location.href = `/exam?taking=1&exam_id=${examId}`;
  };

  const handleDeleteClick = (examId) => {
    setDeletingExam(examId);
    setShowDeleteConfirmation(true);
    setCountdown(5);
  };

  const handleDeleteCancel = () => {
    setDeletingExam(null);
    setShowDeleteConfirmation(false);
    setCountdown(5);
  };

  useEffect(() => {
    let timer;
    if (showDeleteConfirmation && countdown > 0) {
      timer = setTimeout(() => {
        setCountdown(countdown - 1);
      }, 1000);
    } else if (showDeleteConfirmation && countdown === 0) {
      // Auto delete after countdown
      handleDeleteConfirm();
    }
    return () => clearTimeout(timer);
  }, [showDeleteConfirmation, countdown]);

  const handleDeleteConfirm = async () => {
    try {
      await api.deleteUnsubmittedExam(deletingExam);
      setUnsubmittedExams(prev =>
        prev.filter(exam => exam['exam-id'] !== deletingExam)
      );
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
      setCountdown(5);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <PopupOverlay
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          onClick={onClose}
        >
          <PopupContent
            initial={{ scale: 0.95, y: 20, opacity: 0 }}
            animate={{
              scale: 1,
              y: 0,
              opacity: 1,
              transition: { duration: 0.5 }
            }}
            exit={{
              opacity: 0,
              transition: { duration: 0.2 }
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <CloseButton onClick={onClose}>&times;</CloseButton>

            <Header
              initial={{ y: -20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              Unsubmitted Exams
            </Header>

            {loading ? (
              <NoExamsMessage>Loading...</NoExamsMessage>
            ) : unsubmittedExams.length === 0 ? (
              <NoExamsMessage>
                Great! You have no unsubmitted exams in the past 7 days.
              </NoExamsMessage>
            ) : (
              <AnimatePresence>
                {unsubmittedExams.map((exam, index) => (
                  <ExamCard
                    key={exam['exam-id']}
                    initial={{ opacity: 0, x: -50 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: 50 }}
                    transition={{
                      duration: 0.3,
                      delay: index * 0.1
                    }}
                  >
                    <ExamHeader>
                      <div>
                        <ExamTitle>
                          {exam.test_name || `${exam.subject} - ${exam.lessons.join(', ')}`}
                        </ExamTitle>
                        <ExamMeta>
                          {exam.question_count} questions • Created: {formatDate(exam.timestamp)}
                        </ExamMeta>
                      </div>
                    </ExamHeader>

                    <ExamDetails>
                      <strong>Subject:</strong> <span className="highlight">{exam.subject}</span>
                      {exam.test ? (
                        <p>This is a <span className="highlight">test</span> exam</p>
                      ) : (
                        <p>Lessons: <span className="highlight">{exam.lessons.join(', ')}</span></p>
                      )}
                    </ExamDetails>

                    {showDeleteConfirmation && deletingExam === exam['exam-id'] && (
                      <DeleteConfirmation
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                      >
                        <p>⚠️ This action is <strong>irreversible</strong>!</p>
                        <CountdownText>{countdown}</CountdownText>
                        <ConfirmCancelButtons>
                          <CancelDeleteButton onClick={handleDeleteCancel}>
                            Cancel
                          </CancelDeleteButton>
                          <ConfirmDeleteButton onClick={handleDeleteConfirm}>
                            Confirm Delete ({countdown}s)
                          </ConfirmDeleteButton>
                        </ConfirmCancelButtons>
                      </DeleteConfirmation>
                    )}

                    {!showDeleteConfirmation && (
                      <ActionButtons>
                        <ContinueButton
                          onClick={() => handleContinueExam(exam['exam-id'])}
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                        >
                          Continue Exam
                        </ContinueButton>
                        <DeleteButton
                          onClick={() => handleDeleteClick(exam['exam-id'])}
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                          disabled={deletingExam !== null}
                        >
                          Delete Exam
                        </DeleteButton>
                      </ActionButtons>
                    )}
                  </ExamCard>
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
          </PopupContent>
        </PopupOverlay>
      )}
    </AnimatePresence>
  );
};

export default UnsubmittedExamPopup;