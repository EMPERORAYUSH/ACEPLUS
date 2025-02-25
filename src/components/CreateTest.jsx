import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';


import { FaEdit, FaTrash } from 'react-icons/fa';
import { IoMdAdd } from 'react-icons/io';
import styled from 'styled-components';
import { ExamSkeletonLoading } from './Exam';
import { questionCardVariants, buttonVariants } from './animations';
import { api, API_BASE_URL } from '../utils/api';
import { Dialog } from '@mui/material';
import { Skeleton } from "@mui/material";
import { keyframes } from 'styled-components';
import { toast } from 'react-toastify';
import 'katex/dist/katex.min.css';
import { InlineMath, BlockMath } from 'react-katex';
// Progress tracking messages
const FAKE_MESSAGES = [
  "Analyzing image structures...",
  "Detecting question patterns...",
  "Optimizing OCR processing...",
  "Verifying answer consistency...",
  "Cross-referencing curriculum...",
  "Generating distractors..."
];
// Animation keyframes
const shimmerKeyframes = keyframes`
  0% {
    background-position: -1000px 0;
  }
  100% {
    background-position: 1000px 0;
  }
`;

const ProgressContainer = styled(motion.div)`
  margin: 2rem 0;
  padding: 2rem;
  background: #2a2a2a;
  border-radius: 15px;
  position: relative;
  overflow: hidden;
`;

const ProgressHeader = styled(motion.div)`
  text-align: center;
  margin-bottom: 1.5rem;
  font-size: 1.2rem;
  color: #2196f3;
`;

const ProgressBarBack = styled.div`
  height: 8px;
  background: #333;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
`;

const ProgressBarFill = styled(motion.div).attrs(props => ({
  style: {
    width: `${Math.min((props.completed / props.total) * 100, 100)}%`
  }
}))`
  height: 100%;
  background: linear-gradient(
    270deg,
    #2196f3 0%,
    #00bcd4 50%,
    #2196f3 100%
  );
  background-size: 200% 100%;
  border-radius: 4px;
  transition: width 0.3s ease;
  animation: shimmer 2s linear infinite;

  @keyframes shimmer {
    0% {
      background-position: 100% 0;
    }
    100% {
      background-position: -100% 0;
    }
  }
`;

const ProgressStats = styled(motion.div)`
  display: flex;
  justify-content: space-between;
  margin-top: 1rem;
  font-size: 0.9rem;
  color: #888;
  
  .progress-fraction {
    font-family: monospace;
    color: #2196f3;
  }
`;

const textGlow = keyframes`
  0% { background-position: -500px 0; }
  100% { background-position: 500px 0; }
`;

const loadingMessageVariants = {
  hidden: {
    opacity: 0,
    y: 20,
    scale: 0.95,
    filter: 'blur(2px) brightness(0.5)'
  },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    filter: 'blur(0px) brightness(1)',
    transition: {
      duration: 0.6,
      ease: [0.22, 1, 0.36, 1]
    }
  },
  exit: {
    opacity: 0,
    y: -20,
    scale: 0.95,
    filter: 'blur(2px) brightness(0.5)',
    transition: {
      duration: 0.4,
      ease: [0.22, 1, 0.36, 1]
    }
  }
};

const LoadingMessage = styled(motion.div)`
  text-align: center;
  font-size: 1.1rem;
  margin: 1.5rem 0;
  color: #fff;
  position: relative;
  overflow: hidden;
  padding: 1.5rem;
  background: rgba(33, 150, 243, 0.08);
  border-radius: 12px;
  box-shadow: 
    0 0 30px rgba(33, 150, 243, 0.1),
    inset 0 0 20px rgba(33, 150, 243, 0.05);
  backdrop-filter: blur(10px);
  letter-spacing: 0.3px;
  font-weight: 400;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 200%;
    height: 100%;
    background: linear-gradient(
      90deg,
      transparent,
      rgba(33, 150, 243, 0.15),
      transparent
    );
    animation: shine 4s linear infinite;
  }

  &::after {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: 12px;
    padding: 1px;
    background: linear-gradient(
      135deg,
      rgba(33, 150, 243, 0.4) 0%,
      transparent 50%,
      rgba(33, 150, 243, 0.4) 100%
    );
    mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    animation: borderRotate 8s linear infinite;
  }

  @keyframes shine {
    0% {
      transform: translateX(-100%) skewX(-15deg);
    }
    50%, 100% {
      transform: translateX(100%) skewX(-15deg);
    }
  }

  @keyframes borderRotate {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }
`;

const rainbowGradient = `
  linear-gradient(
    45deg,
    #FF0000,
    #FF7F00,
    #FFFF00,
    #00FF00,
    #0000FF,
    #4B0082,
    #8B00FF
  )
`;

const glowKeyframes = keyframes`
  0% {
    box-shadow: 0 0 50px rgba(255, 0, 0, 0.5),
                0 0 100px rgba(255, 127, 0, 0.3),
                0 0 150px rgba(255, 255, 0, 0.2);
  }
  33% {
    box-shadow: 0 0 50px rgba(0, 255, 0, 0.5),
                0 0 100px rgba(0, 0, 255, 0.3),
                0 0 150px rgba(75, 0, 130, 0.2);
  }
  66% {
    box-shadow: 0 0 50px rgba(148, 0, 211, 0.5),
                0 0 100px rgba(255, 0, 0, 0.3),
                0 0 150px rgba(255, 127, 0, 0.2);
  }
  100% {
    box-shadow: 0 0 50px rgba(255, 0, 0, 0.5),
                0 0 100px rgba(255, 127, 0, 0.3),
                0 0 150px rgba(255, 255, 0, 0.2);
  }
`;

const gradientKeyframes = keyframes`
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
`;

const borderAnimation = keyframes`
  0% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0% 50%;
  }
`;

const borderGlow = keyframes`
  0% {
    background-position: 0% 0%;
  }
  25% {
    background-position: 100% 0%;
  }
  50% {
    background-position: 100% 100%;
  }
  75% {
    background-position: 0% 100%;
  }
  100% {
    background-position: 0% 0%;
  }
`;

// Skeleton components
const SkeletonLine = styled(motion.div)`
  height: ${props => props.height || '20px'};
  background: #444;
  border-radius: 6px;
  width: ${props => props.width || '100%'};
  position: relative;
  overflow: hidden;
  z-index: 1;
`;

