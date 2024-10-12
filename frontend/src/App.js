import React, { useState } from 'react';
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';
import Login from './components/Login';
import Register from './components/Register';
import ImageUploader from './components/ImageUploader';
import ChatPopup from './components/ChatPopup'; // Импортируем чат

const App = () => {
  const [token, setToken] = useState(localStorage.getItem('token') || null);

  const handleLoginSuccess = (token) => {
    setToken(token);
  };

  const handleLogout = () => {
    setToken(null);
    localStorage.removeItem('token');
  };

  return (
    <Router>
      <div>
        <Header token={token} handleLogout={handleLogout} />
        <Routes>
          <Route
            path="/"
            element={
              token ? <Navigate to="/upload" /> : <Navigate to="/login" />
            }
          />
          <Route
            path="/login"
            element={
              !token ? (
                <Login onLoginSuccess={handleLoginSuccess} />
              ) : (
                <Navigate to="/upload" />
              )
            }
          />
          <Route
            path="/register"
            element={!token ? <Register /> : <Navigate to="/upload" />}
          />
          <Route
            path="/upload"
            element={
              token ? <ImageUploader token={token} /> : <Navigate to="/login" />
            }
          />
          <Route path="*" element={<h2>404 - Страница не найдена</h2>} />
        </Routes>

        <ChatPopup />

        <Footer />
      </div>
    </Router>
  );
};

export default App;
