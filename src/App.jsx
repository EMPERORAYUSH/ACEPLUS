import React, { useState, useEffect } from "react";
import {
  Route,
  Routes,
  Navigate,
  useLocation,
} from "react-router-dom";
import Sidebar from "./components/sidebar";
import Content from "./components/body-content";
import BottomNav from "./components/mobile-bottomnav";
import Exam from "./components/Exam";
import Login from "./components/Login";
import Register from "./components/Register";
import ProtectedRoute from "./components/ProtectedRoute";
import NotFound from "./components/NotFound";
import Analysis from "./components/AnalysisView";
import SubjectDetails from "./components/SubjectDetails";
import ExamTaking from "./components/ExamTaking";
import ExamResults from "./components/ExamResults";
import History from "./components/History";
import TestSeries from "./components/TestSeries";
import Header from "./components/Header";
import CreateTest from "./components/CreateTest";
import LandingPage from "./components/LandingPage";

import "./App.css";

const ScrollToTop = () => {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pathname]);
  return null;
};

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isHeaderVisible, setIsHeaderVisible] = useState(true);
  const [completedTasks, setCompletedTasks] = useState([]);
  const [refreshCoins, setRefreshCoins] = useState(false);
  const location = useLocation();

  const handleTaskCompletion = (tasks) => {
    setCompletedTasks(tasks);
    setRefreshCoins(true); // Trigger coin refresh
  };

  useEffect(() => {
    const token = localStorage.getItem("token");
    setIsAuthenticated(!!token);
  }, []);

  const showHeader = location.pathname !== '/';

  return (
    <div className={`App ${isHeaderVisible ? "" : "header-hidden"}`}>
      {showHeader && <Header onVisibilityChange={setIsHeaderVisible} completedTasks={completedTasks} />}
      {isAuthenticated && <Sidebar isHeaderHidden={!isHeaderVisible} />}
      
      <Routes>
        <Route
          path="/"
          element={isAuthenticated ? <Navigate to="/home" /> : <LandingPage />}
        />
        <Route
          path="/home"
          element={
            <ProtectedRoute>
              <Content />
              <ScrollToTop />
            </ProtectedRoute>
          }
        />
        <Route
          path="/login"
          element={isAuthenticated ? <Navigate to="/home" /> : <Login />}
        />
        <Route
          path="/register"
          element={isAuthenticated ? <Navigate to="/home" /> : <Register />}
        />
        <Route
          path="/create"
          element={
            <ProtectedRoute>
              <Exam />
            </ProtectedRoute>
          }
        />
        <Route
          path="/analyse"
          element={
            <ProtectedRoute>
              <Analysis />
            </ProtectedRoute>
          }
        />
        <Route
          path="/analyse/:subject"
          element={
            <ProtectedRoute>
              <SubjectDetails />
            </ProtectedRoute>
          }
        />
        <Route
          path="/history"
          element={
            <ProtectedRoute>
              <History />
            </ProtectedRoute>
          }
        />
        <Route
          path="/exam/g/:id"
          element={
            <ProtectedRoute>
              <ExamTaking />
            </ProtectedRoute>
          }
        />
        <Route
          path="/exam/results/:id"
          element={
            <ProtectedRoute>
              <ExamResults onTaskCompletion={handleTaskCompletion} />
            </ProtectedRoute>
          }
        />
        <Route
          path="/test-series"
          element={
            <ProtectedRoute>
              <TestSeries />
            </ProtectedRoute>
          }
        />
        <Route
          path="/create-test"
          element={
            <ProtectedRoute>
              <CreateTest />
            </ProtectedRoute>
          }
        />
        {/* Catch-all route */}
        <Route
          path="*"
          element={isAuthenticated ? <NotFound /> : <Navigate to="/login" />}
        />
      </Routes>

      {isAuthenticated && window.innerWidth <= 768 && <BottomNav />}
    </div>
  );
}

export default App;