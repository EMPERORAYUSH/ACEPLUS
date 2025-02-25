import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { FaExclamationCircle, FaChartLine } from 'react-icons/fa';
import { AiOutlineLoading3Quarters, AiOutlineBulb } from 'react-icons/ai';
import { BsCheckCircleFill } from 'react-icons/bs';
import { motion, AnimatePresence } from 'framer-motion';
import styled from 'styled-components';
import CopyableExamId from './CopyableExamId';
import { api } from '../utils/api';
import 'katex/dist/katex.min.css';
import { InlineMath, BlockMath } from 'react-katex';
import { IoClose } from 'react-icons/io5';
import MobilePopup from './MobilePopup';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

const ExamWrapper = styled.div`
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding-top: 60px; /* Account for header */
  transition: margin-left 0.3s ease-in-out;
  margin-left: 70px;

  .sidebar:hover ~ & {
    margin-left: 220px;
  }

  @media (max-width: 768px) {
    margin-left: 0;
  }
`;

const ReportButton = styled(motion.button)`
  position: absolute;
  top: 1.5rem;
  right: 1.5rem;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2;
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  -webkit-touch-callout: none;
  height: 32px;
  
  &:disabled {
    cursor: default;
  }
`;

const CloseButton = styled(motion.button)`
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffd700;
  z-index: 1001;
  
  &:hover {
    color: #fff;
  }
  
  svg {
    width: 24px;
    height: 24px;
  }
`;

const HintContainer = styled(motion.div)`
  margin-top: 1rem;
  padding: 1.5rem;
  border-radius: 12px;
  background: rgba(255, 215, 0, 0.1);
  border: 1px solid rgba(255, 215, 0, 0.2);
  color: #ffd700;
  font-size: 0.95rem;
  line-height: 1.5;
  
  .katex {
    color: #ffd700;
  }

  @media (max-width: 768px) {
    display: none;
  }
`;

const HintContent = styled.div`
  color: #ffd700;
  
  .hint-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1rem;
    color: #ffd700;
    font-weight: 600;
  }

  .hint-content {
    color: #ffd700;
    font-size: 1rem;
    line-height: 1.6;
    margin-top: 0.5rem;

    h1, h2, h3, h4, h5, h6 {
      color: #fff;
      margin: 1.5rem 0 1rem;
      font-weight: 600;
      line-height: 1.3;

      &:first-child {
        margin-top: 0;
      }
    }

    h1 { font-size: 1.5rem; }
    h2 { font-size: 1.3rem; }
    h3 { 
      font-size: 1.2rem;
      color: #ffd700;
    }
    h4 { font-size: 1.1rem; }
    h5, h6 { font-size: 1rem; }

    p {
      margin: 0.8rem 0;
      
      &:first-child {
        margin-top: 0;
      }
    }

    ul, ol {
      margin: 0.8rem 0;
      padding-left: 1.5rem;
    }

    li {
      margin: 0.3rem 0;
      
      p {
        margin: 0.4rem 0;
      }
    }

    code {
      background: rgba(255, 255, 255, 0.1);
      padding: 0.2rem 0.4rem;
      border-radius: 4px;
      font-family: 'Fira Code', monospace;
      font-size: 0.9em;
    }

    pre {
      background: rgba(18, 18, 18, 0.8);
      padding: 1rem;
      border-radius: 8px;
      overflow-x: auto;
      margin: 1rem 0;
      border: 1px solid rgba(255, 215, 0, 0.2);

      code {
        background: none;
        padding: 0;
        color: #fff;
      }
    }

    blockquote {
      border-left: 4px solid #ffd700;
      margin: 1rem 0;
      padding: 0.5rem 0 0.5rem 1rem;
      font-style: italic;
      background: rgba(255, 215, 0, 0.05);
      border-radius: 0 4px 4px 0;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      margin: 1rem 0;
      font-size: 0.9em;
    }

    th, td {
      border: 1px solid rgba(255, 215, 0, 0.2);
      padding: 0.5rem;
      text-align: left;
    }

    th {
      background: rgba(255, 215, 0, 0.1);
      font-weight: 600;
    }

    tr:nth-child(even) {
      background: rgba(255, 255, 255, 0.03);
    }

    hr {
      border: none;
      border-top: 1px solid rgba(255, 215, 0, 0.2);
      margin: 1.5rem 0;
    }

    a {
      color: #ffd700;
      text-decoration: none;
      border-bottom: 1px dashed #ffd700;
      transition: all 0.2s ease;

      &:hover {
        border-bottom-style: solid;
        color: #fff;
      }
    }

    img {
      max-width: 100%;
      height: auto;
      border-radius: 8px;
      margin: 1rem 0;
    }

    .katex {
      font-size: 1.1em;
      color: #ffd700;
    }

    .katex-display {
      margin: 1rem 0;
      padding: 0.5rem;
      background: rgba(255, 215, 0, 0.05);
      border-radius: 8px;
      overflow-x: auto;
    }
  }
`;

