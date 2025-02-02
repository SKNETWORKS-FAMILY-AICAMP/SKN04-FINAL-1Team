import React from 'react';
import '../styles/SocialKakao.css';

const SocialKakao = ({ isOpen, closeModal }) => {
    const REST_API_KEY = '40c5325f5f2367d3a912d067b2f06148';
    const REDIRECT_URI = 'http://127.0.0.1:3000/kakao/callback';
    const link = `https://kauth.kakao.com/oauth/authorize?client_id=${REST_API_KEY}&redirect_uri=${REDIRECT_URI}&response_type=code`;

    const loginHandler = () => {
        window.location.href = link;
    }

    return (
        <div>
            <button
                onClick={loginHandler}
                className='kakaologinbtn'
            >
                <img
                    src="/images/kakao.png"
                    alt="카카오"
                    className="kakaologin"
                />
            </button>
        </div>
    );
}

export default SocialKakao;
