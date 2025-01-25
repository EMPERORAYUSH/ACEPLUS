import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import styled from 'styled-components';
import { useNavigate } from 'react-router-dom';
import { ExamSkeletonLoading } from './Exam';
import { Skeleton } from "@mui/material";
import Select from 'react-select';
import { api } from '../utils/api';

const TestCard = styled(motion.div)`
  background: ${props => props.bgColor};
  border-radius: 15px;
  padding: 2rem;
  color: white;
  margin-bottom: 1.5rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease;
  cursor: pointer;
  &:hover {
    transform: translateY(-5px);
    box-shadow: 0 8px 12px rgba(0, 0, 0, 0.2);
  }
  position: relative;
  z-index: 1;
`;

const TestInfo = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const TestDetails = styled.div`
  margin-top: 1rem;
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
`;

const Badge = styled.span`
  background: rgba(255, 255, 255, 0.2);
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
`;

const SkeletonWrapper = styled(motion.div)`
  margin-top: 0;
  height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--background-color, #121212);
`;

const EmptyStateWrapper = styled(motion.div)`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 50vh;
  text-align: center;
  padding: 2rem;
`;

const EmptyStateIcon = styled(motion.div)`
  font-size: 5rem;
  margin-bottom: 1.5rem;
`;

const EmptyStateTitle = styled(motion.h2)`
  font-size: 1.8rem;
  margin-bottom: 1rem;
  color: #2d3748;
`;

const EmptyStateText = styled(motion.p)`
  font-size: 1.1rem;
  color: #718096;
  max-width: 500px;
  line-height: 1.6;
`;

const TeacherForm = styled(motion.div)`
  background: #1a1a1a;
  padding: 2rem;
  border-radius: 15px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  margin-bottom: 2rem;
  position: relative;
  z-index: 100;
  h2 {
    color: #ffffff;
    margin-bottom: 1.5rem;
  }
`;

const FormGroup = styled.div`
  margin-bottom: 1.5rem;
  
  label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 600;
    color: #e2e8f0;
  }
  
  select {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #2d3748;
    border-radius: 8px;
    background-color: #2d3748;
    color: #ffffff;
    font-size: 1rem;
    cursor: ${props => props.isDisabled ? 'not-allowed' : 'pointer'};

    &:disabled {
      background-color: #1a1a1a;
      border-color: #2d3748;
      color: #718096;
      cursor: not-allowed;
    }

    option {
      background-color: #2d3748;
      color: #ffffff;
    }
  }

  .react-select-container {
    .react-select__control {
      background-color: #2d3748;
      border-color: #4a5568;
      position: relative;
      z-index: 101;
      
      &:hover {
        border-color: #4a5568;
      }
    }

    .react-select__menu {
      background-color: #2d3748;
      border: 1px solid #4a5568;
      z-index: 102;
    }

    .react-select__option {
      background-color: #2d3748;
      color: #ffffff;

      &:hover {
        background-color: #4a5568;
      }
    }

    .react-select__multi-value {
      background-color: #4a5568;
      
      .react-select__multi-value__label {
        color: #ffffff;
      }
      
      .react-select__multi-value__remove {
        color: #ffffff;
        
        &:hover {
          background-color: #e53e3e;
          color: #ffffff;
        }
      }
    }

    .react-select__input-container {
      color: #ffffff;
    }

    .react-select__placeholder {
      color: #a0aec0;
    }
  }
`;

const DisabledInput = styled.input`
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #2d3748;
  border-radius: 8px;
  background-color: #1a1a1a;
  color: #718096;
  font-size: 1rem;
  cursor: not-allowed;
`;

const GenerateButton = styled.button`
  padding: 0.75rem 1.5rem;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: ${props => props.disabled ? 'not-allowed' : 'pointer'};
  width: 100%;
  font-size: 1rem;
  font-weight: 600;
  transition: background-color 0.2s ease;

  &:disabled {
    background-color: #2d3748;
    opacity: 0.7;
  }

  &:hover:not(:disabled) {
    background-color: #3d8b40;
  }
`;