const MobileHintPopup = styled(motion.div)`
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(18, 18, 18, 0.95);
  backdrop-filter: blur(10px);
  border-top-left-radius: 20px;
  border-top-right-radius: 20px;
  padding: 1.5rem;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.3);
  z-index: 1000;
  border-top: 1px solid rgba(255, 215, 0, 0.2);
  max-height: 70vh;
  overflow-y: auto;
  
  .hint-content {
    color: #ffd700;
    font-size: 1rem;
    line-height: 1.6;
    margin-top: 0.5rem;
  }

  .hint-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1rem;
    color: #ffd700;
    font-weight: 600;
  }

  .drag-handle {
    width: 40px;
    height: 4px;
    background: rgba(255, 255, 255, 0.2);
    border-radius: 2px;
    margin: -0.5rem auto 1rem;
  }

  @media (min-width: 769px) {
    display: none;
  }
`;

const ExamContainer = styled.div`
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
  width: 100%;
  transition: all 0.3s ease-in-out;

  @media (max-width: 768px) {
    padding: 1rem;
    margin-bottom: 60px;
  }

  -webkit-tap-highlight-color: transparent;
  * {
    -webkit-tap-highlight-color: transparent;
  }
`;

const OptionContainer = styled(motion.div)`
  -webkit-tap-highlight-color: transparent;
  user-select: none;
`;

const IconContainer = ({ status, index }) => {
  return (
    <motion.div
      initial={{ scale: 0.8 }}
      animate={{ scale: 1 }}
      exit={{ scale: 0.8 }}
      transition={{ duration: 0.2 }}
    >
      {status === index ? (
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
        >
          <AiOutlineLoading3Quarters
            style={{ fontSize: '1.2rem', color: '#666' }}
          />
        </motion.div>
      ) : status === `${index}-done` ? (
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 300, damping: 25 }}
        >
          <BsCheckCircleFill
            style={{ fontSize: '1.2rem', color: '#22c55e' }}
          />
        </motion.div>
      ) : (
        <motion.div
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
        >
          <FaExclamationCircle
            style={{ fontSize: '1.2rem', color: '#dc2626' }}
          />
        </motion.div>
      )}
    </motion.div>
  );
};

const ExamIdSection = styled.div`
  background: #1a1a1a;
  border-radius: 12px;
  padding: 1.5rem;
  margin: 1.5rem 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
`;

const ExamIdTitle = styled.h3`
  margin: 0;
  color: #667eea;
  font-size: 1.2rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;

  svg {
    font-size: 1.4rem;
  }
`;

const ExamIdContent = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
  justify-content: center;
`;

const ExamIdLabel = styled.div`
  color: #b0b0b0;
  font-size: 0.9rem;
`;

const ExamHeader = styled.div`
  background: #1a1a1a;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
  text-align: center;
`;

const ExamTitle = styled.h1`
  margin: 0 0 1rem 0;
  color: #ffffff;
  font-size: 2rem;
  font-weight: 600;
`;

const LessonsContainer = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  justify-content: center;
  margin-top: 1rem;
`;

const LessonTag = styled.span`
  background-color: rgba(102, 126, 234, 0.1);
  color: #667eea;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
  border: 1px solid rgba(102, 126, 234, 0.2);
  transition: all 0.2s ease;

  &:hover {
    background-color: rgba(102, 126, 234, 0.15);
    border-color: rgba(102, 126, 234, 0.3);
    transform: translateY(-1px);
  }
`;

const QuestionCard = styled(motion.div)`
  background: #1a1a1a;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  position: relative;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
`;

