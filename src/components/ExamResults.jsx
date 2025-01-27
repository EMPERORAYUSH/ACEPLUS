import React, { useState, useEffect } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { FaChartLine, FaLightbulb, FaExclamationTriangle, FaCheckCircle } from 'react-icons/fa';
import { motion } from 'framer-motion';
import styled from 'styled-components';
import CopyableExamId from './CopyableExamId';
import { api } from '../utils/api';
import 'katex/dist/katex.min.css';
import { InlineMath, BlockMath } from 'react-katex';

const renderLatexString = (text) => {
  if (!text) return text;
  
  // First split by LaTeX expressions
  const parts = text.split(/(\$\$.*?\$\$|\$.*?\$)/gs);
  
  return parts.map((part, index) => {
    if (part.startsWith('$$') && part.endsWith('$$')) {
      // Display mode LaTeX
      const latex = part.slice(2, -2);
      return <BlockMath key={`latex-${index}`} math={latex} />;
    } else if (part.startsWith('$') && part.endsWith('$')) {
      // Inline mode LaTeX
      const latex = part.slice(1, -1);
      return <InlineMath key={`latex-${index}`} math={latex} />;
    } else {
      // Process HTML tags and bold text in non-LaTeX parts
      const processHTML = (text) => {
        const parts = [];
        let currentText = '';
        let i = 0;
        
        while (i < text.length) {
          if (text[i] === '<') {
            // If we have accumulated text, push it
            if (currentText) {
              parts.push(currentText);
              currentText = '';
            }
            
            // Find the end of the tag
            const tagEnd = text.indexOf('>', i);
            if (tagEnd === -1) {
              currentText += text[i];
              i++;
              continue;
            }
            
            const fullTag = text.slice(i, tagEnd + 1);
            const isClosingTag = fullTag.startsWith('</');
            const tagName = isClosingTag ? 
              fullTag.slice(2, -1).toLowerCase() : 
              fullTag.slice(1, -1).toLowerCase();
            
            if (isClosingTag) {
              // Handle closing tag
              parts.push(`</${tagName}>`);
              i = tagEnd + 1;
            } else {
              // Handle opening tag
              if (tagName === 'br') {
                parts.push(<br key={`br-${i}`} />);
                i = tagEnd + 1;
              } else {
                // Find the closing tag
                const closingTag = `</${tagName}>`;
                const closingIndex = text.indexOf(closingTag, tagEnd);
                
                if (closingIndex === -1) {
                  currentText += text[i];
                  i++;
                  continue;
                }
                
                // Get the content between tags
                const content = text.slice(tagEnd + 1, closingIndex);
                
                // Create the appropriate element based on tag name
                switch (tagName) {
                  case 'sub':
                    parts.push(<sub key={`sub-${i}`}>{processHTML(content)}</sub>);
                    break;
                  case 'sup':
                    parts.push(<sup key={`sup-${i}`}>{processHTML(content)}</sup>);
                    break;
                  case 'i':
                    parts.push(<i key={`i-${i}`}>{processHTML(content)}</i>);
                    break;
                  case 'b':
                    parts.push(<b key={`b-${i}`}>{processHTML(content)}</b>);
                    break;
                  case 'u':
                    parts.push(<u key={`u-${i}`}>{processHTML(content)}</u>);
                    break;
                  case 'em':
                    parts.push(<em key={`em-${i}`}>{processHTML(content)}</em>);
                    break;
                  default:
                    parts.push(content);
                }
                
                i = closingIndex + closingTag.length;
              }
            }
          } else if (text.slice(i).startsWith('**')) {
            // Handle bold text
            if (currentText) {
              parts.push(currentText);
              currentText = '';
            }
            
            const endBold = text.indexOf('**', i + 2);
            if (endBold === -1) {
              currentText += text[i];
              i++;
              continue;
            }
            
            const boldContent = text.slice(i + 2, endBold);
            parts.push(<strong key={`bold-${i}`}>{processHTML(boldContent)}</strong>);
            i = endBold + 2;
          } else {
            currentText += text[i];
            i++;
          }
        }
        
        if (currentText) {
          parts.push(currentText);
        }
        
        return parts;
      };

      return processHTML(part);
    }
  });
};

