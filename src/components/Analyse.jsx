import React from 'react';
import { motion } from 'framer-motion';

const Analyse = () => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.2 }}
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        height: '80vh',
        color: 'white',
        textAlign: 'center',
        padding: '20px'
      }}
    >
      <h1 style={{ fontSize: '2.5rem', marginBottom: '1rem' }}>🚧 Under Construction 🚧</h1>
      <p style={{ fontSize: '1.2rem' }}>This page is currently being built. Please check back later!</p>
    </motion.div>
  );
};

export default Analyse;