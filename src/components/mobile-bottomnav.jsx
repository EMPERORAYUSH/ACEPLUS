import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { RiDashboardLine, RiFileAddLine, RiBarChartLine, RiHistoryLine, RiFileTextLine, RiArrowLeftLine } from 'react-icons/ri';

function BottomNav() {
  let navigate = useNavigate();
  const location = useLocation();
  const [isExiting, setIsExiting] = useState(false);
  const [shouldRender, setShouldRender] = useState(false);

  const mainRoutes = ['/', '/home', '/create', '/test-series', '/analyse', '/history'];
  const isMainRoute = mainRoutes.includes(location.pathname);

  useEffect(() => {
    if (!isMainRoute && !shouldRender) {
      setShouldRender(true);
    } else if (isMainRoute && shouldRender) {
      setIsExiting(true);
      const timer = setTimeout(() => {
        setShouldRender(false);
        setIsExiting(false);
      }, 300); // Match animation duration
      return () => clearTimeout(timer);
    }
  }, [isMainRoute, shouldRender]);

  const handleBack = () => {
    setIsExiting(true);
    setTimeout(() => {
      navigate(-1);
    }, 150); // Half of animation duration for smoother feel
  };

  return (
    <div className="bottom-nav">
      <div className={`bottom-nav-content ${!isMainRoute ? 'with-back' : ''}`}>
        {shouldRender && (
          <>
            <button 
              onClick={handleBack} 
              className={`nav-item back-button ${isExiting ? 'exit' : 'enter'}`}
            >
              <RiArrowLeftLine size={20} />
              <span>Back</span>
            </button>
            <div className={`nav-divider ${isExiting ? 'exit' : 'enter'}`}></div>
          </>
        )}
        <button 
          onClick={() => navigate('/')} 
          className={`nav-item ${location.pathname === '/home' ? 'active' : ''}`}
        >
          <RiDashboardLine size={20} />
          <span>Dashboard</span>
        </button>
        <button 
          onClick={() => navigate('/create')} 
          className={`nav-item ${location.pathname === '/create' ? 'active' : ''}`}
        >
          <RiFileAddLine size={20} />
          <span>Create</span>
        </button>
        <button 
          onClick={() => navigate('/test-series')} 
          className={`nav-item ${location.pathname === '/test-series' ? 'active' : ''}`}
        >
          <RiFileTextLine size={20} />
          <span>Tests</span>
        </button>
        <button 
          onClick={() => navigate('/analyse')} 
          className={`nav-item ${location.pathname === '/analyse' ? 'active' : ''}`}
        >
          <RiBarChartLine size={20} />
          <span>Analyse</span>
        </button>
        <button 
          onClick={() => navigate('/history')} 
          className={`nav-item ${location.pathname === '/history' ? 'active' : ''}`}
        >
          <RiHistoryLine size={20} />
          <span>History</span>
        </button>
      </div>
    </div>
  );
}

export default BottomNav;
