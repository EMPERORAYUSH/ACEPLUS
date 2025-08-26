import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { RiDashboardLine, RiFileAddLine, RiBarChartLine, RiHistoryLine, RiFileTextLine, RiArrowLeftLine } from 'react-icons/ri';
import './mobile-bottomnav.css';

function BottomNav() {
  const navigate = useNavigate();
  const location = useLocation();
  const [isScrolled, setIsScrolled] = useState(false);
  const mainRoutes = ['/', '/home', '/create', '/test-series', '/analyse', '/history'];
  const isMainRoute = mainRoutes.includes(location.pathname);

  // Normalize active route logic: treat "/" and "/home" as Dashboard
  const isDashboardActive = location.pathname === '/' || location.pathname === '/home';

  const navRef = useRef(null);
  const highlightRef = useRef(null);

  useEffect(() => {
    let lastScrollTop = 0;
    const handleScroll = () => {
      const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
      // Hide on scroll down, show on scroll up - but only when back button is visible
      if (!isMainRoute) {
        setIsScrolled(scrollTop > lastScrollTop && scrollTop > 50);
      } else {
        setIsScrolled(false); // Always expand on main routes
      }
      lastScrollTop = scrollTop <= 0 ? 0 : scrollTop;
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  }, [isMainRoute]);

  const handleBack = () => {
    // Check if we can go back in history, otherwise go to dashboard
    if (window.history.length > 1) {
      navigate(-1);
    } else {
      navigate('/');
    }
  };

  useEffect(() => {
    const activeButton = navRef.current.querySelector('.nav-item.active');
    if (activeButton && highlightRef.current) {
      highlightRef.current.style.width = `${activeButton.offsetWidth}px`;
      highlightRef.current.style.left = `${activeButton.offsetLeft}px`;
    }
  }, [location]);

  return (
    <div className={`bottom-nav ${isScrolled ? 'scrolled' : ''}`}>
      {/* Back button with improved positioning */}
      <button
        onClick={handleBack}
        className={`mobile-back-button ${!isMainRoute ? 'show' : 'hide'}`}
        aria-label="Go back to previous page"
      >
        <RiArrowLeftLine />
      </button>

      {/* Main navigation bar */}
      <nav
        ref={navRef}
        className={`bottom-nav-content ${!isMainRoute ? 'contract' : 'expand'}`}
        role="navigation"
        aria-label="Main navigation"
      >
        <div ref={highlightRef} className="nav-highlight" />
        <button
          onClick={() => navigate('/')}
          className={`nav-item ${isDashboardActive ? 'active' : ''}`}
          aria-label="Dashboard"
          aria-current={isDashboardActive ? 'page' : undefined}
        >
          <RiDashboardLine />
          <span>Dashboard</span>
        </button>
        <button
          onClick={() => navigate('/create')}
          className={`nav-item ${location.pathname === '/create' ? 'active' : ''}`}
          aria-label="Create new test"
          aria-current={location.pathname === '/create' ? 'page' : undefined}
        >
          <RiFileAddLine />
          <span>Create</span>
        </button>
        <button
          onClick={() => navigate('/test-series')}
          className={`nav-item ${location.pathname === '/test-series' ? 'active' : ''}`}
          aria-label="Test series"
          aria-current={location.pathname === '/test-series' ? 'page' : undefined}
        >
          <RiFileTextLine />
          <span>Tests</span>
        </button>
        <button
          onClick={() => navigate('/analyse')}
          className={`nav-item ${location.pathname === '/analyse' ? 'active' : ''}`}
          aria-label="Analyze results"
          aria-current={location.pathname === '/analyse' ? 'page' : undefined}
        >
          <RiBarChartLine />
          <span>Analyse</span>
        </button>
        <button
          onClick={() => navigate('/history')}
          className={`nav-item ${location.pathname === '/history' ? 'active' : ''}`}
          aria-label="View history"
          aria-current={location.pathname === '/history' ? 'page' : undefined}
        >
          <RiHistoryLine />
          <span>History</span>
        </button>
      </nav>
    </div>
  );
}

export default BottomNav;
