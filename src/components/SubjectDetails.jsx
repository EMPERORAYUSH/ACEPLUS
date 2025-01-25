import React, { useState, useEffect } from 'react';
import { api } from '../utils/api';
import { motion } from 'framer-motion';

const SkeletonCard = () => (
  <div className="subject-detail-card skeleton">
    <div className="skeleton-text"></div>
    <div className="skeleton-text"></div>
  </div>
);

const SubjectDetails = ({ subject }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [details, setDetails] = useState(null);

  useEffect(() => {
    const fetchDetails = async () => {
      try {
        const data = await api.getSubjectStats(subject);
        setDetails(data);
      } catch (error) {
        console.error('Error fetching subject details:', error);
      } finally {
        setIsLoading(false);
      }
    };
    fetchDetails();
  }, [subject]);

  const detailCards = [
    { title: 'Exams Given', value: details?.attempted, icon: '📚', color: '#7FB069' },
    { title: 'Questions Attempted', value: details?.marksAttempted, icon: '✏️', color: '#64B5F6' },
    { title: 'Marks Gained', value: details?.marksGained, icon: '🎯', color: '#FFD54F' },
    { title: 'Average Percentage', value: details?.avgPercentage ? `${details.avgPercentage.toFixed(2)}%` : 'N/A', icon: '📊', color: '#BA68C8' },
    { title: 'Highest Percentage in Exam', value: details?.highestMark ? details.highestMark.toFixed(2) : 'N/A', icon: '💪', color: '#FF8A65' },
    { title: 'Lowest Percentage in Exam', value: details?.lowestMark ? details.lowestMark.toFixed(2) : 'N/A', icon: '🔍', color: '#A1887F' },
  ]
  return (
    <motion.div 
      className="subject-details-container"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.3 }}
    >
      <h1 className="subject-title">{subject.charAt(0).toUpperCase() + subject.slice(1)} Analysis</h1>
      <div className="subject-details-grid">
        {isLoading
          ? Array(6).fill(null).map((_, index) => <SkeletonCard key={index} />)
          : detailCards.map((card, index) => (
              <div key={index} className="subject-detail-card" style={{ '--card-color': card.color }}>
                <div className="card-icon">{card.icon}</div>
                <h2 className="card-title">{card.title}</h2>
                <p className="card-value">{card.value !== undefined ? card.value : 'N/A'}</p>
              </div>
            ))
        }
      </div>
    </motion.div>
  );
};

export default SubjectDetails;