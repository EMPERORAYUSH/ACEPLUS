// components/ExamSkeletonLoading.jsx
import React from 'react';

const ExamSkeletonLoading = () => {
  return (
    <div className="exam-skeleton-container">
      {[1, 2, 3, 4].map((item) => (
        <div key={item} className="exam-skeleton-card">
          <div className="exam-skeleton-question"></div>
          <div className="exam-skeleton-options">
            <div className="exam-skeleton-option"></div>
            <div className="exam-skeleton-option"></div>
            <div className="exam-skeleton-option"></div>
            <div className="exam-skeleton-option"></div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default ExamSkeletonLoading;