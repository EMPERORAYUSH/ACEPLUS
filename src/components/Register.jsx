import React, { useState } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { HiEye, HiEyeOff } from 'react-icons/hi';
import { api } from '../utils/api';
import './login.css';

const Register = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [userId, setUserId] = useState(location.state?.userId || '');
  const [registrationCode, setRegistrationCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

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
      const data = await api.register({ userId, registrationCode, newPassword });
      if (data.token) {
        localStorage.setItem('token', data.token);
        localStorage.setItem('user_id', data.user_id);
        if (data.version) {
          localStorage.setItem('version', data.version);
        }
        navigate('/home');
        window.location.reload();
      } else {
        setError(data.message || 'An unexpected error occurred.');
      }
    } catch (error) {
      setError(error.message || 'An error occurred during registration.');
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
            Register
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
            <input
              type="text"
              id="registrationCode"
              className="form-input"
              value={registrationCode}
              onChange={(e) => setRegistrationCode(e.target.value)}
              placeholder=" "
              required
            />
            <label htmlFor="registrationCode" className="form-label">Registration Code</label>
          </motion.div>

          <motion.div 
            className="form-group"
            variants={itemVariants}
          >
            <div className="password-input-wrapper">
              <input
                type={showPassword ? "text" : "password"}
                id="newPassword"
                className="form-input"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder=" "
                required
              />
              <label htmlFor="newPassword" className="form-label">New Password</label>
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
                <span>Registering...</span>
              </>
            ) : (
              'Register and Login'
            )}
          </motion.button>
        </form>
        <motion.p
          variants={itemVariants}
          className="extra-link"
        >
          Already registered? <Link to="/login">Login</Link>
        </motion.p>
      </motion.div>
    </div>
  );
};

export default Register;