const TestCardSkeleton = () => (
  <motion.div 
    className="test-card skeleton"
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    transition={{ duration: 0.3 }}
    style={{
      background: '#2a2a2a',
      borderRadius: '15px',
      padding: '2rem',
      marginBottom: '1.5rem',
      boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
      height: '200px'
    }}
  >
    {/* Header with subject and ID */}
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
      <Skeleton variant="text" width={120} height={32} style={{ background: 'rgba(255, 255, 255, 0.1)' }} />
      <Skeleton variant="text" width={60} height={24} style={{ background: 'rgba(255, 255, 255, 0.1)' }} />
    </div>

    {/* Badges */}
    <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem' }}>
      <Skeleton 
        variant="rounded" 
        width={120} 
        height={35} 
        style={{ background: 'rgba(255, 255, 255, 0.1)', borderRadius: '20px' }} 
      />
      <Skeleton 
        variant="rounded" 
        width={120} 
        height={35} 
        style={{ background: 'rgba(255, 255, 255, 0.1)', borderRadius: '20px' }} 
      />
    </div>

    {/* Lesson tags */}
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
      {[1, 2, 3].map((n) => (
        <Skeleton 
          key={n}
          variant="rounded" 
          width={80} 
          height={24} 
          style={{ background: 'rgba(255, 255, 255, 0.1)', borderRadius: '15px' }} 
        />
      ))}
    </div>
  </motion.div>
);

const PageHeader = styled(motion.div)`
  margin-bottom: 2rem;
  padding-top: 1.5rem;
  text-align: center;
  
  h1 {
    font-weight: 700;
    font-size: 2.2rem;
    letter-spacing: -0.5px;
    color: #ffffff;
    margin-bottom: 1.5rem;
    text-transform: uppercase;
    background: linear-gradient(135deg, #ffffff 0%, #b3b3b3 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }
`;