const ResultSkeleton = () => (
  <div className="question-result skeleton">
    <div className="skeleton-text" style={{ width: '60%', height: '24px', marginBottom: '10px' }}></div>
    <div className="skeleton-text" style={{ width: '40%', height: '18px', marginBottom: '10px' }}></div>
    <div className="skeleton-text" style={{ width: '80%', height: '18px', marginBottom: '10px' }}></div>
    <div className="skeleton-text" style={{ width: '70%', height: '18px' }}></div>
  </div>
);

const PerformanceAnalysisContainer = styled(motion.div)`
  background: #1a1a1a;
  border-radius: 12px;
  padding: 2rem 0;
  margin: 2rem 0;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;
  width: 100%;
  
  /* Ensure smooth transitions for width changes */
  transition: all 0.3s ease-in-out;
  
  /* Create a stable layout that prevents scroll jumps */
  contain: layout paint;
  min-height: fit-content;
  transform-origin: bottom center;

  .performance-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 2rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);

    h2 {
      margin: 0;
      font-size: 1.8rem;
      background: linear-gradient(135deg, #ffffff 0%, #b3b3b3 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .analysis-icon {
      font-size: 1.8rem;
      color: #4a90e2;
    }
  }

  @media (max-width: 768px) {
    padding: 1.5rem 0;
    margin: 1rem 0;

    .performance-header {
      margin-bottom: 1.5rem;
      
      h2 {
        font-size: 1.5rem;
      }

      .analysis-icon {
        font-size: 1.5rem;
      }
    }
  }
`;

const AnalysisSection = styled(motion.div)`
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.06);
  
  /* Ensure smooth text wrapping */
  overflow-wrap: break-word;
  word-wrap: break-word;
  hyphens: auto;

  .section-header {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);

    .section-icon {
      font-size: 1.4rem;
      color: #4a90e2;
    }

    h3 {
      margin: 0;
      font-size: 1.2rem;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #ffffff;
      font-weight: 600;
    }
  }

  .section-content {
    color: #e0e0e0;
    font-size: 1.1rem;
    line-height: 1.6;
    letter-spacing: 0.3px;
    position: relative;

    &::before {
      content: '';
      position: absolute;
      left: 0;
      top: 0;
      bottom: 0;
      width: 2px;
      background: linear-gradient(180deg, 
        rgba(74, 144, 226, 0) 0%,
        rgba(74, 144, 226, 0.3) 10%,
        rgba(74, 144, 226, 0.3) 90%,
        rgba(74, 144, 226, 0) 100%
      );
    }

    .content-line {
      margin: 0.8rem 0;
      padding-left: 1.5rem;
      position: relative;

      &::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0.8em;
        width: 0.8rem;
        height: 1px;
        background: rgba(74, 144, 226, 0.3);
      }

      &:first-child {
        margin-top: 0;
      }

      &:last-child {
        margin-bottom: 0;
      }

      strong {
        color: #4a90e2;
        font-weight: 600;
      }

      /* Style for bullet points */
      &[data-bullet="true"] {
        padding-left: 2.5rem;
        
        &::before {
          width: 1.8rem;
        }
        
        &::after {
          content: "•";
          position: absolute;
          left: 1.5rem;
          top: 0.1em;
          color: #4a90e2;
          font-size: 1.2em;
        }
      }
    }

    .indent-2 {
      margin-left: 1rem;
      
      &::before {
        left: -1rem;
        width: 1.8rem;
      }
    }

    .indent-4 {
      margin-left: 2rem;
      
      &::before {
        left: -2rem;
        width: 2.8rem;
      }
    }
  }

  @media (max-width: 768px) {
    padding: 1.2rem;
    margin-bottom: 0.8rem;

    .section-header {
      padding-bottom: 0.8rem;
      margin-bottom: 1.2rem;

      .section-icon {
        font-size: 1.2rem;
      }

      h3 {
        font-size: 1.1rem;
      }
    }

    .section-content {
      font-size: 1rem;
      line-height: 1.5;

      .content-line {
        padding-left: 1.2rem;
        margin: 0.6rem 0;

        &::before {
          width: 0.6rem;
        }

        &[data-bullet="true"] {
          padding-left: 2rem;
          
          &::before {
            width: 1.4rem;
          }
          
          &::after {
            left: 1.2rem;
          }
        }
      }

      .indent-2 {
        margin-left: 0.8rem;
        
        &::before {
          left: -0.8rem;
          width: 1.4rem;
        }
      }

      .indent-4 {
        margin-left: 1.2rem;
        
        &::before {
          left: -1.2rem;
          width: 2rem;
        }
      }
    }
  }

  &:hover {
    background: rgba(255, 255, 255, 0.05);
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    transition: all 0.3s ease;
  }
`;

