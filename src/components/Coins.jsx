import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FaTimes, FaCoins, FaArrowRight } from 'react-icons/fa';
import './Coins.css';

const Coins = ({ isOpen, onClose, tasks, coins }) => {
  const [isRendered, setIsRendered] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (isOpen) {
      setIsRendered(true);
    }
  }, [isOpen]);

  const handleClose = () => {
    onClose();
  };

  const onAnimationEnd = () => {
    if (!isOpen) {
      setIsRendered(false);
    }
  };

  const handleActionClick = (action) => {
    if (action.type === 'exam') {
      if (action.lessons && action.lessons.length > 0) {
        navigate('/exam/g/create', { state: { subject: action.subject, lessons: action.lessons } });
      } else {
        navigate('/create', { state: { subject: action.subject } });
      }
    } else if (action.type === 'navigate') {
      navigate(action.path);
    } else if (action.type === 'test') {
      navigate('/exam/g/create', { state: { testId: action['test-id'] } });
    }
    handleClose();
  };

  const generateTaskDescription = (task) => {
    if (!task.details || !task.details.text) {
      return <p className="task-description">{task.description}</p>;
    }

    const parts = task.details.text.split(/(\{.*?\})/g).map((part, index) => {
      if (part === '{count}') {
        return <strong key={index}>{task.details.count}</strong>;
      }
      if (task.details.completed !== null && task.details.total) {
        if (part === '{completed}') {
          return <strong key={index}>{task.details.completed}</strong>;
        }
        if (part === '{total}') {
          return <strong key={index}>{task.details.total}</strong>;
        }
      }
      if (part === '{subject}') {
        return <span key={index} className="task-param">{task.details.subject}</span>;
      }
      if (part === '{lesson}' || part === '{lessons}') {
        if (Array.isArray(task.details.lessons)) {
          return <span key={index} className="task-param">{task.details.lessons.join(', ')}</span>;
        }
        return <span key={index} className="task-param">{task.details.lesson}</span>;
      }
      return part;
    });

    return <p className="task-description">{parts}</p>;
  };

  if (!isRendered) return null;

  return (
    <div
      className={`coins-popup-overlay ${!isOpen ? 'closing' : ''}`}
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          handleClose();
        }
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="daily-tasks-title"
    >
      <div
        className={`coins-popup ${!isOpen ? 'closing' : ''}`}
        onAnimationEnd={onAnimationEnd}
        role="document"
      >
        <div className="popup-header">
          <div className="coins-display" aria-label={`You have ${coins} coins`}>
            <FaCoins />
            <span>{coins}</span>
          </div>
          <h2 id="daily-tasks-title">Daily Tasks</h2>
          <button className="close-button" onClick={handleClose} aria-label="Close daily tasks popup">
            <FaTimes />
          </button>
        </div>
        <div className="tasks-container">
          {tasks && tasks.length > 0 ? (
            tasks.map((task) => (
              <div key={task.id} className={`task-card ${task.completed ? 'completed' : ''}`}>
                <div className="task-info">
                  <h3 className="task-title">{task.title}</h3>
                  {generateTaskDescription(task)}
                </div>
                <div className="task-meta">
                  <div className="task-reward">
                    <FaCoins className="coins-icon" />
                    <span>{task.reward}</span>
                  </div>
                  <button
                    className="cta-button"
                    onClick={() => handleActionClick(task.action)}
                    disabled={task.completed}
                    aria-label={`${task.cta} - ${task.title}`}
                  >
                    <span>{task.completed ? 'Completed' : typeof task.num_completed === 'number' ? `${task.num_completed}/${task.details.count} Done` : task.cta || 'Go'}</span>
                    {!task.completed && <FaArrowRight />}
                  </button>
                </div>
              </div>
            ))
          ) : (
            <p className="no-tasks-message">No tasks available for today. Check back tomorrow!</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default Coins;