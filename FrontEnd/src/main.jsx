import { createRoot } from 'react-dom/client';
import './index.css';
import App from './App.jsx';
import { StrictMode } from 'react';

createRoot(document.getElementById('root')).render(
    // <StrictMode>
    <App />
    /* App을 최상위 컴포넌트로 렌더링 */
    // </StrictMode>
);