const PerformanceAnalysis = ({ analysis }) => {
  if (!analysis) return null;

  const sections = analysis.split('###').filter(s => s.trim());

  const containerVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.5,
        staggerChildren: 0.2
      }
    }
  };

  const sectionVariants = {
    hidden: { 
      opacity: 0,
      x: -20
    },
    visible: {
      opacity: 1,
      x: 0,
      transition: {
        duration: 0.5,
        ease: "easeOut"
      }
    }
  };

  const getIconForSection = (title) => {
    const upperCaseTitle = title.trim().toUpperCase();
    switch (upperCaseTitle) {
      case 'PERFORMANCE OVERVIEW':
        return <FaChartLine className="section-icon" />;
      case 'TOPIC ANALYSIS':
        return <FaExclamationTriangle className="section-icon" />;
      case 'FOCUS AREAS':
        return <FaLightbulb className="section-icon" />;
      case 'NEXT STEPS': 
        return <FaCheckCircle className="section-icon" />;
      default:
        return <FaChartLine className="section-icon" />;
    }
  };

  return (
    <PerformanceAnalysisContainer
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      <div className="performance-header">
        <FaChartLine className="analysis-icon" />
        <h2>PERFORMANCE ANALYSIS</h2>
      </div>
      
      <div className="analysis-content">
        {sections.map((section, index) => {
          const [title, ...content] = section.trim().split('\n');
          const contentText = content.join('\n').trim();
          const upperCaseTitle = title.trim().toUpperCase();
          
          return (
            <AnalysisSection 
              key={index} 
              variants={sectionVariants}
              whileHover={{ 
                scale: 1.01,
                transition: { duration: 0.2 }
              }}
            >
              <div className="section-header">
                {getIconForSection(title)}
                <h3>{upperCaseTitle}</h3>
              </div>
              <div className="section-content">
                {contentText.split('\n').map((line, lineIndex) => {
                  const indentLevel = line.match(/^\s*/)[0].length;
                  const cleanLine = line.trim();
                  if (!cleanLine) return null;
                  
                  // Check if line starts with *
                  const isBulletPoint = cleanLine.startsWith('*');
                  const processedLine = isBulletPoint ? cleanLine.slice(1).trim() : cleanLine;
                  
                  return (
                    <p 
                      key={lineIndex} 
                      className={`content-line indent-${indentLevel}`}
                      data-bullet={isBulletPoint}
                    >
                      {renderLatexString(processedLine)}
                    </p>
                  );
                })}
              </div>
            </AnalysisSection>
          );
        })}
      </div>
    </PerformanceAnalysisContainer>
  );
};

const AnalyticsContainer = styled(motion.div)`
  margin: 20px auto;
  padding: 20px;
  background: linear-gradient(135deg, #1a1a1a 0%, #2a2a2a 100%);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  max-width: 1200px;
  width: 100%;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
`;

const AnalyticsTitle = styled.h3`
  font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 1.5rem;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  text-align: center;

  svg {
    color: #4a90e2;
  }
`;

const LessonGrid = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  width: 100%;
  justify-content: center;