const QuestionHeader = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding-right: 3rem;
`;

const QuestionNumber = styled.div`
  position: absolute;
  top: -12px;
  left: -12px;
  background: #2196f3;
  color: white;
  width: 35px;
  height: 35px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
  z-index: 1;
`;

const QuestionText = styled.h3`
  color: #ffffff;
  font-size: 1.2rem;
  font-weight: 500;
  margin: 0;
  line-height: 1.5;
  padding-top: 4px;
  flex: 1;

  .katex {
    font-size: 1.1em;
    line-height: 1.2;
  }
`;

// Table styled components
const TableContainer = styled.div`
  margin: 1rem 0;
  overflow-x: auto;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  padding: 1rem;
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  color: #ffffff;
  font-size: 1rem;
`;

const TableHeader = styled.th`
  background: rgba(79, 172, 254, 0.1);
  padding: 0.75rem 1rem;
  text-align: left;
  border: 1px solid rgba(255, 255, 255, 0.1);
  font-weight: 600;
`;

const TableCell = styled.td`
  padding: 0.75rem 1rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
`;

const TableRow = styled.tr`
  &:nth-child(even) {
    background: rgba(255, 255, 255, 0.02);
  }
  &:hover {
    background: rgba(79, 172, 254, 0.05);
  }
`;

const OptionsContainer = styled(motion.div)`
  display: grid;
  gap: 1rem;
  margin-top: 1rem;
`;

const RippleContainer = styled(motion.div)`
  position: relative;
  overflow: hidden;
  border-radius: 8px;
`;

const Ripple = styled(motion.span)`
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  transform: translate(-50%, -50%);
  pointer-events: none;
`;

const Option = styled(motion.div)`
  background: rgba(255, 255, 255, 0.05);
  padding: 1rem 1.2rem;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s ease, border-color 0.2s ease;
  transform: scale(1);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #ffffff;
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  -webkit-touch-callout: none;
  position: relative;
  overflow: hidden;

  &:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.2);
    transform: translateY(-1px);
  }

  &.selected {
    background: rgba(102, 126, 234, 0.1);
    border-color: rgba(102, 126, 234, 0.3);
    color: #667eea;
  }

  .ripple {
    position: absolute;
    border-radius: 50%;
    transform: scale(0);
    animation: ripple 0.6s linear;
    background-color: rgba(255, 255, 255, 0.2);
  }

  @keyframes ripple {
    to {
      transform: scale(4);
      opacity: 0;
    }
  }
`;

// Add new styled component for loading dots
const LoadingDots = styled(motion.div)`
  display: flex;
  gap: 8px;
  justify-content: center;
  padding: 12px 0;
  margin-top: 8px;

  div {
    width: 8px;
    height: 8px;
    background: rgba(255, 215, 0, 0.4);
    border-radius: 50%;
  }
`;

const HintSkeletonLoader = styled(motion.div)`
  margin-top: 1rem;
  padding: 1.5rem;
  border-radius: 12px;
  background: rgba(255, 215, 0, 0.05);
  border: 1px solid rgba(255, 215, 0, 0.1);
  height: 80px;
  position: relative;
  overflow: hidden;
  
  &::before, &::after {
    content: '';
    position: absolute;
    inset: 0;
  }

  &::before {
    background: linear-gradient(
      90deg,
      transparent 25%,
      rgba(255, 215, 0, 0.2) 50%,
      transparent 75%
    );
    transform: translateX(-150%);
    animation: shimmer 1.5s infinite, pulse 2s infinite;
  }

  &::after {
    background: repeating-linear-gradient(
      45deg,
      rgba(255, 215, 0, 0.03) 0px,
      rgba(255, 215, 0, 0.03) 10px,
      rgba(255, 215, 0, 0.06) 10px,
      rgba(255, 215, 0, 0.06) 20px
    );
  }

  @keyframes shimmer {
    0% { transform: translateX(-150%); }
    100% { transform: translateX(150%); }
  }

  @keyframes pulse {
    0% { opacity: 0.9; }
    50% { opacity: 0.7; }
    100% { opacity: 0.9; }
  }
`;

const HintWord = styled(motion.span)`
  display: inline-block;
  margin-right: 4px;
