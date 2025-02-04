import '../styles/LoginModal.css';
import { useState } from 'react';
import { loginUser } from '../api'
import RegisterModal from './RegisterModal';

const LoginModal = ({ isOpen, closeModal, openRegisterModal, onLoginSuccess }) => {
    const [isRegisterOpen, setIsRegisterOpen] = useState(false);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loginError, setLoginError] = useState(null);

    const closeRegisterForm = () => {
        setIsRegisterOpen(false);
    };

    const handleLogin = async () => {
        const credentials = { username, password };

        try {
            const response = await loginUser(credentials);
            console.log('로그인 성공');
            console.log(response)
            alert('안녕하세요. 서집사에 오신걸 환영합니다.')
            localStorage.setItem('isLoggedIn', 'true');

            if (onLoginSuccess) {
                onLoginSuccess();
            }

            closeModal();
        } catch (error) {
            setLoginError('아이디 또는 비밀번호가 잘못되었습니다. 회원가입 후 이용해 주세요.');
            console.error('로그인 실패:', error);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') {
            handleLogin()
        }
    }

    return (
        isOpen && (
            <div className="login-modal-overlay" onClick={closeModal}>
                <div className="login-modal" onClick={(e) => e.stopPropagation()}>
                    <div className="login-header">
                        <h2>서집사</h2>
                        <button onClick={closeModal}>
                            <img src="/images/close.png" alt="닫기 이미지" />
                        </button>
                    </div>
                    <div className="sociallogin">
                        <div className={`input-group ${username ? 'filled' : ''}`}>
                            <input
                                type="text"
                                id="username"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                            />
                            <label htmlFor="username">아이디</label>
                        </div>

                        <div className={`input-group ${password ? 'filled' : ''}`}>
                            <input
                                type="password"
                                id="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                onKeyDown={handleKeyDown}
                            />
                            <label htmlFor="password">비밀번호</label>
                        </div>
                        <br />
                        <div className='loginmodalbtn'>
                            {loginError && <p style={{ color: 'red' }}>{loginError}</p>}
                            <button onClick={handleLogin}>로그인</button>
                            <button onClick={openRegisterModal}>회원가입</button>
                        </div>
                    </div>

                    {isRegisterOpen && <RegisterModal closeModal={closeRegisterForm} />}
                </div>
            </div>
        )
    );
};

export default LoginModal;