import './App.css';
import Kakao from './components/Kakao';
import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary.jsx';
import LoginModal from './components/LoginModal.jsx';
import KakaoCallback from './components/KakaoCallback.jsx';
import NaverCallback from './components/NaverCallback.jsx';


const App = () => {
  return (
    <Router>
      <ErrorBoundary>
        <Routes>
          <Route path="/" element={<LoginModal />} />
          <Route path="/kakao/callback" element={<KakaoCallback />} />
          <Route path="/naver/callback" element={<NaverCallback />} />
        </Routes>
        <Kakao />
      </ErrorBoundary>
    </Router>
  );
};

export default App