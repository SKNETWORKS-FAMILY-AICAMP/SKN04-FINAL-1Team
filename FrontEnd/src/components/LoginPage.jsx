import { useNavigate } from 'react-router-dom';

const LoginPage = () => {
    const navigate = useNavigate();

    const handleLogin = () => {
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