const LoadingSkeleton = styled(motion.div)`
  margin: 2rem 0;
  position: relative;
  border-radius: 15px;
  background: #2a2a2a;
  padding: 3px;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: 15px;
    background: linear-gradient(
      90deg,
      #FF0000, #FF8000, #FFFF00, #00FF00, 
      #00FFFF, #0000FF, #8000FF, #FF0080,
      #FF0000
    );
    -webkit-mask: 
      linear-gradient(#fff 0 0) content-box, 
      linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    background-size: 200% 100%;
    animation: ${borderGlow} 2s linear infinite;
  }
`;

const LoadingContent = styled.div`
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  position: relative;
  z-index: 1;
  background: #2a2a2a;
  border-radius: 12px;
  height: 100%;
`;

const QuestionSkeleton = styled(motion.div)`
  position: relative;
  background: #333;
  border-radius: 12px;
  padding: 3px;
  margin-bottom: 1rem;
  overflow: hidden;

  &::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: 12px;
    background: linear-gradient(
      90deg,
      #FF0000, #FF8000, #FFFF00, #00FF00, 
      #00FFFF, #0000FF, #8000FF, #FF0080,
      #FF0000
    );
    -webkit-mask: 
      linear-gradient(#fff 0 0) content-box, 
      linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    background-size: 200% 100%;
    animation: ${borderGlow} 2s linear infinite;
    animation-delay: ${props => props.index * -0.5}s;
  }

  &::after {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(
      90deg,
      rgba(255, 0, 0, 0.5),
      rgba(255, 128, 0, 0.5),
      rgba(255, 255, 0, 0.5),
      rgba(0, 255, 0, 0.5),
      rgba(0, 255, 255, 0.5),
      rgba(0, 0, 255, 0.5),
      rgba(128, 0, 255, 0.5),
      rgba(255, 0, 0, 0.5)
    );
    filter: blur(8px);
    opacity: 0.15;
    border-radius: 12px;
    z-index: -1;
    background-size: 200% 100%;
    animation: ${borderGlow} 2s linear infinite;
    animation-delay: ${props => props.index * -0.5}s;
  }
`;

const QuestionSkeletonContent = styled.div`
  padding: 1.5rem;
  background: #333;
  border-radius: 10px;
  position: relative;
  height: 100%;
`;

// Enhanced skeleton components
const EnhancedSkeletonLine = styled(motion.div)`
  height: ${props => props.height || '20px'};
  background: #444;
  border-radius: 6px;
  width: ${props => props.width || '100%'};
  position: relative;
  overflow: hidden;
  will-change: transform, opacity;

  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(
      90deg,
      transparent,
      rgba(33, 150, 243, 0.15),
      transparent
    );
    animation: ${shimmerKeyframes} 2s infinite linear;
    transform: translate3d(0, 0, 0);
  }
`;

const UploadProgressBar = styled.div`
  width: 100%;
  height: 6px;
  background-color: #2a2a2a;
  border-radius: 3px;
  overflow: hidden;
  margin-top: 1rem;

  .progress {
    height: 100%;
    background-color: #2196f3;
    transition: width 0.3s ease;
  }
`;

const QuestionGenerationSkeleton = styled(motion.div)`
  margin: 2rem 0;
  position: relative;
  overflow: hidden;
  border-radius: 15px;
  background: #2a2a2a;
  width: 100%;
  will-change: transform, opacity;
  
  &::before {
    content: '';
    position: absolute;
    top: -100%;
    left: -100%;
    right: -100%;
    bottom: -100%;
    background: linear-gradient(
      45deg,
      rgba(33, 150, 243, 0.15),
      rgba(33, 150, 243, 0.05),
      rgba(3, 169, 244, 0.15),
      rgba(0, 188, 212, 0.05),
      rgba(33, 150, 243, 0.15)
    );
    background-size: 200% 200%;
    animation: ${gradientKeyframes} 10s ease infinite;
    filter: blur(30px);
    z-index: 0;
    transform: translate3d(0, 0, 0);
  }
`;

const SkeletonQuestion = styled(motion.div)`
  background: #333;
  border-radius: 12px;
  padding: 1.5rem;
  position: relative;
  overflow: hidden;
  will-change: transform, opacity;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(
      90deg,
      transparent,
      rgba(33, 150, 243, 0.1),
      transparent
    );
    animation: ${shimmerKeyframes} 2s infinite linear;
    transform: translate3d(0, 0, 0);
  }

  &::after {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    right: -50%;
    bottom: -50%;
    background: radial-gradient(
      circle,
      rgba(33, 150, 243, 0.1) 0%,
      transparent 70%
    );
    animation: ${glowKeyframes} 3s ease-in-out infinite;
    z-index: 0;
    filter: blur(20px);
    transform: translate3d(0, 0, 0);
  }
`;

const PageHeader = styled(motion.div)`
  text-align: center;
  margin-bottom: 2rem;
  
  h1 {
    font-size: 2.5rem;
    color: #fff;
    margin: 0;
  }
`;

const Container = styled.div`
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
`;

const TestInfo = styled.div`
  background: #2a2a2a;
  border-radius: 15px;
  padding: 2rem;
  margin-bottom: 2rem;
  color: white;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);

  h2 {
    margin: 0 0 1.5rem 0;
    font-size: 1.8rem;
    color: #2196f3;
    font-weight: 500;
  }

  .details-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1.5rem;
    justify-content: center;
  }

  .detail-item {
    background: #333;
    padding: 1rem;
    border-radius: 10px;
    transition: transform 0.2s ease;

    &:hover {
      transform: translateY(-2px);
    }
  }

  p {
    margin: 0.5rem 0;
    color: #ccc;
    font-size: 1.1rem;
    
    span {
      display: block;
      color: white;
      font-weight: 500;
      margin-top: 0.3rem;
      font-size: 1.2rem;
    }
  }
`;

const ImageUploadSection = styled.div`
  background: #2a2a2a;
  border-radius: 15px;
  padding: 2rem;
  margin-bottom: 2rem;
  color: white;
  text-align: center;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: height 0.3s ease;
  
  h2 {
    margin: 0 0 1.5rem 0;
    font-size: 1.8rem;
    color: #2196f3;
    font-weight: 500;
  }

  .upload-container {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 1rem;
  }

  .content-container {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .button-container {
    display: flex;
    justify-content: center;
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }
`;

