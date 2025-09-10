import React from 'react';
import { Navigate } from 'react-router-dom';

const ProtectedRoute = ({ children, updateAuthState }) => {
    const token = localStorage.getItem('token');
    if (!token) {
        // Update the auth state in the parent App component
        if (updateAuthState) {
            updateAuthState();
        }
        return <Navigate to="/login" />;
    }
    return children;
};

export default ProtectedRoute;