`;

// Function to parse markdown tables
const parseMarkdownTable = (text) => {
  const hasTable = text.includes('|') && text.includes('\n');
  if (!hasTable) return { text, tables: [] };

  const tables = [];
  const parts = text.split('\n');
  let currentTable = [];
  let isInTable = false;
  let textParts = [];

  parts.forEach((line, index) => {
    if (line.trim().startsWith('|')) {
      isInTable = true;
      currentTable.push(line);
    } else {
      if (isInTable && currentTable.length > 0) {
        tables.push(currentTable);
        currentTable = [];
        isInTable = false;
      }
      if (line.trim()) {
        textParts.push(line);
      }
    }
  });

  if (currentTable.length > 0) {
    tables.push(currentTable);
  }

  return {
    text: textParts.join('\n'),
    tables: tables.map(tableLines => {
      // Filter out separator rows (rows containing only dashes and pipes)
      const contentRows = tableLines.filter(line => !line.replace(/\|/g, '').trim().match(/^[-\s]+$/));
      
      const rows = contentRows.map(line => {
        // Split by | and remove first and last empty elements
        const cells = line.split('|');
        return cells.slice(1, -1).map(cell => cell.trim());
      });
      
      // First row is always headers
      const headerRow = rows[0];
      const dataRows = rows.slice(1);
      
      return {
        headers: headerRow,
        rows: dataRows
      };
    })
  };
};

// Update renderLatexText function to handle bold markdown
const renderLatexText = (text) => {
  if (!text) return null;

  // First handle LaTeX to prevent splitting formulas
  const parts = text.split(/(\$[^\$]+\$)/g);
  
  return parts.map((part, index) => {
    if (part.startsWith('$') && part.endsWith('$')) {
      // Return LaTeX as a single unit
      const latex = part.slice(1, -1);
      return <InlineMath key={`latex-${index}`} math={latex} />;
    } else {
      // Split non-LaTeX parts into words and process bold
      const words = part.split(/\s+/);
      return words.map((word, wordIndex) => {
        const processedWord = word.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        return word.trim() ? (
          <motion.span
            key={`word-${index}-${wordIndex}`}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ 
              delay: (index + wordIndex) * 0.05,
              duration: 0.3,
              ease: "easeOut"
            }}
            style={{ display: 'inline-block', marginRight: '4px' }}
            dangerouslySetInnerHTML={{ __html: processedWord }}
          />
        ) : ' ';
      });
    }
  });
};

// Function to render a table cell with LaTeX support
const renderTableCell = (content) => {
  return <TableCell>{renderLatexText(content)}</TableCell>;
};

// Update the renderTable function to support LaTeX
const renderTable = (tableData) => {
  return (
    <TableContainer>
      <Table>
        <thead>
          <tr>
            {tableData.headers.map((header, index) => (
              <TableHeader key={index}>{renderLatexText(header)}</TableHeader>
            ))}
          </tr>
        </thead>
        <tbody>
          {tableData.rows.map((row, rowIndex) => (
            <TableRow key={rowIndex}>
              {row.map((cell, cellIndex) => (
                <TableCell key={cellIndex}>{renderLatexText(cell)}</TableCell>
              ))}
            </TableRow>
          ))}
        </tbody>
      </Table>
    </TableContainer>
  );
};

const HintToggleButton = styled(motion.button)`
  background: ${props => props.isGenerated ? 'rgba(255, 215, 0, 0.1)' : 'transparent'};
  border: 2px solid ${props => props.isGenerated ? '#ffd700' : 'rgba(255, 215, 0, 0.3)'};
  border-radius: 12px;
  cursor: pointer;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffd700;
  transition: all 0.3s ease;
  height: 40px;
  gap: 8px;
  font-size: 0.95rem;
  font-weight: 500;
  width: fit-content;
  min-width: 120px;
  backdrop-filter: blur(5px);
  
  &:hover {
    background: rgba(255, 215, 0, 0.15);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(255, 215, 0, 0.1);
  }
  
  &:active {
    transform: translateY(1px);
  }
  
  &:disabled {
    cursor: default;
    color: #666;
    border-color: rgba(102, 102, 102, 0.3);
    background: transparent;
    transform: none;
    box-shadow: none;
  }

  svg {
    font-size: 1.2rem;
  }
