import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence, useScroll } from 'framer-motion';
import { useInView } from 'react-intersection-observer';
import './LandingPage.css';

const features = [
  {
    title: "Smart Exam Creation",
    description: "Tailor-made exams based on your chosen subjects and lessons.",
    icon: "📚"
  },
  {
    title: "AI-Powered Analysis",
    description: "Get detailed performance insights and personalized AI solutions for every question, helping you learn from mistakes and improve faster.",
    icon: "🤖"
  },
  {
    title: "Subject-wise Performance", 
    description: "Track progress across subjects and improve your weakest subjects.",
    icon: "⭐"
  },
  {
    title: "Monthly Leaderboard",
    description: "Compete with peers and track your standing in your division.",
    icon: "🏆"
  }
];

const LandingPage = () => {
  const navigate = useNavigate();
  const { scrollYProgress } = useScroll();
  const [isVisible, setIsVisible] = useState(false);

  const [featuresRef, featuresInView] = useInView({
    triggerOnce: true,
    threshold: 0.2
  });

  useEffect(() => {
    // Hide bottom nav when landing page mounts
    const bottomNav = document.querySelector('.bottom-nav');
    if (bottomNav) {
      bottomNav.style.display = 'none';
    }

    // Show bottom nav when component unmounts
    return () => {
      if (bottomNav) {
        bottomNav.style.display = 'block';
      }
    };
  }, []);

  useEffect(() => {
    const visited = localStorage.getItem('hasVisitedBefore');
    if (visited) {
      navigate('/login');
    }
  }, [navigate]);

  const handleGetStarted = () => {
    localStorage.setItem('hasVisitedBefore', 'true');
    navigate('/login');
  };

  useEffect(() => {
    const toggleVisibility = () => {
      setIsVisible(window.pageYOffset > 300);
    };

    window.addEventListener('scroll', toggleVisibility);
    return () => window.removeEventListener('scroll', toggleVisibility);
  }, []);

  return ( 
    <div className="landing-container">
      <motion.div 
        className="progress-bar"
        style={{ scaleX: scrollYProgress }}
      />

      <nav className="landing-nav">
        <motion.div 
          className="logo"
          initial={{ opacity: 0, x: -50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8 }}
        >
          AcePlus
        </motion.div>
      </nav>

      <main className="landing-main">
        <section className="hero-section">
          <motion.div 
            className="hero-content"
            initial={{ y: -50, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.8, delay: 0.2 }}
          >
            <h1>Elevate Your Learning with AcePlus</h1>
            <p>Empowering students of Holy Angels School with AI-driven exam preparation</p>
            <motion.button 
              className="get-started-btn"
              onClick={handleGetStarted}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              Get Started
              <span className="arrow-icon">→</span>
            </motion.button>
          </motion.div>
          
          <motion.div
            className="scroll-indicator"
            animate={{ y: [0, 10, 0] }}
            transition={{ repeat: Infinity, duration: 1.5 }}
          >
            ↓
          </motion.div>
        </section>

        <motion.section 
          ref={featuresRef}
          className="features-section"
        >
          <motion.h2 
            initial={{ opacity: 0, y: 30 }}
            animate={featuresInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.6 }}
          >
            Key Features
          </motion.h2>
          
          <div className="features-grid">
            {features.map((feature, index) => (
              <motion.div 
                key={feature.title}
                className="feature-card"
                initial={{ opacity: 0, y: 50, scale: 0.9 }}
                animate={featuresInView ? { 
                  opacity: 1, 
                  y: 0, 
                  scale: 1 
                } : {}}
                transition={{
                  duration: 0.5,
                  delay: featuresInView ? 0.2 * index : 0,
                  type: "spring",
                  stiffness: 100,
                  damping: 15
                }}
                whileHover={{
                  scale: 1.05,
                  rotateY: 5,
                  boxShadow: "0 20px 40px rgba(79, 172, 254, 0.2)"
                }}
              >
                <div className="feature-icon">{feature.icon}</div>
                <h3>{feature.title}</h3>
                <p>{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </motion.section>

        <motion.div 
          className="creator-section"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.5 }}
        >
          <h2>About the Creator</h2>
          <p>Created with ❤️ by Ayush Pandey</p>
          <p>Class IX Student at Holy Angels School, Dombivli</p>
          <p>Designed exclusively for Holy Angels School students</p>
        </motion.div>
      </main>

      <footer className="landing-footer">
        <p>© 2024 AcePlus - Holy Angels School Dombivli</p>
        <p>A student initiative for smarter learning</p>
      </footer>
    </div>
  );
};

export default LandingPage;