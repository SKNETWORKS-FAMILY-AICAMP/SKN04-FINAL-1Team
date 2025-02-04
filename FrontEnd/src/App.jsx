import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useState } from 'react';
import ErrorBoundary from './components/ErrorBoundary';
import Sidebar from './components/Sidebar';
import Kakao from './components/Kakao';

function App() {
  const [properties, setProperties] = useState([]);

  return (
    <Router>
      <ErrorBoundary>
        <Kakao properties={properties} />
        <Sidebar
          isOpen={true}
          toggleSidebar={() => { }}
          setProperties={setProperties}
        />
        <Routes>
          <Route path="/" element={<div>메인 화면</div>} />
        </Routes>
      </ErrorBoundary>
    </Router>
  );
}

export default App;