`;

const iconStyles = {
  fontSize: '1.2rem',
};

const questionCardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.3 },
  },
  exit: {
    opacity: 0,
    y: -20,
    transition: { duration: 0.2 },
  },
};

const buttonVariants = {
  hidden: { opacity: 0, scale: 0.8, y: 50 },
  visible: (index) => ({
    opacity: 1,
    scale: 1,
    y: 0,
    transition: {
      duration: 0.8,
      delay: index * 0.2,
      type: 'spring',
      stiffness: 100,
      damping: 15,
    },
  }),
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
      ease: 'easeOut',
    },
  },
  exit: {
    opacity: 0,
    scale: 1.05,
    filter: 'blur(10px)',
    transition: {
      duration: 0.3,
      ease: 'easeIn',
    },
  },
};

const notificationVariants = {
  hidden: { opacity: 0, y: -50 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { type: 'spring', stiffness: 300, damping: 25 },
  },
  exit: {
    opacity: 0,
    y: -50,
    transition: { duration: 0.2 },
  },
};

const particleVariants = {
  animate: (i) => ({
    y: [0, -15, 0],
    x: [0, Math.sin(i * Math.PI) * 10, 0],
    opacity: [0.8, 1, 0.8],
    scale: [1, 1.2, 1],
    transition: {
      duration: 2,
      repeat: Infinity,
      delay: i * 0.2,
    }
  })
};

const ExamTaking = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [examData, setExamData] = useState(null);
  const [answers, setAnswers] = useState({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showNotification, setShowNotification] = useState(false);
  const [reportedQuestions, setReportedQuestions] = useState(new Set());
  const [reportingQuestion, setReportingQuestion] = useState(null);
  const [hints, setHints] = useState({});
  const [loadingHints, setLoadingHints] = useState({});
  const [visibleHints, setVisibleHints] = useState({});
  const [currentHint, setCurrentHint] = useState(null); // For mobile view
  const [showMobileHint, setShowMobileHint] = useState(false);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  useEffect(() => {
    const fetchExamData = async () => {
      setIsLoading(true);
      try {
        const data = await api.getExam(id);

        if (data.is_submitted) {
          navigate(`/exam/results/${id}`);
          return;
        }

        const questionsWithIds = data.questions.map((question, index) => ({
          ...question,
          uniqueId: `q${index + 1}`,
        }));
        setExamData({ ...data, questions: questionsWithIds });

        const storedAnswers = localStorage.getItem(`answers_${id}`);
        if (storedAnswers) {
          setAnswers(JSON.parse(storedAnswers));
        }
      } catch (error) {
        console.error('Error fetching exam data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchExamData();
  }, [id, navigate]);

  const handleAnswerChange = (questionId, selectedOption) => {
    setAnswers((prevAnswers) => {
      const newAnswers = { ...prevAnswers, [questionId]: selectedOption };
      console.log('Updated answers:', newAnswers); // Debug log
      localStorage.setItem(`answers_${id}`, JSON.stringify(newAnswers));
      return newAnswers;
    });
  };

const handleHintRequest = async (questionId, questionText) => {
  if (loadingHints[questionId]) return;

  setLoadingHints(prev => ({ ...prev, [questionId]: true }));
  setVisibleHints(prev => ({ ...prev, [questionId]: false }));
  setHints(prev => ({ ...prev, [questionId]: '' }));

  try {
    await api.generateHint(questionText, {
      onProgress: (chunk) => {
        setHints(prev => {
          const newHintText = (prev[questionId] || '') + chunk;
          // Only set visibleHints to true if it was previously false and we have content
          if (!prev[questionId]) {
            setVisibleHints(currentVisibleHints => ({ ...currentVisibleHints, [questionId]: true }));
          }
          setCurrentHint({ id: questionId, text: newHintText });
          return {
            ...prev,
            [questionId]: newHintText
          };
        });
      }
    });
  } catch (error) {
    console.error('Error getting hint:', error);
    setHints(prev => ({
      ...prev,
      [questionId]: "Sorry, couldn't generate a hint at this time."
    }));
  } finally {
    setLoadingHints(prev => ({ ...prev, [questionId]: false }));
  }
};


  const handleSubmit = async () => {
    const unansweredQuestions = examData.questions.filter(
      (question) => !answers[question.uniqueId]
    );

    if (unansweredQuestions.length > 0) {
      setShowNotification(true);
      setTimeout(() => {
        setShowNotification(false);
      }, 2000);
      return;
    }

    setIsSubmitting(true);
    try {
      const formattedAnswers = examData.questions.map((question) => ({
        'question-no': question['question-no'],
        option: answers[question.uniqueId],
      }));

      await api.submitExam(id, { answers: formattedAnswers });
      navigate(`/exam/results/${id}`);
    } catch (error) {
      console.error('Error submitting exam:', error);
      setShowNotification(true);
      setTimeout(() => {
        setShowNotification(false);
      }, 2000);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReportQuestion = async (questionId, questionIndex) => {
    if (reportedQuestions.has(questionId) || reportingQuestion === questionId) {
      return;
    }

    setReportingQuestion(questionId);

    try {
      await api.reportQuestion({
        examId: id,
        questionId: questionId,
        questionIndex: questionIndex + 1,
      });

      setReportedQuestions(prev => new Set([...prev, questionId]));
      setTimeout(() => {
        setReportingQuestion(`${questionId}-done`);
      }, 500);
    } catch (error) {
      console.error('Error reporting question:', error);
      setReportingQuestion(null);
    }
  };

    const toggleHint = (questionId) => {
      setVisibleHints(prev => {
          const newState = { ...prev, [questionId]: !prev[questionId] };
          if (newState[questionId]) {
              setCurrentHint({ id: questionId, text: hints[questionId] });
          } else {
              setCurrentHint(null);
          }
          return newState;
      });
  };

  if (isLoading) {
    return (
      <div className="exam-skeleton-container">
        {[...Array(5)].map((_, index) => (
          <div key={index} className="exam-skeleton-card">
            <div className="exam-skeleton-question" />
            <div className="exam-skeleton-options">
              {[...Array(4)].map((_, optionIndex) => (
                <div key={optionIndex} className="exam-skeleton-option" />
              ))}
            </div>
          </div>
        ))}
        <div className="submit-btn" style={{ width: '100%', marginTop: '2rem' }}>
          <span className="spinner" aria-hidden="true"></span>
          Loading...
        </div>
      </div>
    );
  }

  if (!examData) {
    return <div>Exam not found</div>;
  }

  const lessonStyle = {
    display: 'inline-block',
    backgroundColor: '#2a2a2a',
    padding: '4px 8px',
    margin: '0 4px 4px 0',
    borderRadius: '3px',
    fontSize: '0.9em',
  };

  return (
    <ExamWrapper>
      <ExamContainer className="exam-taking-container">
        <ExamHeader>
          <ExamTitle>{examData.subject} Exam</ExamTitle>
          <LessonsContainer>
            {examData.lessons.map((lesson, index) => (
              <LessonTag key={index}>
                {lesson}
              </LessonTag>
            ))}
          </LessonsContainer>
        </ExamHeader>

        <ExamIdSection>
          <ExamIdTitle>
            <FaChartLine />
            Exam Details
          </ExamIdTitle>
          <ExamIdContent>
            <ExamIdLabel>Exam ID:</ExamIdLabel>
            <CopyableExamId examId={examData['exam-id']} />
          </ExamIdContent>
        </ExamIdSection>

        {showNotification && (
          <motion.div
            className="notification"
            variants={notificationVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
          >
            Please answer all questions before submitting.
          </motion.div>
        )}
        {examData.questions.map((question, index) => {
          const questionId = question.id || question['l-id'];
          return (
            <QuestionCard
              key={question.uniqueId}
              variants={questionCardVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              custom={index}
              transition={{ delay: index * 0.1 }}
            >
              <ReportButton
                onClick={() => handleReportQuestion(questionId, index)}
                disabled={reportedQuestions.has(questionId) || reportingQuestion === questionId}
                title={reportedQuestions.has(questionId) ? "Question reported" : "Report issue with question"}
                variants={buttonVariants}
                initial="hidden"
                animate="visible"
                custom={index}
                whileHover={!reportedQuestions.has(questionId) ? { scale: 1.1 } : {}}
                whileTap={!reportedQuestions.has(questionId) ? { scale: 0.9 } : {}}
              >
                <AnimatePresence mode="wait">
                  <motion.div
                    key={
                      reportingQuestion === questionId
                        ? 'loading'
                        : reportedQuestions.has(questionId)
                        ? 'done'
                        : 'initial'
                    }
                    variants={fadeTransition}
                    initial="hidden"
                    animate="visible"
                    exit="exit"
                  >
                    <IconContainer
                      status={reportingQuestion === questionId ? questionId : reportedQuestions.has(questionId) ? `${questionId}-done` : null}
                      index={questionId}
                    />
                  </motion.div>
                </AnimatePresence>
              </ReportButton>
              
              <QuestionHeader>
                <QuestionNumber>{index + 1}</QuestionNumber>
                <div>
                  <QuestionText>{renderLatexText(question.question)}</QuestionText>
                  {(() => {
                    const { tables } = parseMarkdownTable(question.question);
                    return tables.map((table, tableIndex) => renderTable(table));
                  })()}
                </div>
              </QuestionHeader>

              <OptionsContainer
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: index * 0.1 + 0.3 }}
              >
                {question.options ? (
                  Object.entries(question.options).map(([key, value], optionIndex) => {
                    const isSelected = answers[question.uniqueId] === key;
                    return (
                      <RippleContainer
                        key={key}
                        onClick={(e) => {
                          const rect = e.currentTarget.getBoundingClientRect();
                          const rippleSize = Math.max(rect.width, rect.height);
                          const x = e.clientX - rect.left;
                          const y = e.clientY - rect.top;
                          
                          const ripple = document.createElement('span');
                          ripple.style.width = ripple.style.height = `${rippleSize}px`;
                          ripple.style.left = `${x}px`;
                          ripple.style.top = `${y}px`;
                          ripple.className = 'ripple';
                          
                          e.currentTarget.appendChild(ripple);
                          
                          setTimeout(() => ripple.remove(), 1000);
                          handleAnswerChange(question.uniqueId, key);
                        }}
                      >
                        <Option
                          className={isSelected ? 'selected' : ''}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0 }}
                          transition={{
                            duration: 0.1,
                            ease: "easeOut"
                          }}
                          whileTap={{
                            scale: 0.98,
                          }}
                        >
                          {`${key.toUpperCase()}. `}{renderLatexText(value)}
                        </Option>
                      </RippleContainer>
                    );
                  })
                ) : (
                  <div>No options available for this question.</div>
                )}
              </OptionsContainer>
              
              <motion.div
                style={{ marginTop: '1.5rem' }}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: index * 0.1 + 0.4 }}
              >
                <HintToggleButton
                  onClick={() => {
                    if (hints[question.uniqueId]) {
                      toggleHint(question.uniqueId);
                    } else {
                      handleHintRequest(question.uniqueId, question.question);
                    }
                  }}
                  disabled={loadingHints[question.uniqueId]}
                  isGenerated={hints[question.uniqueId]}
                  variants={buttonVariants}
                  initial="hidden"
                  animate="visible"
                  custom={index}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <AnimatePresence mode="wait">
                    <motion.div
                      key={loadingHints[question.uniqueId] ? 'loading' : 'bulb'}
                      variants={fadeTransition}
                      initial="hidden"
                      animate="visible"
                      exit="exit"
                      style={{ display: 'flex', alignItems: 'center' }}
                    >
                      {loadingHints[question.uniqueId] ? (
                        <motion.div
                          animate={{ rotate: 360 }}
                          transition={{ 
                            duration: 1,
                            repeat: Infinity,
                            ease: "linear"
                          }}
                        >
                          <AiOutlineLoading3Quarters style={{ fontSize: '1.2rem' }} />
                        </motion.div>
                      ) : (
                        <AiOutlineBulb />
                      )}
                    </motion.div>
                  </AnimatePresence>
                  <span>
                    {loadingHints[question.uniqueId] ? 'Generating...' :
                      hints[question.uniqueId] ? 
                        (visibleHints[question.uniqueId] ? 'Hide Hint' : 'Show Hint') : 
                        'Get Hint'
                    }
                  </span>
                </HintToggleButton>

                {loadingHints[question.uniqueId] && (
                    <>
                      <HintSkeletonLoader
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 80 }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.3 }}
                      />
                      <LoadingDots
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.3 }}
                      >
                        {[...Array(3)].map((_, i) => (
                          <motion.div
                            key={i}
                            animate={{
                              y: [-3, 3, -3],
                              opacity: [0.4, 1, 0.4]
                            }}
                            transition={{
                              y: {
                                duration: 1.2,
                                repeat: Infinity,
                                delay: i * 0.2
                              },
                              opacity: {
                                duration: 1.2,
                                repeat: Infinity,
                                delay: i * 0.2
                              }
                            }}
                          />
                        ))}
                      </LoadingDots>
                    </>
                  )}
                {hints[question.uniqueId] && visibleHints[question.uniqueId] && (
                  <HintContainer>
                    <ReactMarkdown
                      key={hints[question.uniqueId]}
                      remarkPlugins={[remarkGfm, remarkMath]}
                      rehypePlugins={[rehypeKatex]}
                    >
                      {hints[question.uniqueId]}
                    </ReactMarkdown>
                  </HintContainer>
                )}
              </motion.div>
            </QuestionCard>
          );
        })}
          <motion.button
            className="submit-btn"
          onClick={handleSubmit}
          disabled={isSubmitting}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          style={{
            border: 'none',
            borderRadius: '8px',
            color: 'white',
            padding: '12px 24px',
            position: 'relative',
            overflow: 'hidden',
            background: '#2196f3',
            minWidth: '150px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '10px'
          }}
        >
          {isSubmitting ? (
            <>
              <motion.svg
                width="40"
                height="40"
                viewBox="0 0 50 50"
                style={{ position: 'relative' }}
              >
                {/* Background circle with wave effect */}
                <motion.circle
                  cx="25"
                  cy="25"
                  r="20"
                  fill="#2196f3"
                  animate={{
                    r: [20, 22, 20],
                    filter: [
                      'drop-shadow(0 0 2px #2196f3)',
                      'drop-shadow(0 0 8px #2196f3)',
                      'drop-shadow(0 0 2px #2196f3)'
                    ]
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                />

                {/* Liquid blob */}
                <motion.path
                  fill="#ffffff"
                  animate={{
                    d: [
                      "M25,15 C28,15 31,17 31,20 C31,23 28,25 25,25 C22,25 19,23 19,20 C19,17 22,15 25,15",
                      "M25,15 C29,15 33,17 33,21 C31,24 29,25 25,25 C21,25 19,24 17,21 C17,17 21,15 25,15",
                      "M25,15 C28,15 31,17 31,20 C31,23 28,25 25,25 C22,25 19,23 19,20 C19,17 22,15 25,15"
                    ],
                    opacity: [0.7, 1, 0.7]
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                />

                {/* Floating particles */}
                {[...Array(8)].map((_, i) => (
                  <motion.circle
                    key={i}
                    r={1.5}
                    fill="#ffffff"
                    custom={i}
                    variants={particleVariants}
                    animate="animate"
                    style={{
                      originX: 0.5,
                      originY: 0.5,
                    }}
                    cx={25 + Math.cos(i * Math.PI / 4) * 10}
                    cy={25 + Math.sin(i * Math.PI / 4) * 10}
                  />
                ))}

                {/* Central spinning ring */}
                <motion.circle
                  cx="25"
                  cy="25"
                  r="15"
                  fill="none"
                  stroke="rgba(255,255,255,0.5)"
                  strokeWidth="1"
                  strokeDasharray="20 20"
                  animate={{
                    rotate: [0, 360],
                  }}
                  transition={{
                    duration: 8,
                    repeat: Infinity,
                    ease: "linear"
                  }}
                />

                {/* Pulsing core */}
                <motion.circle
                  cx="25"
                  cy="25"
                  r="5"
                  fill="#ffffff"
                  animate={{
                    r: [5, 7, 5],
                    opacity: [0.5, 1, 0.5],
                  }}
                  transition={{
                    duration: 1.5,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                />
              </motion.svg>
              <motion.span
                style={{ marginLeft: '8px' }}
                animate={{
                  opacity: [1, 0.7, 1],
                }}
                transition={{
                  duration: 1.5,
                  repeat: Infinity,
                  ease: "easeInOut"
                }}
              >
                Submitting...
              </motion.span>
            </>
          ) : (
            'Submit Exam'
          )}
        </motion.button>
      </ExamContainer>
      <MobilePopup
        isOpen={currentHint !== null}
        onClose={() => {
          if (currentHint) {
            toggleHint(currentHint.id);
          }
        }}
        title="Hint"
      >
        <HintContent>
          <div className="hint-content">
            {currentHint && (
              <ReactMarkdown
                key={currentHint.text}
                remarkPlugins={[remarkGfm, remarkMath]}
                rehypePlugins={[rehypeKatex]}
              >
                {currentHint.text}
              </ReactMarkdown>
            )}
          </div>
        </HintContent>
      </MobilePopup>
    </ExamWrapper>
  );
};

export default ExamTaking;