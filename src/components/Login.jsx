import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { HiEye, HiEyeOff } from 'react-icons/hi';
import Spinner from './Spinner'; // Import your Spinner component
import Notification from './Notification'; // Import your Notification component
import { api } from '../utils/api';
import './login.css';

const Login = () => {
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const navigate = useNavigate();

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        duration: 0.3,
        when: "beforeChildren",
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        type: "spring",
        stiffness: 300,
        damping: 24
      }
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const data = await api.login({ userId, password });
      localStorage.setItem('token', data.token);
      localStorage.setItem('user_id', data.user_id);
      navigate('/home');
      window.location.reload();
    } catch (error) {
      setError(error.message || 'An error occurred during login.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-page">
      <motion.div 
        className="login-card"
        initial="hidden"
        animate="visible"
        variants={containerVariants}
      >
        {error && (
          <motion.div 
            className="error-message"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
          >
            {error}
          </motion.div>
        )}
        <form onSubmit={handleSubmit}>
          <motion.h2 
            className="login-title"
            variants={itemVariants}
          >
            Welcome Back
          </motion.h2>
          
          <motion.div 
            className="form-group"
            variants={itemVariants}
          >
            <input
              type="text"
              id="userId"
              className="form-input"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder=" "
              required
            />
            <label htmlFor="userId" className="form-label">GR NUMBER</label>
          </motion.div>

          <motion.div 
            className="form-group"
            variants={itemVariants}
          >
            <div className="password-input-wrapper">
              <input
                type={showPassword ? "text" : "password"}
                id="password"
                className="form-input"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder=" "
                required
              />
              <label htmlFor="password" className="form-label">Password</label>
              <motion.button
                type="button"
                className="password-toggle"
                onClick={() => setShowPassword(!showPassword)}
                tabIndex="-1"
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <HiEyeOff size={20} /> : <HiEye size={20} />}
              </motion.button>
            </div>
          </motion.div>

          <motion.button 
            type="submit" 
            className="login-button" 
            disabled={isLoading}
            variants={itemVariants}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {isLoading ? (
              <>
                <div className="spinner" />
                <span>Logging in...</span>
              </>
            ) : (
              'Login'
            )}
          </motion.button>
        </form>
      </motion.div>
    </div>
  );
};

export default Login;