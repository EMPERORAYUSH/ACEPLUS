import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { RiDashboardLine, RiFileAddLine, RiBarChartLine, RiHistoryLine, RiFileTextLine, RiArrowLeftLine } from 'react-icons/ri';

function BottomNav() {
  const navigate = useNavigate();
  const location = useLocation();
  const mainRoutes = ['/', '/home', '/create', '/test-series', '/analyse', '/history'];
  const isMainRoute = mainRoutes.includes(location.pathname);
  
  const handleBack = () => {
    // Optionally add delay for exit animation
    setTimeout(() => {
      navigate(-1);
    }, 150);
  };

  return (
    <div className="bottom-nav">
      <div className={`bottom-nav-content ${!isMainRoute ? 'with-back' : ''}`}>
        <button 
          onClick={handleBack} 
          className={`nav-item back-button ${!isMainRoute ? 'enter' : 'exit'}`}
        >
          <RiArrowLeftLine size={20} />
          <span>Back</span>
        </button>
        <div className={`nav-divider ${!isMainRoute ? 'enter' : 'exit'}`}></div>
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
