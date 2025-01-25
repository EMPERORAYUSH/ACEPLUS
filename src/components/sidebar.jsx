import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

function Sidebar({ isHeaderHidden }) {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div className={`sidebar ${isHeaderHidden ? 'header-hidden' : ''}`}>
      <button onClick={() => navigate('/home')} className={`btn ${location.pathname === '/' ? 'active' : ''}`}>
        🏠
        <span>Home</span>
      </button>
      <button onClick={() => navigate('/create')} className={`btn ${location.pathname === '/create' ? 'active' : ''}`}>
        📖
        <span>Create Exam</span>
      </button>
      <button onClick={() => navigate('/test-series')} className={`btn ${location.pathname === '/test-series' ? 'active' : ''}`}>
        📝
        <span>Test Series</span>
      </button>
      <button onClick={() => navigate('/analyse')} className={`btn ${location.pathname === '/analyse' ? 'active' : ''}`}>
        📊
        <span>Analyse</span>
      </button>
      <button onClick={() => navigate('/history')} className={`btn ${location.pathname === '/history' ? 'active' : ''}`}>
        📜
        <span>History</span>
      </button>
    </div>
  );
}

export default Sidebar;