const ImageUploadButton = styled(motion.label)`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.8rem;
  background: linear-gradient(135deg, #2196f3 0%, #1976D2 100%);
  color: white;
  border: none;
  border-radius: 12px;
  padding: 1rem 2rem;
  font-size: 1.1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
  }

  input {
    display: none;
  }

  svg {
    font-size: 1.4rem;
  }
`;

const ConfirmDialog = styled(Dialog)`
  .MuiDialog-paper {
    background: #2a2a2a;
    color: white;
    padding: 2rem;
    border-radius: 15px;
    min-width: 300px;
    font-family: 'Roboto', sans-serif;
  }

  h3 {
    margin: 0 0 1.5rem 0;
    color: #2196f3;
    font-size: 1.5rem;
    text-align: center;
  }

  .dialog-buttons {
    display: flex;
    gap: 1rem;
    margin-top: 2rem;
    justify-content: center;
  }
`;

const DialogButton = styled(motion.button)`
  padding: 0.8rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  font-weight: 500;
  min-width: 100px;

  &.confirm {
    background: #4CAF50;
    color: white;
    &:hover {
      background: #45a049;
    }
  }

  &.cancel {
    background: #f44336;
    color: white;
    &:hover {
      background: #d32f2f;
    }
  }
`;

const QuestionCard = styled(motion.div)`
  background: ${props => {
    if (props.isNew) {
      return props.hasAnswer ? '#423c1c' : '#422222';  // Yellow tint for answered, red tint for unanswered
    }
    return '#2a2a2a';  // Default dark background
  }};
  border-radius: 15px;
  padding: 2rem;
  margin-bottom: 1.5rem;
  position: relative;
  color: white;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transition: box-shadow 0.3s ease, background-color 0.3s ease;
  border: 2px solid ${props => {
    if (props.isNew) {
      return props.hasAnswer ? 'rgba(255, 255, 0, 0.2)' : 'rgba(255, 0, 0, 0.2)';
    }
    return 'transparent';
  }};

  &:hover {
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
  }

  h3 {
    margin-top: 0;
    margin-bottom: 1.5rem;
    color: ${props => props.isNew ? (props.hasAnswer ? '#ffd700' : '#ff4444') : '#2196f3'};
  }

  .question-number {
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
  }

  .options-container {
    display: grid;
    gap: 1rem;
    margin-top: 1rem;
  }

  .option {
    background: #333;
    padding: 1rem;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 0.5rem;

    &:hover {
      background: #444;
      transform: translateX(5px);
    }

    &.selected {
      background: #4CAF50;
      color: white;
      transform: translateX(10px);
    }
  }
`;

const EditButton = styled(motion.button)`
  position: absolute;
  top: 1rem;
  right: 4rem;
  background: transparent;
  border: none;
  color: #4CAF50;
  cursor: pointer;
  font-size: 1.2rem;
  
  &:hover {
    color: #45a049;
  }
`;

const DeleteButton = styled(motion.button)`
  position: absolute;
  top: 1rem;
  right: 1rem;
  background: transparent;
  border: none;
  color: #f44336;
  cursor: pointer;
  font-size: 1.2rem;
  
  &:hover {
    color: #d32f2f;
  }
`;

const AddQuestionButton = styled(motion.button)`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  background: #2196f3;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-size: 1rem;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  
  &:hover {
    background: #1976D2;
  }

  svg {
    flex-shrink: 0;
  }
`;

const CreateTestButton = styled(motion.button)`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  background: #2196f3;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-size: 1rem;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  
  &:hover {
    background: #1976D2;
  }
`;

const QuestionInput = styled.textarea`
  width: 100%;
  padding: 1rem;
  margin-bottom: 1rem;
  background: #333;
  border: 1px solid #444;
  border-radius: 8px;
  color: white;
  font-size: 1rem;
  min-height: 100px;
  resize: vertical;
  transition: border-color 0.3s ease;

  &:focus {
    border-color: #2196f3;
    outline: none;
  }
`;

const OptionInput = styled.input`
  width: 100%;
  padding: 0.75rem;
  background: #333;
  border: 1px solid #444;
  border-radius: 8px;
  color: white;
  font-size: 0.95rem;
  transition: all 0.3s ease;

  &:focus {
    border-color: #2196f3;
    outline: none;
    background: #3a3a3a;
  }
`;

const OptionContainer = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
  
  label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    min-width: 30px;
    color: #ccc;
  }
`;

const ButtonsContainer = styled.div`
  display: flex;
  gap: 1rem;
  margin: 2rem auto 2rem;
  max-width: 600px;
  width: 100%;
  
  > * {
    flex: 1;
    height: 48px;
    min-width: 0;
  }
`;

const LoadingContainer = styled(motion.div)`
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
  padding-bottom: 4rem;
`;

const LoadingHeader = styled(motion.div)`
  text-align: center;
  margin-bottom: 2rem;
`;

const LoadingCard = styled(motion.div)`
  background: #2a2a2a;
  border-radius: 15px;
  padding: 2rem;
  margin-bottom: 1.5rem;
  position: relative;
`;

const ImageLoadingSkeleton = styled(motion.div)`
  margin: 1rem 0;
  position: relative;
  overflow: hidden;
  border-radius: 15px;
  background: #2a2a2a;
  width: 100%;
  
  &::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    right: -50%;
    bottom: -50%;
    background: linear-gradient(
      45deg,
      rgba(33, 150, 243, 0.15),
      rgba(33, 150, 243, 0.05),
      rgba(3, 169, 244, 0.15),
      rgba(0, 188, 212, 0.05),
      rgba(33, 150, 243, 0.15)
    );
    background-size: 200% 200%;
    animation: ${gradientKeyframes} 10s ease infinite;
    z-index: 0;
    filter: blur(20px);
    opacity: 0.15;
  }
`;

const SkeletonContent = styled.div`
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
  width: 100%;
`;

const ImagePreviewContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
  width: 100%;
  padding: 1rem;
`;