`;

const LessonCard = styled(motion.div)`
  background: linear-gradient(145deg, #1f1f1f, #242424);
  padding: 1.2rem;
  border-radius: 12px;
  border: 1px solid #383838;
  transition: all 0.3s ease;
  flex: 0 1 300px;  
  min-width: 250px; 
  max-width: 350px; 

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    border-color: ${props => props.percentage >= 70 
      ? '#4caf50' 
      : props.percentage >= 40 
      ? '#ff9800' 
      : '#f44336'};
  }
`;

const LessonHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
`;

const LessonName = styled.h4`
  font-weight: 500;
  margin: 0;
  color: #ffffff;
  font-size: 1.1rem;
`;

const LessonScore = styled.span`
  font-size: 0.9rem;
  font-weight: 600;
  color: ${props => props.percentage >= 70 
    ? '#4caf50' 
    : props.percentage >= 40 
    ? '#ff9800' 
    : '#f44336'};
  background-color: ${props => props.percentage >= 70 
    ? 'rgba(76, 175, 80, 0.1)' 
    : props.percentage >= 40 
    ? 'rgba(255, 152, 0, 0.1)' 
    : 'rgba(244, 67, 54, 0.1)'};
  padding: 4px 8px;
  border-radius: 6px;
`;

const ProgressBarBg = styled.div`
  width: 100%;
  height: 8px;
  background-color: #2a2a2a;
  border-radius: 999px;
  overflow: hidden;
`;

const ProgressBarFill = styled.div`
  height: 100%;
  background: ${props => props.percentage >= 70 
    ? 'linear-gradient(90deg, #4caf50, #81c784)'
    : props.percentage >= 40 
    ? 'linear-gradient(90deg, #ff9800, #ffb74d)'
    : 'linear-gradient(90deg, #f44336, #e57373)'};
  border-radius: 999px;
  transition: width 0.5s ease, background-color 0.3s ease;
`;

const LessonAnalytics = ({ lessonAnalytics }) => {
  if (!lessonAnalytics) return null;

  return (
    <AnalyticsContainer
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <AnalyticsTitle>
        <FaChartLine />
        LESSON-WISE ANALYSIS
      </AnalyticsTitle>
      <LessonGrid>
        {Object.entries(lessonAnalytics).map(([lessonId, data]) => (
          <LessonCard 
            key={lessonId}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
          >
            <LessonHeader>
              <LessonName>{data.lesson_name}</LessonName>
              <LessonScore percentage={data.percentage}>
                {data.questions_correct}/{data.questions_total} ({Math.round(data.percentage)}%)
              </LessonScore>
            </LessonHeader>
            <ProgressBarBg>
              <ProgressBarFill
                percentage={data.percentage}
                style={{ width: `${data.percentage}%` }}
              />
            </ProgressBarBg>
          </LessonCard>
        ))}
      </LessonGrid>
    </AnalyticsContainer>
  );
};

const OptionsList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  margin: 1rem 0;
`;

const Option = styled.div`
  padding: 1.2rem 1.5rem;
  border-radius: 8px;
  background: ${props => {
    if (props.$isCorrect) return 'rgba(76, 175, 80, 0.12)';
    if (props.$isWrong) return 'rgba(244, 67, 54, 0.12)';
    return 'rgba(255, 255, 255, 0.02)';
  }};
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid ${props => {
    if (props.$isCorrect) return '#4caf50';
    if (props.$isWrong) return '#f44336';
    return 'rgba(255, 255, 255, 0.1)';
  }};
  color: ${props => {
    if (props.$isCorrect) return '#4caf50';
    if (props.$isWrong) return '#f44336';
    return '#ffffff';
  }};
  position: relative;
  padding-right: ${props => (props.$isSelected || props.$isCorrect || props.$isWrong) ? '3.5rem' : '1.5rem'};
  font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
  font-size: 1.1rem;
  line-height: 1.5;
  letter-spacing: 0.2px;
  font-weight: 500;
  
  ${props => props.$isWrong && `
    &::after {
      content: '✗';
      position: absolute;
      right: 1.5rem;
      top: 50%;
      transform: translateY(-50%);
      color: #f44336;
      font-weight: bold;
      font-size: 1.4rem;
    }
  `}
  
  ${props => props.$isCorrect && `
    &::after {
      content: '✓';
      position: absolute;
      right: 1.5rem;
      top: 50%;
      transform: translateY(-50%);
      color: #4caf50;
      font-weight: bold;
      font-size: 1.4rem;
    }
  `}

  transition: all 0.2s ease;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  
  &:hover {
    background: ${props => {
      if (props.$isCorrect) return 'rgba(76, 175, 80, 0.18)';
      if (props.$isWrong) return 'rgba(244, 67, 54, 0.18)';
      return 'rgba(255, 255, 255, 0.08)';
    }};
    transform: translateY(-2px);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  }

  .katex {
    font-size: 1.1em;
  }
