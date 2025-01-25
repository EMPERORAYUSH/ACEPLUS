import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { RiDashboardLine, RiFileAddLine, RiBarChartLine, RiHistoryLine, RiFileTextLine } from 'react-icons/ri';

function BottomNav() {
  let navigate = useNavigate();
  const location = useLocation();

  return (
    <div className="bottom-nav">
      <div className="bottom-nav-content">
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
