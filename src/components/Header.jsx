import React, { useState, useEffect } from 'react';
import { FaCoins } from 'react-icons/fa';
import { api } from '../utils/api';
import logo from './logo512.png';
import './Header.css';
import Coins from './Coins';

const Header = ({ completedTasks }) => {
  const [coins, setCoins] = useState(0);
  const [tasks, setTasks] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCoinsPopupOpen, setCoinsPopupOpen] = useState(false);
  const isAuthenticated = !!localStorage.getItem('token');

  const fetchCoinData = async () => {
    if (!isAuthenticated) return;
    try {
      const data = await api.fetchCoins();
      setCoins(data.coins);
      setTasks(data.tasks || []);
    } catch (error) {
      console.error("Failed to fetch coins data", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isAuthenticated) {
      const timer = setTimeout(() => {
        fetchCoinData();
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (completedTasks && completedTasks.length > 0) {
      fetchCoinData();
    }
  }, [completedTasks]);

  const handleCoinsClick = () => {
    setCoinsPopupOpen(true);
  };

  const handleClosePopup = () => {
    setCoinsPopupOpen(false);
  };

  return (
    <>
      <div className="header">
        <div className="header-left">
          <img src={logo} alt="AcePlus Logo" className="header-logo" />
          <h1 className="header-text">AcePlus</h1>
        </div>
        {isAuthenticated && (
          <div className={`header-right ${isLoading ? 'is-loading' : 'is-loaded'}`} onClick={handleCoinsClick} style={{ cursor: 'pointer' }}>
            <div className="skeleton skeleton-coin"></div>
            <div className="coins-container">
              <FaCoins className="coins-icon" />
              <span className="coins-amount">{coins}</span>
            </div>
          </div>
        )}
      </div>
      {isAuthenticated && <Coins isOpen={isCoinsPopupOpen} onClose={handleClosePopup} tasks={tasks} coins={coins} />}
    </>
  );
};

export default Header;