`;

const ExamResultsWrapper = styled.div`
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding-top: 40px;
  transition: margin-left 0.3s ease-in-out;
  margin-left: 80px;
  font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
  letter-spacing: 0.2px;
  * {
    font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
  }

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

  .sidebar:hover ~ & {
    margin-left: 220px;
  }

  @media (max-width: 768px) {
    margin-left: 0;
    padding-top: 20px;
  }
`;

const ExamResultsContainer = styled.div`
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
  transition: all 0.3s ease-in-out;
  transform-origin: bottom center;
  width: 100%;

  .question-result {
    margin-bottom: 3rem;
    background: rgba(255, 255, 255, 0.03);
    padding: 2rem;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    
    h3 {
      font-size: 1.4rem;
      font-weight: 600;
      color: #ffffff;
      margin-bottom: 1.5rem;
      line-height: 1.4;
      letter-spacing: 0.2px;
    }

    .solution-card {
      background: rgba(255, 255, 255, 0.05);
      border-radius: 8px;
      padding: 1.5rem;
      margin-top: 1.5rem;
      border: 1px solid rgba(255, 255, 255, 0.08);

      h4 {
        font-size: 1.2rem;
        font-weight: 600;
        color: #e0e0e0;
        margin-bottom: 1rem;
        letter-spacing: 0.2px;
        text-transform: uppercase;
      }

      p {
        font-size: 1.1rem;
        line-height: 1.6;
        color: #ffffff;
        letter-spacing: 0.2px;
        font-weight: 400;
      }
    }
  }

  @media (max-width: 768px) {
    padding: 1rem;
    margin-bottom: 60px;

    .question-result {
      padding: 1.5rem;
      margin-bottom: 2rem;
    }
  }
`;

const ExamIdSection = styled.div`
  background: #1a1a1a;
  border-radius: 12px;
  padding: 1.5rem;
  margin: 1.5rem auto;
  max-width: 800px;
  width: calc(100% - 2rem);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);

  @media (max-width: 768px) {
    padding: 1.2rem;
    margin: 1rem auto;
    width: calc(100% - 1rem);
  }
