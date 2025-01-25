import React, { useState, useEffect } from 'react';
import logo from './logo512.png'; // Update this path to your logo

const Header = ({ onVisibilityChange }) => {
  const [isVisible, setIsVisible] = useState(true);
  const [lastScrollY, setLastScrollY] = useState(0);

  useEffect(() => {
    const controlHeader = () => {
      if (typeof window !== 'undefined') {
        if (window.scrollY > lastScrollY) {
          setIsVisible(false);
        } else {
          setIsVisible(true);
        }
        setLastScrollY(window.scrollY);
      }
    };

    if (typeof window !== 'undefined') {
      window.addEventListener('scroll', controlHeader);

      return () => {
        window.removeEventListener('scroll', controlHeader);
      };
    }
  }, [lastScrollY]);

  useEffect(() => {
    onVisibilityChange(isVisible);
  }, [isVisible, onVisibilityChange]);
  
  return (
    <div className={`header ${isVisible ? '' : 'header--hidden'}`}>
      <img src={logo} alt="AcePlus Logo" className="header-logo" />
      <h1 className="header-text">AcePlus</h1>
    </div>
  );
};

export default Header;