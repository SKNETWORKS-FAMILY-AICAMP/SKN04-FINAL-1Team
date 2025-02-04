import './App.css';
import Kakao from './components/Kakao';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary.jsx';
import LoginModal from './components/LoginModal.jsx';


const App = () => {
  return (
    <Router>
      <ErrorBoundary>
        <Routes>
          <Route path="/" element={<LoginModal />} />
        </Routes>
        <Kakao />
      </ErrorBoundary>
    </Router>
  );
};

export default App