`;

const ExamIdTitle = styled.h3`
  margin: 0;
  color: #667eea;
  font-size: 1.5rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 0.8rem;
  letter-spacing: -0.3px;
  text-transform: uppercase;

  svg {
    font-size: 1.6rem;
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

const ResultsSummaryCard = styled(motion.div)`
  background: linear-gradient(135deg, #1E1E1E 0%, #2D2D2D 100%);
  border-radius: 24px;
  padding: 3rem;
  margin: 1rem auto;
  max-width: 800px;
  width: calc(100% - 2rem);
  position: relative;
  overflow: hidden;
  box-shadow: 
    0 25px 50px -12px rgba(0, 0, 0, 0.5),
    0 0 0 1px rgba(255, 255, 255, 0.1);
  transform-style: preserve-3d;
  perspective: 1000px;
  transition: all 0.3s ease;

  &:hover {
    transform: translateY(-5px);
    box-shadow: 
      0 30px 60px -15px rgba(0, 0, 0, 0.6),
      0 0 0 1px rgba(255, 255, 255, 0.15);
  }

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: ${props => props.percentage >= 70 
      ? 'linear-gradient(90deg, #4CAF50, #81C784)'
      : props.percentage >= 40 
      ? 'linear-gradient(90deg, #FF9800, #FFB74D)'
      : 'linear-gradient(90deg, #F44336, #E57373)'};
  }

  @media (max-width: 768px) {
    padding: 2rem 1.5rem;
    margin: 1rem auto;
    width: calc(100% - 1rem);
  }
`;

const ResultsContent = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4rem;
  
  @media (max-width: 768px) {
    flex-direction: column;
    gap: 2rem;
  }
`;

const CircularProgress = styled(motion.div)`
  position: relative;
  width: 280px;
  height: 280px;
  background: linear-gradient(145deg, #1f1f1f, #242424);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 
    inset 0 0 50px rgba(0,0,0,0.3),
    0 0 30px rgba(0,0,0,0.2);
  transform-style: preserve-3d;
  transition: all 0.3s ease;
  cursor: pointer;

  &:hover {
    transform: translateY(-5px) scale(1.02);
    box-shadow: 
      inset 0 0 60px rgba(0,0,0,0.4),
      0 20px 40px rgba(0,0,0,0.3);
  }

  &::before {
    content: '';
    position: absolute;
    width: 100%;
    height: 100%;
    border-radius: 50%;
    background: conic-gradient(
      ${props => props.percentage >= 70 
        ? '#4CAF50'
        : props.percentage >= 40 
        ? '#FF9800'
        : '#F44336'} 
      ${props => props.percentage}%, 
      #333 0
    );
    mask: radial-gradient(transparent 65%, black 66%);
    -webkit-mask: radial-gradient(transparent 65%, black 66%);
    transition: filter 0.3s ease;
  }

  &:hover::before {
    filter: brightness(1.1);
  }

  &::after {
    content: '';
    position: absolute;
    top: 10px;
    left: 10px;
    right: 10px;
    bottom: 10px;
    border-radius: 50%;
    background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
    filter: blur(2px);
    opacity: 0.5;
    transition: opacity 0.3s ease;
  }

  &:hover::after {
    opacity: 0.7;
  }

  @media (max-width: 768px) {
    width: 220px;
    height: 220px;
  }
`;

const ScoreDisplay = styled.div`
  text-align: center;
  position: relative;
  z-index: 1;
  background: linear-gradient(145deg, #1a1a1a, #222);
  padding: 2rem;
  border-radius: 50%;
  width: 75%;
  height: 75%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 2px 4px rgba(255,255,255,0.1);
  transform-style: preserve-3d;
  transition: all 0.3s ease;

  ${CircularProgress}:hover & {
    transform: translateZ(20px);
    box-shadow: 
      inset 0 2px 4px rgba(255,255,255,0.15),
      0 10px 20px rgba(0,0,0,0.2);
  }

  .percentage {
    font-size: 4.5rem;
    font-weight: 800;
    background: ${props => props.percentage >= 70 
      ? 'linear-gradient(to bottom right, #fff, #4CAF50)'
      : props.percentage >= 40 
      ? 'linear-gradient(to bottom right, #fff, #FF9800)'
      : 'linear-gradient(to bottom right, #fff, #F44336)'};
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    line-height: 1;
    margin-bottom: 0.5rem;
    font-family: 'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
    position: relative;
    display: flex;
    align-items: center;
    transition: transform 0.3s ease;
    
    ${CircularProgress}:hover & {
      transform: scale(1.05);
    }
    
    &::after {
      content: '%';
      font-size: 2rem;
      margin-left: 0.3rem;
      opacity: 0.8;
      background: inherit;
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
  }

  .score {
    font-size: 1.4rem;
    color: #666;
    font-weight: 600;
    margin-top: 0.5rem;
    letter-spacing: 1px;
    transition: color 0.3s ease;

    ${CircularProgress}:hover & {
      color: #888;
    }
  }

  @media (max-width: 768px) {
    padding: 1.5rem;
    
    .percentage {
      font-size: 3.5rem;
      
      &::after {
        font-size: 1.6rem;
      }
    }
    
    .score {
      font-size: 1.2rem;
    }
  }
`;

const StatsContainer = styled.div`  display: flex;
  flex-direction: column;
  gap: 2rem;
  padding-left: 2rem;
  border-left: 2px solid rgba(255, 255, 255, 0.1);

  @media (max-width: 768px) {
    padding-left: 0;
    border-left: none;
    border-top: 2px solid rgba(255, 255, 255, 0.1);
    padding-top: 2rem;
  }
`;

const StatBox = styled.div`
  background: rgba(255, 255, 255, 0.03);
  padding: 1.5rem;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  transform-style: preserve-3d;
  transition: all 0.3s ease;
  cursor: pointer;
  text-align: center;

  &:hover {
    transform: translateY(-5px) rotateX(2deg) rotateY(-2deg);
    background: rgba(255, 255, 255, 0.05);
    border-color: rgba(255, 255, 255, 0.1);
    box-shadow: 
      0 15px 30px -10px rgba(0, 0, 0, 0.3),
      0 0 0 1px rgba(255, 255, 255, 0.1);
  }

  .label {
    font-size: 1rem;
    color: #888;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 0.5rem;
    font-weight: 500;
    transition: color 0.3s ease;
  }

  .value {
    font-size: 2.2rem;
    font-weight: 700;
    color: #FFF;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    transition: transform 0.3s ease;
  }

  .subtitle {
    font-size: 0.9rem;
    color: #666;
    margin-top: 0.5rem;
    transition: color 0.3s ease;
  }

  &:hover .label {
    color: #aaa;
  }

  &:hover .value {
    transform: translateZ(10px);
  }

  &:hover .subtitle {
    color: #888;
  }
`;

const GradeIndicator = styled.div`
  font-size: 3.5rem;
  font-weight: 800;
  color: ${props => props.percentage >= 70 
    ? '#4CAF50'
    : props.percentage >= 40 
    ? '#FF9800'
    : '#F44336'};
  text-shadow: 0 0 20px ${props => props.percentage >= 70 
    ? 'rgba(76, 175, 80, 0.3)'
    : props.percentage >= 40 
    ? 'rgba(255, 152, 0, 0.3)'
    : 'rgba(244, 67, 54, 0.3)'};
  transition: all 0.3s ease;

  ${StatBox}:hover & {
    transform: translateZ(15px);
    text-shadow: 0 0 30px ${props => props.percentage >= 70 
      ? 'rgba(76, 175, 80, 0.5)'
      : props.percentage >= 40 
      ? 'rgba(255, 152, 0, 0.5)'
      : 'rgba(244, 67, 54, 0.5)'};
  }
`;

const ExamResults = () => {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const [results, setResults] = useState(null);
  const [examData, setExamData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchResults = async () => {
      setIsLoading(true);
      try {
        if (location.state && location.state.results) {
          setResults(location.state.results);
          setExamData(location.state);
        } else {
          const examData = await api.getExam(id);

          if (!examData.is_submitted) {
            navigate(`/exam/g/${id}`);
            return;
          }

          setExamData(examData);
          setResults(examData.results);
        }
      } catch (error) {
        console.error('Error fetching results:', error);
        if (error.message === 'Unauthorized access') {
          navigate('/login');
        }
        setResults(null);
        setExamData(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchResults();
  }, [id, navigate, location.state]);

  if (isLoading) {
    return (
      <ExamResultsWrapper>
        <ExamResultsContainer>
          <h1 style={{ textAlign: 'center' }}>Exam Results</h1>
          <div className="results-summary skeleton">
            <div className="skeleton-text" style={{ width: '40%', height: '24px', marginBottom: '10px' }}></div>
            <div className="skeleton-text" style={{ width: '60%', height: '24px' }}></div>
          </div>
          {[...Array(5)].map((_, index) => (
            <ResultSkeleton key={index} />
          ))}
        </ExamResultsContainer>
      </ExamResultsWrapper>
    );
  }

  if (!results) {
    return (
      <ExamResultsWrapper>
        <ExamResultsContainer className="no-results">
          No results found.
        </ExamResultsContainer>
      </ExamResultsWrapper>
    );
  }

  return (
    <ExamResultsWrapper>
      <ExamResultsContainer>
        <h1 style={{ textAlign: 'center' }}>Exam Results</h1>
        
        <ResultsSummaryCard
          percentage={results.filter(r => r.is_correct).length / results.length * 100}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <ResultsContent>
            <CircularProgress
              percentage={results.filter(r => r.is_correct).length / results.length * 100}
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.8, delay: 0.2 }}
            >
              <ScoreDisplay percentage={results.filter(r => r.is_correct).length / results.length * 100}>
                <div className="percentage">
                  {Math.round(results.filter(r => r.is_correct).length / results.length * 100)}
                </div>
                <div className="score">
                  {results.filter(r => r.is_correct).length} / {results.length}
                </div>
              </ScoreDisplay>
            </CircularProgress>

            <StatsContainer>
              <StatBox>
                <div className="label">Performance Grade</div>
                <div className="value" style={{ flexDirection: 'column', gap: '0.3rem' }}>
                  <GradeIndicator percentage={results.filter(r => r.is_correct).length / results.length * 100}>
                    {results.filter(r => r.is_correct).length / results.length * 100 >= 70 
                      ? 'A' 
                      : results.filter(r => r.is_correct).length / results.length * 100 >= 40 
                      ? 'B' 
                      : 'C'}
                  </GradeIndicator>
                  <span style={{ fontSize: '1.2rem', color: '#666' }}>
                    {results.filter(r => r.is_correct).length / results.length * 100 >= 70 
                      ? 'Excellent' 
                      : results.filter(r => r.is_correct).length / results.length * 100 >= 40 
                      ? 'Good' 
                      : 'Needs Improvement'}
                  </span>
                </div>
              </StatBox>

              <StatBox>
                <div className="label">Lessons Attempted</div>
                <div className="value" style={{ justifyContent: 'center', fontSize: '2.5rem' }}>
                  {examData?.lesson_analytics ? Object.keys(examData.lesson_analytics).length : 0}
                </div>
                <div className="subtitle" style={{ fontSize: '1.1rem', color: '#888', marginTop: '0.8rem' }}>
                  Topics Covered in Exam
                </div>
              </StatBox>
            </StatsContainer>
          </ResultsContent>
        </ResultsSummaryCard>

        {examData && examData['exam-id'] && (
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
        )}

        {examData?.lesson_analytics && (
          <LessonAnalytics lessonAnalytics={examData.lesson_analytics} />
        )}

        {examData?.performance_analysis && (
          <PerformanceAnalysis analysis={examData.performance_analysis} />
        )}

        {results.map((result) => {
          const questionData = examData.questions.find(q => q.question === result.question);
          
          return (
            <div key={result['question-no']} className={`question-result ${result.is_correct ? 'correct' : 'incorrect'}`}>
              <h3>{result['question-no']}. {renderLatexString(result.question)}</h3>
              
              <OptionsList>
                {['a', 'b', 'c', 'd'].map((optionKey) => {
                  const optionText = questionData.options[optionKey];
                  const fullOptionText = `${optionKey.toUpperCase()}) ${optionText}`;
                  
                  const isSelectedOption = result.selected_answer.toLowerCase() === `${optionKey}) ${optionText}`.toLowerCase();
                  const isCorrectOption = questionData.answer.toLowerCase() === optionKey;
                  const isWrongOption = isSelectedOption && !isCorrectOption;

                  return (
                    <Option
                      key={optionKey}
                      $isSelected={isSelectedOption}
                      $isCorrect={isCorrectOption}
                      $isWrong={isWrongOption}
                    >
                      {renderLatexString(fullOptionText)}
                    </Option>
                  );
                })}
              </OptionsList>

              {!result.is_correct && (
                <div className="solution-card">
                  <h4>Solution:</h4>
                  <p>{renderLatexString(result.solution)}</p>
                </div>
              )}
            </div>
          );
        })}
      </ExamResultsContainer>
    </ExamResultsWrapper>
  );
};

export default ExamResults;