const TestSeries = () => {
  const [tests, setTests] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showSkeletonLoading, setShowSkeletonLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const navigate = useNavigate();
  const progressInterval = useRef(null);
  const startTimeRef = useRef(null);
  const lastProgressRef = useRef(0);
  const [isTeacher, setIsTeacher] = useState(false);
  const [teacherSubject, setTeacherSubject] = useState('');
  const [teacherStandard, setTeacherStandard] = useState([]);
  const [selectedStandard, setSelectedStandard] = useState('');
  const [selectedLessons, setSelectedLessons] = useState([]);
  const [availableLessons, setAvailableLessons] = useState([]);
  const [isLessonsLoading, setIsLessonsLoading] = useState(false);

  const getSubjectColor = (subject) => {
    const colors = { 
      Math: '#4CAF50', 
      Science: '#2196F3', 
      English: '#FFC107', 
      SS: '#9C27B0' 
    };
    return colors[subject] || '#607D8B';
  };

  const getSubjectIcon = (subject) => {
    const icons = { 
      Math: '📐', 
      Science: '🧪', 
      English: '📚', 
      SS: '🌍' 
    };
    return icons[subject] || '📚';
  };

  useEffect(() => {
    const fetchTests = async () => {
      try {
        const data = await api.getTests();
        setTests(data.tests);
        setIsTeacher(data.teacher);
        if (data.teacher) {
          setTeacherSubject(data.teacher_subject);
          if (data.teacher_standard) {
            setTeacherStandard(data.teacher_standard);
            setSelectedStandard(data.teacher_standard[0]);
          }
        }
      } catch (error) {
        console.error('Error fetching tests:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchTests();
  }, []);

  useEffect(() => {
    if (selectedStandard && teacherSubject) {
      fetchLessons();
    }
  }, [selectedStandard, teacherSubject]);

  const fetchLessons = async () => {
    setIsLessonsLoading(true);
    try {
      const data = await api.getLessons(teacherSubject, selectedStandard === 10);
      setAvailableLessons(data.map(lesson => ({ value: lesson, label: lesson })));
    } catch (error) {
      console.error('Error fetching lessons:', error);
    } finally {
      setIsLessonsLoading(false);
    }
  };

  const handleGenerateTest = async (e) => {
    e.preventDefault();
    setShowSkeletonLoading(true);
    
    try {
      const data = await api.generateTest({
        subject: teacherSubject,
        lessons: selectedLessons.map(l => l.value),
        class10: selectedStandard === 10
      });
      
      navigate('/create-test', { state: { generatedTest: data } });
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setShowSkeletonLoading(false);
    }
  };

  const cardVariants = {
    hidden: { 
      opacity: 0, 
      scale: 0.8, 
      y: 50,
      rotateX: -15
    },
    visible: (index) => ({ 
      opacity: 1, 
      scale: 1, 
      y: 0,
      rotateX: 0,
      transition: {
        duration: 0.8,
        delay: index * 0.15,
        type: "spring",
        stiffness: 100,
        damping: 15
      }
    }),
    hover: {
      scale: 1.03,
      rotateX: 5,
      boxShadow: "0 15px 30px rgba(0,0,0,0.2)",
      transition: {
        duration: 0.3,
        type: "spring",
        stiffness: 400,
        damping: 10
      }
    }
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

  const handleTestClick = async (testId) => {
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
        test: true,
        'test-id': testId
      });
      
      clearInterval(progressInterval.current);
      setProgress(100);
      
      setTimeout(() => {
        navigate(`/exam/g/${examData['exam-id']}`);
      }, 100);
    } catch (error) {
      console.error('Error creating exam:', error);
      clearInterval(progressInterval.current);
      setShowSkeletonLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, ease: "easeOut" }}
      className="test-series-container"
    >
      <AnimatePresence mode="wait">
        {showSkeletonLoading ? (
          <SkeletonWrapper
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <ExamSkeletonLoading progress={progress} />
          </SkeletonWrapper>
        ) : (
          <>
            <PageHeader
              initial={{ y: -20 }}
              animate={{ y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <h1>Test Series</h1>
            </PageHeader>

            {isTeacher && (
              <TeacherForm
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
              >
                <h2>Create New Test</h2>
                <form onSubmit={handleGenerateTest}>
                  <FormGroup>
                    <label>Subject</label>
                    <DisabledInput
                      type="text"
                      value={teacherSubject}
                      disabled
                    />
                  </FormGroup>

                  <FormGroup isDisabled={teacherStandard.length === 1}>
                    <label>Standard</label>
                    {teacherStandard.length === 1 ? (
                      <DisabledInput
                        type="text"
                        value={`Standard ${selectedStandard}`}
                        disabled
                      />
                    ) : (
                      <select
                        value={selectedStandard}
                        onChange={(e) => setSelectedStandard(Number(e.target.value))}
                        required
                      >
                        <option value="">Select Standard</option>
                        {teacherStandard.includes(9) && <option value={9}>Standard 9</option>}
                        {teacherStandard.includes(10) && <option value={10}>Standard 10</option>}
                      </select>
                    )}
                  </FormGroup>

                  <FormGroup>
                    <label>Lessons</label>
                    <Select
                      isMulti
                      options={availableLessons}
                      value={selectedLessons}
                      onChange={setSelectedLessons}
                      isLoading={isLessonsLoading}
                      isDisabled={!selectedStandard}
                      placeholder={selectedStandard ? "Select lessons" : "Select standard first"}
                      className="react-select-container"
                      classNamePrefix="react-select"
                      styles={{
                        control: (base) => ({
                          ...base,
                          background: '#2d3748',
                          borderColor: '#4a5568',
                          '&:hover': {
                            borderColor: '#4a5568'
                          }
                        }),
                        menu: (base) => ({
                          ...base,
                          background: '#2d3748',
                          border: '1px solid #4a5568'
                        }),
                        option: (base, state) => ({
                          ...base,
                          background: state.isFocused ? '#4a5568' : '#2d3748',
                          color: '#ffffff',
                          cursor: 'pointer'
                        }),
                        multiValue: (base) => ({
                          ...base,
                          background: '#4a5568'
                        }),
                        multiValueLabel: (base) => ({
                          ...base,
                          color: '#ffffff'
                        }),
                        multiValueRemove: (base) => ({
                          ...base,
                          color: '#ffffff',
                          ':hover': {
                            background: '#e53e3e',
                            color: '#ffffff'
                          }
                        }),
                        input: (base) => ({
                          ...base,
                          color: '#ffffff'
                        }),
                        placeholder: (base) => ({
                          ...base,
                          color: '#a0aec0'
                        })
                      }}
                    />
                  </FormGroup>

                  <GenerateButton
                    type="submit"
                    disabled={!selectedStandard || selectedLessons.length === 0}
                  >
                    Generate Test
                  </GenerateButton>
                </form>
              </TeacherForm>
            )}

            <motion.div 
              key="content"
              initial="hidden"
              animate="visible"
              exit="exit"
              variants={fadeTransition}
              className="tests-grid"
            >
              {isLoading ? (
                <div className="tests-grid">
                  {[1, 2, 3].map((n) => (
                    <TestCardSkeleton key={n} />
                  ))}
                </div>
              ) : tests.length === 0 ? (
                <EmptyStateWrapper
                  initial={{ opacity: 0, y: 50 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ 
                    duration: 0.8,
                    type: "spring",
                    stiffness: 100,
                    damping: 15
                  }}
                >
                  <EmptyStateIcon
                    initial={{ scale: 0, rotate: -180 }}
                    animate={{ scale: 1, rotate: 0 }}
                    transition={{ 
                      duration: 0.8,
                      delay: 0.2,
                      type: "spring",
                      stiffness: 200
                    }}
                  >
                    🎉
                  </EmptyStateIcon>
                  <EmptyStateTitle
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.3 }}
                  >
                    All Caught Up!
                  </EmptyStateTitle>
                  <EmptyStateText
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.4 }}
                  >
                    You've completed all available tests. Check back later for new challenges to tackle and keep improving!
                  </EmptyStateText>
                </EmptyStateWrapper>
              ) : (
                tests.map((test, index) => (
                  <TestCard
                    key={test['test-id']}
                    bgColor={getSubjectColor(test.subject)}
                    variants={cardVariants}
                    initial="hidden"
                    animate="visible"
                    whileHover="hover"
                    whileTap={{ scale: 0.98 }}
                    custom={index}
                    onClick={() => handleTestClick(test['test-id'])}
                  >
                    <TestInfo>
                      <h2>{getSubjectIcon(test.subject)} {test.subject}</h2>
                      <span className="test-id">#{test['test-id']}</span>
                    </TestInfo>
                    
                    <TestDetails>
                      <Badge>
                        <span>📝</span>
                        {test.questions} Questions
                      </Badge>
                      <Badge>
                        <span>📚</span>
                        {test.lessons.length} Lessons
                      </Badge>
                    </TestDetails>

                    <div className="lessons-list">
                      {test.lessons.map((lesson, idx) => (
                        <motion.span
                          key={idx}
                          className="lesson-tag"
                          initial={{ opacity: 0, scale: 0.8, x: -20 }}
                          animate={{ opacity: 1, scale: 1, x: 0 }}
                          transition={{ 
                            delay: index * 0.1 + idx * 0.05,
                            type: "spring",
                            stiffness: 200,
                            damping: 15
                          }}
                        >
                          {lesson}
                        </motion.span>
                      ))}
                    </div>
                  </TestCard>
                ))
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default TestSeries;