const ImagePreview = styled(motion.div)`
  position: relative;
  aspect-ratio: 16/9;
  background: #333;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  width: 100%;
  transform-origin: center;
  will-change: transform, opacity;
  
  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .delete-button {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    background: rgba(244, 67, 54, 0.9);
    color: white;
    border: none;
    border-radius: 50%;
    width: 30px;
    height: 30px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s ease;
    opacity: 0.8;
    transform: scale(1);
    will-change: transform;

    &:hover {
      background: #f44336;
      transform: scale(1.1);
      opacity: 1;
    }

    @media (min-width: 768px) {
      opacity: 0;
      transform: scale(0.8);
    }
  }

  @media (min-width: 768px) {
    &:hover .delete-button {
      opacity: 1;
      transform: scale(1);
    }
  }
`;

const ImageAnalysis = styled(motion.div)`
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 0.5rem;
  font-size: 0.8rem;
  transform: translateY(100%);
  transition: transform 0.3s ease;

  .analysis-content {
    max-height: 100px;
    overflow-y: auto;
    padding: 0.5rem;
  }

  ${ImagePreview}:hover & {
    transform: translateY(0);
  }
`;

const GenerateButton = styled(motion.button)`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.8rem;
  background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
  color: white;
  border: none;
  border-radius: 12px;
  padding: 1rem 2rem;
  font-size: 1.1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  margin-top: 1rem;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.2);
  }

  &:disabled {
    background: #666;
    cursor: not-allowed;
    transform: none;
    box-shadow: none;
  }
`;

const ImagePopup = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 2rem;

  .close-button {
    position: absolute;
    top: 1rem;
    right: 1rem;
    background: rgba(255, 255, 255, 0.2);
    border: none;
    color: white;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.2s ease;
    font-size: 1.5rem;

    &:hover {
      background: rgba(255, 255, 255, 0.3);
      transform: scale(1.1);
    }
  }

  .image-container {
    max-width: 90%;
    max-height: 90vh;
    display: flex;
    align-items: center;
    justify-content: center;
    
    img {
      max-width: 100%;
      max-height: 90vh;
      object-fit: contain;
      border-radius: 8px;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
    }
  }
`;

const NoQuestionsDialog = styled(Dialog)`
  .MuiDialog-paper {
    background: #2a2a2a;
    color: white;
    padding: 2rem;
    border-radius: 15px;
    min-width: 350px;
    max-width: 500px;
    font-family: 'Roboto', sans-serif;
  }

  .dialog-content {
    text-align: center;
  }

  .dialog-icon {
    font-size: 4rem;
    color: #2196f3;
    margin-bottom: 1rem;
  }

  h3 {
    margin: 0 0 1rem 0;
    color: #2196f3;
    font-size: 1.5rem;
  }

  p {
    color: #ccc;
    margin-bottom: 1.5rem;
    line-height: 1.5;
  }

  .possible-reasons {
    text-align: left;
    background: #333;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;

    h4 {
      color: #2196f3;
      margin: 0 0 0.5rem 0;
      font-size: 1.1rem;
    }

    ul {
      margin: 0;
      padding-left: 1.5rem;
      color: #ccc;

      li {
        margin: 0.5rem 0;
      }
    }
  }

  .dialog-buttons {
    display: flex;
    justify-content: center;
    margin-top: 1.5rem;
  }
`;

const UnderstandButton = styled(motion.button)`
  background: #2196f3;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 0.8rem 2rem;
  font-size: 1rem;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s ease;

  &:hover {
    background: #1976D2;
  }
`;

const PrivacyNoticeDialog = styled(Dialog)`
  .MuiDialog-paper {
    background: #2a2a2a;
    color: white;
    padding: 2rem;
    border-radius: 15px;
    min-width: 400px;
    max-width: 600px;
    font-family: 'Roboto', sans-serif;
  }

  .dialog-content {
    text-align: center;
  }

  .privacy-icon {
    font-size: 4rem;
    color: #ff4444;
    margin-bottom: 1rem;
  }

  h3 {
    margin: 0 0 1rem 0;
    color: #ff4444;
    font-size: 1.8rem;
    font-weight: 600;
  }

  .privacy-text {
    color: #eee;
    margin: 1.5rem 0;
    line-height: 1.6;
    text-align: left;
    background: rgba(255, 68, 68, 0.1);
    padding: 1.5rem;
    border-radius: 8px;
    border: 1px solid rgba(255, 68, 68, 0.2);

    p {
      margin: 0.8rem 0;
      &:first-child {
        margin-top: 0;
      }
      &:last-child {
        margin-bottom: 0;
      }
    }
  }

  .dialog-buttons {
    display: flex;
    justify-content: center;
    margin-top: 2rem;
  }
