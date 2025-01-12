import '../styles/LoginModal.css'; // 스타일 파일
import { useState } from 'react';
import SocialKakao from './SocialKakao';
import SocialNaver from './SocialNaver';

const LoginModal = ({ isOpen, closeModal }) => {

    // 상태 관리
    const [isSocialKakaoOpen, setIsSocialKakaoOpen] = useState(false);
    const [isSocialNaverOpen, setIsSocialNaverOpen] = useState(false);


    const closeSocialKakao = () => {
        setIsSocialKakaoOpen(false);
    };

    const closeSocialNaver = () => {
        setIsSocialNaverOpen(false);
    };

    return (
        isOpen &&
        <div className="login-modal-overlay" onClick={closeModal}>
            <div className="login-modal" onClick={(e) => e.stopPropagation()}>
                <div className="login-header">
                    <h2>서집사</h2>
                    <button
                        onClick={() =>
                            closeModal()
                        }>
                        <img src="/images/close.png" alt="닫기 이미지" />
                    </button>
                </div>
                <div className='sociallogin'>
                    <SocialKakao
                        isOpen={isSocialKakaoOpen}
                        closeModal={closeSocialKakao}
                    />
                    <SocialNaver
                        isOpen={isSocialNaverOpen}
                        closeModal={closeSocialNaver}
                    />
                </div>
            </div>
        </div >
    )
};

export default LoginModal;
