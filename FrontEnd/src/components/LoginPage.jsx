import React from 'react';
import { useNavigate } from 'react-router-dom';

const LoginPage = () => {
    const navigate = useNavigate();

    const handleLogin = () => {
        // 로그인 성공 시 메인 페이지로 이동
        navigate('/main');
    };

    return (
        <div>
            <h1>로그인 페이지</h1>
            <button onClick={handleLogin}>로그인</button>
        </div>
    );
};

export default LoginPage;