`;

const AgreeButton = styled(motion.button)`
  background: #ff4444;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 1rem 3rem;
  font-size: 1.1rem;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s ease;
  box-shadow: 0 4px 6px rgba(255, 68, 68, 0.2);

  &:hover {
    background: #ff3333;
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

// Function to process text and render LaTeX
const renderLatexText = (text) => {
  if (!text) return null;
  
  // Split text by LaTeX delimiters ($)
  const parts = text.split(/(\$[^\$]+\$)/g);
  
  return parts.map((part, index) => {
    if (part.startsWith('$') && part.endsWith('$')) {
      // Remove $ delimiters and render as LaTeX
      const latex = part.slice(1, -1);
      try {
        return <InlineMath key={index} math={latex} />;
      } catch (error) {
        console.error('LaTeX parsing error:', error);
        return part;
      }
    }
    return part;
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

const CreateTestSkeleton = () => (
  <LoadingContainer
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    exit={{ opacity: 0 }}
  >
    <LoadingHeader>
      <Skeleton 
        variant="text" 
        width={200} 
        height={50} 
        style={{ 
          margin: '0 auto',
          background: 'rgba(255, 255, 255, 0.1)' 
        }} 
      />
    </LoadingHeader>

    <LoadingCard>
      <Skeleton 
        variant="text" 
        width={150} 
        height={40} 
        style={{ background: 'rgba(255, 255, 255, 0.1)', marginBottom: '1.5rem' }} 
      />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1.5rem' }}>
        {[1, 2, 3].map((n) => (
          <div key={n} style={{ background: '#333', padding: '1rem', borderRadius: '10px' }}>
            <Skeleton 
              variant="text" 
              width={80} 
              height={24} 
              style={{ background: 'rgba(255, 255, 255, 0.1)' }} 
            />
            <Skeleton 
              variant="text" 
              width={120} 
              height={30} 
              style={{ background: 'rgba(255, 255, 255, 0.1)', marginTop: '0.5rem' }} 
            />
          </div>
        ))}
      </div>
    </LoadingCard>

    {[1, 2, 3].map((n) => (
      <LoadingCard key={n}>
        <Skeleton 
          variant="text" 
          width="100%" 
          height={60} 
          style={{ background: 'rgba(255, 255, 255, 0.1)', marginBottom: '1.5rem' }} 
        />
        {[1, 2, 3, 4].map((o) => (
          <Skeleton 
            key={o}
            variant="rectangular" 
            width="100%" 
            height={50} 
            style={{ 
              background: 'rgba(255, 255, 255, 0.1)', 
              marginBottom: '1rem',
              borderRadius: '8px'
            }} 
          />
        ))}
      </LoadingCard>
    ))}

    <ButtonsContainer>
      <Skeleton 
        variant="rectangular" 
        width="100%" 
        height={48} 
        style={{ 
          background: 'rgba(255, 255, 255, 0.1)', 
          borderRadius: '8px'
        }} 
      />
      <Skeleton 
        variant="rectangular" 
        width="100%" 
        height={48} 
        style={{ 
          background: 'rgba(255, 255, 255, 0.1)', 
          borderRadius: '8px'
        }} 
      />
    </ButtonsContainer>
  </LoadingContainer>
);

const CreateTest = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [questions, setQuestions] = useState([]);
  const [isLoading, setIsLoading] = useState(!location.state?.generatedTest);
  const [openConfirm, setOpenConfirm] = useState(false);
  const [showPrivacyNotice, setShowPrivacyNotice] = useState(false);
  const [hasAgreedToPrivacy, setHasAgreedToPrivacy] = useState(false);
  const [pendingUploadEvent, setPendingUploadEvent] = useState(null);
  const [progress, setProgress] = useState(0);
  const progressInterval = useRef(null);
  const startTimeRef = useRef(null);
  const lastProgressRef = useRef(0);
  const [uploadedImages, setUploadedImages] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  const [showNoQuestionsDialog, setShowNoQuestionsDialog] = useState(false);
  const [currentJobId, setCurrentJobId] = useState(null);
  const [jobProgress, setJobProgress] = useState({ total: 0, completed: 0 });
  const [loadingMessages, setLoadingMessages] = useState([]);
  const [showProgressBar, setShowProgressBar] = useState(false);
  const [newQuestionIds, setNewQuestionIds] = useState(new Set());
  const [uploadProgress, setUploadProgress] = useState(0);

  useEffect(() => {
    if (location.state?.generatedTest) {
      setQuestions(location.state.generatedTest.questions.map(q => ({
        ...q,
        isEditing: false
      })));
      setIsLoading(false);
    }
  }, [location]);

  useEffect(() => {
    if (!location.state?.generatedTest) {
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

      return () => {
        if (progressInterval.current) {
          clearInterval(progressInterval.current);
        }
      };
    }
  }, []);

  const handleEdit = (index) => {
    setQuestions(prev => prev.map((q, i) => 
      i === index ? { ...q, isEditing: !q.isEditing } : q
    ));
  };

  const handleDelete = (index) => {
    setQuestions(prev => prev.filter((_, i) => i !== index));
  };

  const handleQuestionChange = (index, field, value, optionKey) => {
    setQuestions(prev => prev.map((q, i) => {
      if (i !== index) return q;
      
      if (field === 'options') {
        return {
          ...q,
          options: { ...q.options, [optionKey]: value }
        };
      }
      
      return { ...q, [field]: value };
    }));
  };

  const handleAnswerChange = (index, selectedOption) => {
    setQuestions(prev => prev.map((q, i) => 
      i === index ? { ...q, answer: selectedOption } : q
    ));
  };

  const handleAddQuestion = () => {
    const newQuestion = {
      question: '',
      options: { a: '', b: '', c: '', d: '' },
      answer: '',
      isEditing: true,
      id: Date.now()  // Add unique id for new questions
    };
    setQuestions(prev => [...prev, newQuestion]);
    setNewQuestionIds(prev => new Set(prev).add(newQuestion.id));
  };

  const handleCreateTest = async () => {
    setIsLoading(true);
    setProgress(0);
    startTimeRef.current = Date.now();
    lastProgressRef.current = 0;

    const updateProgress = () => {
      const elapsedTime = Date.now() - startTimeRef.current;
      const newProgress = Math.min((elapsedTime / 2000) * 25, 25);

      if (newProgress > lastProgressRef.current) {
        setProgress(newProgress);
        lastProgressRef.current = newProgress;
      }
    };

    progressInterval.current = setInterval(updateProgress, 5);
    
    setOpenConfirm(true);
  };

  const handleConfirmCreate = async () => {
    const updateProgress = () => {
      const elapsedTime = Date.now() - startTimeRef.current;
      const newProgress = Math.min(25 + ((elapsedTime / 1000) * 75), 100);

      if (newProgress > lastProgressRef.current) {
        setProgress(newProgress);
        lastProgressRef.current = newProgress;
      }
    };

    try {
      await api.createTest({
        subject: location.state.generatedTest.subject,
        lessons: location.state.generatedTest.lessons,
        questions: questions.map(({ isEditing, ...q }) => q),
        class10: location.state.generatedTest.class10
      });
      
      clearInterval(progressInterval.current);
      setProgress(100);
      
      setTimeout(() => {
        navigate('/test-series');
      }, 100);
    } catch (error) {
      console.error('Error:', error);
      clearInterval(progressInterval.current);
      setIsLoading(false);
      setOpenConfirm(false);
    }
  };

  const handleCancelCreate = () => {
    clearInterval(progressInterval.current);
    setIsLoading(false);
    setOpenConfirm(false);
    setProgress(0);
  };

  const handleImageUpload = async (event) => {
    if (!hasAgreedToPrivacy) {
      // Convert FileList to Array and store it to ensure we keep the actual file references
      if (event?.target?.files) {
        const filesArray = Array.from(event.target.files);
        setPendingUploadEvent(filesArray);
        setShowPrivacyNotice(true);
        // Reset file input
        event.target.value = '';
      }
      return;
    }

    // Use either the event.target.files or the pendingUploadEvent
    const files = event?.target?.files ? Array.from(event.target.files) : pendingUploadEvent;
    
    if (files && files.length > 0) {
      setIsUploading(true);
      setUploadProgress(0);
      const formData = new FormData();
      
      // Validate file sizes and types before upload
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        if (file.size > 16 * 1024 * 1024) { // 16MB limit
          toast.error(`File ${file.name} is too large. Maximum size is 16MB.`);
          setIsUploading(false);
          return;
        }
        if (!file.type.startsWith('image/')) {
          toast.error(`File ${file.name} is not an image.`);
          setIsUploading(false);
          return;
        }
        formData.append(`image_${i}`, file);
      }

      try {
        const response = await api.uploadImages(formData, (progress) => {
          setUploadProgress(progress);
        });
        
        if (response?.files?.length > 0) {
          const newImages = await Promise.all(response.files.map(async filename => {
            const imageResponse = await api.getUploadedImage(filename);
            const imageBlob = await imageResponse.blob();
            return {
              url: URL.createObjectURL(imageBlob),
              filename
            };
          }));

          setUploadedImages(prev => [...prev, ...newImages]);
          toast.success('Images uploaded successfully!');
        } else {
          throw new Error('No files were uploaded');
        }
      } catch (error) {
        console.error('Error uploading images:', error);
        toast.error(error.message || 'Failed to upload images. Please try again.');
      } finally {
        setIsUploading(false);
        setUploadProgress(0);
        setPendingUploadEvent(null);
        // Reset file input if it exists
        if (event?.target) {
          event.target.value = '';
        }
      }
    }
  };

  const handleDeleteImage = (index) => {
    setUploadedImages(prev => prev.filter((_, i) => i !== index));
  };

  const handleGenerateQuestions = async () => {
    if (uploadedImages.length === 0) {
      toast.error('Please upload at least one image first');
      return;
    }

    setIsGenerating(true);
    setShowProgressBar(false);
    setJobProgress({ total: 0, completed: 0 });
    setLoadingMessages([FAKE_MESSAGES[Math.floor(Math.random() * FAKE_MESSAGES.length)]]);

    // Initialize message rotation
    let messageIndex = 0;
    const messageInterval = setInterval(() => {
      setLoadingMessages([FAKE_MESSAGES[messageIndex]]);
      messageIndex = (messageIndex + 1) % FAKE_MESSAGES.length;
    }, 4000);

    try {
      const filenames = uploadedImages.map(img => img.filename);
      const questions = await api.generateFromImages(filenames, {
        onProgress: (progress) => {
          if (progress.total > 0) {
            setShowProgressBar(true);
            setJobProgress(progress);
          }
        },
        onMessage: (message) => {
          clearInterval(messageInterval);
          setLoadingMessages([message]);
        }
      });

      clearInterval(messageInterval);

      if (!Array.isArray(questions) || questions.length === 0) {
        setShowNoQuestionsDialog(true);
        return;
      }

      // Format questions with unique IDs
      const formattedQuestions = questions.map(q => ({
        ...q,
        isEditing: false,
        id: Date.now() + Math.random()
      }));

      setQuestions(formattedQuestions);
      setNewQuestionIds(new Set(formattedQuestions.map(q => q.id)));
      toast.success('Questions generated successfully!');

    } catch (error) {
      console.error('Error generating questions:', error);
      clearInterval(messageInterval);
      
      if (error.message === 'No questions could be extracted from the images') {
        setShowNoQuestionsDialog(true);
      } else {
        toast.error(error.message || 'Failed to generate questions. Please try again.');
      }
    } finally {
      setIsGenerating(false);
    }
  };

  const handleImageClick = (image) => {
    setSelectedImage(image);
  };

  const handleClosePopup = () => {
    setSelectedImage(null);
  };

  const handleCloseNoQuestionsDialog = () => {
    setShowNoQuestionsDialog(false);
  };

  const handleAgreeToPrivacy = () => {
    setHasAgreedToPrivacy(true);
    setShowPrivacyNotice(false);
    
    // Get the current file list
    const files = pendingUploadEvent;
    
    if (files && files.length > 0) {
      // Create a new FormData for the API call
      const formData = new FormData();
      setIsUploading(true);
      
      // Add each file to the form data
      let hasValidFiles = true;
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        // Validate file size
        if (file.size > 16 * 1024 * 1024) {
          toast.error(`File ${file.name} is too large. Maximum size is 16MB.`);
          setIsUploading(false);
          hasValidFiles = false;
          break;
        }
        
        // Validate file type
        if (!file.type.startsWith('image/')) {
          toast.error(`File ${file.name} is not an image.`);
          setIsUploading(false);
          hasValidFiles = false;
          break;
        }
        
        // Add valid file to form data
        formData.append(`image_${i}`, file);
      }
      
      // If all files are valid, proceed with upload
      if (hasValidFiles) {
        api.uploadImages(formData)
          .then(response => {
            if (response?.files?.length > 0) {
              return Promise.all(response.files.map(async filename => {
                const imageResponse = await api.getUploadedImage(filename);
                const imageBlob = await imageResponse.blob();
                return {
                  url: URL.createObjectURL(imageBlob),
                  filename
                };
              }));
            } else {
              throw new Error('No files were uploaded');
            }
          })
          .then(newImages => {
            setUploadedImages(prev => [...prev, ...newImages]);
            toast.success('Images uploaded successfully!');
          })
          .catch(error => {
            console.error('Error uploading images:', error);
            toast.error(error.message || 'Failed to upload images. Please try again.');
          })
          .finally(() => {
            setIsUploading(false);
            setPendingUploadEvent(null);
          });
      } else {
        setPendingUploadEvent(null);
      }
    }
  };

  return (
    <>
      {isLoading ? (
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          style={{ 
            height: '100vh', 
            width: '100%',
            position: 'fixed',
            top: 0,
            left: 0,
            background: '#1a1a1a'
          }}
        >
          <ExamSkeletonLoading progress={progress} />
        </motion.div>
      ) : (
        <Container>
          <PageHeader
            initial={{ y: -20 }}
            animate={{ y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h1>Create Test</h1>
          </PageHeader>
          
          <TestInfo>
            <h2>Test Details</h2>
            <div className="details-grid">
              <div className="detail-item">
                <p>Subject<span>{location.state?.generatedTest?.subject}</span></p>
              </div>
              <div className="detail-item">
                <p>Total Questions<span>{questions.length}</span></p>
              </div>
              <div className="detail-item">
                <p>Lessons<span>{location.state?.generatedTest?.lessons.join(', ')}</span></p>
              </div>
            </div>
          </TestInfo>

          <ImageUploadSection className="image-upload-section">
            <h2>Upload Images</h2>
            <div className="content-container">
              <div className="upload-container">
                <ImageUploadButton
                  as={motion.label}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <IoMdAdd />
                  Add Images
                  <input
                    type="file"
                    accept="image/*"
                    multiple
                    onChange={handleImageUpload}
                  />
                </ImageUploadButton>
              </div>

              {(uploadedImages.length > 0 || isUploading) && (
                <>
                  <ImagePreviewContainer>
                    <AnimatePresence mode="popLayout">
                      {uploadedImages.map((image, index) => (
                        <ImagePreview
                          key={image.filename}
                          initial={{ opacity: 0, scale: 0.9, height: 0 }}
                          animate={{ 
                            opacity: 1, 
                            scale: 1,
                            height: 'auto',
                            transition: {
                              height: {
                                type: "spring",
                                stiffness: 500,
                                damping: 30,
                                mass: 1
                              },
                              opacity: {
                                duration: 0.2
                              },
                              scale: {
                                type: "spring",
                                stiffness: 150,
                                damping: 15,
                                mass: 0.1
                              }
                            }
                          }}
                          exit={{ 
                            opacity: 0, 
                            scale: 0.9,
                            height: 0,
                            transition: {
                              height: {
                                duration: 0.2,
                                ease: "easeInOut"
                              },
                              opacity: {
                                duration: 0.15
                              },
                              scale: {
                                duration: 0.15
                              }
                            }
                          }}
                          onClick={() => handleImageClick(image)}
                          style={{ cursor: 'pointer' }}
                        >
                          <img src={image.url} alt={`Uploaded ${index + 1}`} />
                          <button
                            className="delete-button"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteImage(index);
                            }}
                          >
                            <FaTrash />
                          </button>
                        </ImagePreview>
                      ))}
                    </AnimatePresence>
                  </ImagePreviewContainer>

                  <AnimatePresence>
                    {isUploading && (
                      <ImageLoadingSkeleton
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ 
                          opacity: 1, 
                          height: 200,
                          transition: {
                            duration: 0.3,
                            ease: "easeOut"
                          }
                        }}
                        exit={{ 
                          opacity: 0, 
                          height: 0,
                          transition: {
                            duration: 0.2,
                            ease: "easeIn"
                          }
                        }}
                      >
                        <SkeletonContent>
                          <SkeletonLine height="40px" width="60%" />
                          <SkeletonLine height="20px" width="80%" />
                          <SkeletonLine height="20px" width="70%" />
                          <SkeletonLine height="20px" width="75%" />
                          <UploadProgressBar>
                            <div 
                              className="progress" 
                              style={{ width: `${uploadProgress}%` }} 
                            />
                          </UploadProgressBar>
                          <div style={{ textAlign: 'center', marginTop: '0.5rem', color: '#fff' }}>
                            {uploadProgress.toFixed(0)}% Uploaded
                          </div>
                        </SkeletonContent>
                      </ImageLoadingSkeleton>
                    )}
                  </AnimatePresence>

                  {uploadedImages.length > 0 && (
                    <motion.div 
                      className="button-container"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                    >
                      <GenerateButton
                        onClick={handleGenerateQuestions}
                        disabled={isGenerating}
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                      >
                        {isGenerating ? 'Generating...' : 'Generate Questions'}
                      </GenerateButton>
                    </motion.div>
                  )}
                </>
              )}
            </div>
          </ImageUploadSection>

          <AnimatePresence>
            {isGenerating && (
              <LoadingSkeleton
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.5 }}
              >
                <LoadingContent>
                  <ProgressContainer>
                    <ProgressHeader
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ duration: 0.3 }}
                    >
                      {showProgressBar ? "Generating Questions" : "Analyzing Images"}
                    </ProgressHeader>

                    <AnimatePresence mode="wait">
                      {!showProgressBar && loadingMessages.map((message) => (
                        <LoadingMessage
                          key={message}
                          variants={loadingMessageVariants}
                          initial="hidden"
                          animate={{
                            ...loadingMessageVariants.visible,
                            y: [0, -5, 0],
                            transition: {
                              y: {
                                repeat: Infinity,
                                duration: 2,
                                ease: "easeInOut"
                              }
                            }
                          }}
                          exit="exit"
                        >
                          {message}
                        </LoadingMessage>
                      ))}
                    </AnimatePresence>

                    <AnimatePresence>
                      {showProgressBar && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          transition={{ duration: 0.3 }}
                        >
                          <ProgressBarBack>
                            <ProgressBarFill completed={jobProgress.completed} total={jobProgress.total} />
                          </ProgressBarBack>
                          <ProgressStats
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.2 }}
                          >
                            <span>
                              <span className="progress-fraction">
                                {jobProgress.completed}/{jobProgress.total}
                              </span> questions processed
                            </span>
                            <span>{Math.round((jobProgress.completed / jobProgress.total) * 100)}%</span>
                          </ProgressStats>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </ProgressContainer>
                  {[1, 2, 3].map((_, index) => (
                    <QuestionSkeleton
                      key={index}
                      index={index}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{
                        duration: 0.5,
                        delay: index * 0.2,
                        ease: [0.4, 0, 0.2, 1]
                      }}
                    >
                      <QuestionSkeletonContent>
                        <SkeletonLine 
                          height="24px" 
                          width="80%" 
                          initial={{ opacity: 0, scaleX: 0.8 }}
                          animate={{ opacity: 1, scaleX: 1 }}
                          transition={{ duration: 0.3, delay: index * 0.2 + 0.2 }}
                        />
                        <div style={{ marginTop: '1.5rem', display: 'grid', gap: '1rem' }}>
                          {[1, 2, 3, 4].map((_, optionIndex) => (
                            <SkeletonLine
                              key={optionIndex}
                              height="20px"
                              width={`${85 - optionIndex * 5}%`}
                              initial={{ opacity: 0, scaleX: 0.8 }}
                              animate={{ opacity: 1, scaleX: 1 }}
                              transition={{
                                duration: 0.3,
                                delay: index * 0.2 + optionIndex * 0.1 + 0.3
                              }}
                            />
                          ))}
                        </div>
                      </QuestionSkeletonContent>
                    </QuestionSkeleton>
                  ))}
                </LoadingContent>
              </LoadingSkeleton>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {questions.map((question, index) => (
              <QuestionCard
                key={question.id || index}
                variants={questionCardVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                custom={index}
                isNew={newQuestionIds.has(question.id)}
                hasAnswer={!!question.answer}
              >
                <div className="question-number">{index + 1}</div>
                <EditButton
                  onClick={() => handleEdit(index)}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                >
                  <FaEdit />
                </EditButton>
                <DeleteButton
                  onClick={() => handleDelete(index)}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                >
                  <FaTrash />
                </DeleteButton>

                {question.isEditing ? (
                  <>
                    <QuestionInput
                      value={question.question}
                      onChange={(e) => handleQuestionChange(index, 'question', e.target.value)}
                      placeholder="Enter your question here... (Use markdown tables with | for columns)"
                    />
                    {Object.entries(question.options).map(([key, value]) => (
                      <OptionContainer key={key}>
                        <label>
                          <input
                            type="radio"
                            name={`answer-${index}`}
                            value={key}
                            checked={question.answer === key}
                            onChange={() => handleAnswerChange(index, key)}
                          />
                          {key.toUpperCase()}
                        </label>
                        <OptionInput
                          value={value}
                          onChange={(e) => handleQuestionChange(index, 'options', e.target.value, key)}
                          placeholder={`Option ${key.toUpperCase()}`}
                        />
                      </OptionContainer>
                    ))}
                  </>
                ) : (
                  <>
                    {(() => {
                      const { text, tables } = parseMarkdownTable(question.question);
                      return (
                        <>
                          <h3>{renderLatexText(text)}</h3>
                          {tables.map((table, tableIndex) => renderTable(table))}
                        </>
                      );
                    })()}
                    <div className="options-container">
                      {Object.entries(question.options).map(([key, value]) => (
                        <motion.div
                          key={key}
                          className={`option ${question.answer === key ? 'selected' : ''}`}
                          onClick={() => handleAnswerChange(index, key)}
                          whileHover={{ x: 5 }}
                          whileTap={{ scale: 0.98 }}
                        >
                          <strong>{key.toUpperCase()}.</strong> {renderLatexText(value)}
                        </motion.div>
                      ))}
                    </div>
                  </>
                )}
              </QuestionCard>
            ))}
          </AnimatePresence>

          <ButtonsContainer>
            <AddQuestionButton
              onClick={handleAddQuestion}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
            >
              <IoMdAdd />
              Add Question
            </AddQuestionButton>

            <CreateTestButton
              onClick={handleCreateTest}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              disabled={questions.length === 0}
            >
              Create Test
            </CreateTestButton>
          </ButtonsContainer>
        </Container>
      )}

      <ConfirmDialog
        open={openConfirm}
        onClose={handleCancelCreate}
        style={{ zIndex: 9999 }}
      >
        <h3>Create Test?</h3>
        <p>Are you sure you want to create this test? This action <strong>cannot</strong> be undone.</p>
        <div className="dialog-buttons">
          <DialogButton
            className="cancel"
            onClick={handleCancelCreate}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Cancel
          </DialogButton>
          <DialogButton
            className="confirm"
            onClick={() => {
              setOpenConfirm(false);
              handleConfirmCreate();
            }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Create
          </DialogButton>
        </div>
      </ConfirmDialog>

      <NoQuestionsDialog
        open={showNoQuestionsDialog}
        onClose={handleCloseNoQuestionsDialog}
      >
        <div className="dialog-content">
          <div className="dialog-icon">⚠️</div>
          <h3>No Questions Detected</h3>
          <p>We couldn't detect any questions from the uploaded images.</p>
          
          <div className="possible-reasons">
            <h4>This might be because:</h4>
            <ul>
              <li>The image doesn't contain any questions</li>
              <li>The image quality is too low or unclear</li>
              <li>The text in the image is not properly visible</li>
              <li>The questions are not in a recognizable format</li>
            </ul>
          </div>

          <p>Please check your images and try again with clear, well-lit photos of questions.</p>
          
          <div className="dialog-buttons">
            <UnderstandButton
              onClick={handleCloseNoQuestionsDialog}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              I Understand
            </UnderstandButton>
          </div>
        </div>
      </NoQuestionsDialog>

      <AnimatePresence>
        {selectedImage && (
          <ImagePopup
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={handleClosePopup}
          >
            <div className="image-container" onClick={(e) => e.stopPropagation()}>
              <img src={selectedImage.url} alt="Selected" />
              <button className="close-button" onClick={handleClosePopup}>×</button>
            </div>
          </ImagePopup>
        )}
      </AnimatePresence>

      <PrivacyNoticeDialog
        open={showPrivacyNotice}
        onClose={() => {}}
      >
        <div className="dialog-content">
          <div className="privacy-icon">🔒</div>
          <h3>Privacy Notice</h3>
          <div className="privacy-text">
            <p>Before proceeding with image uploads, please carefully read and acknowledge the following privacy terms:</p>
            <p>1. Any images you upload will be stored on AcePlus servers located in Romania.</p>
            <p>2. Do not upload any images containing sensitive, private, or confidential information that you wish to keep private.</p>
            <p>3. The creator, Ayush Pandey, maintains complete rights and authority to access, test, check, and verify any uploaded images for the purpose of product improvement and quality assurance.</p>
            <p>4. By clicking "I Agree", you acknowledge that you understand and accept these terms regarding the handling and storage of your uploaded images.</p>
          </div>
          <div className="dialog-buttons">
            <AgreeButton
              onClick={handleAgreeToPrivacy}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              I Agree
            </AgreeButton>
          </div>
        </div>
      </PrivacyNoticeDialog>
    </>
  );
};

export default CreateTest;