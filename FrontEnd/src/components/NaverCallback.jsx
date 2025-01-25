import axios from 'axios';
import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

const NaverCallback = () => {
    const navigate = useNavigate();
    const isCalled = useRef(false);

    useEffect(() => {
        if (isCalled.current) return;
        isCalled.current = true;

        const code = new URL(window.location.href).searchParams.get('code');
        const state = new URL(window.location.href).searchParams.get('state');

        if (code && state) {
            getToken(code, state);
        }
    }, []);

    const getToken = async (code, state) => {
        const CLIENT_ID = 'HaY3V1fzfW0wBsqWdwyF';
        const CLIENT_SECRET = 'PYYXh95Wmx';
        const REDIRECT_URI = 'http://127.0.0.1:3000/naver/callback';

        try {
            const response = await axios.post(
                'https://nid.naver.com/oauth2.0/token',
                null,
                {
                    params: {
                        grant_type: 'authorization_code',
                        client_id: CLIENT_ID,
                        client_secret: CLIENT_SECRET,
                        redirect_uri: REDIRECT_URI,
                        code: code,
                        state: state,
                    },
                }
            );

            window.history.replaceState({}, null, window.location.pathname);

            const accessToken = response.data.access_token;
            console.log('액세스 토큰:', accessToken);

            getUserInfo(accessToken);
        } catch (err) {
            console.error('토큰 요청 실패:', err);

            window.history.replaceState({}, null, window.location.pathname);

            alert('로그인에 실패했습니다.');
            navigate('/');
        }
    };

    const getUserInfo = async (token) => {
        try {
            const response = await axios.get('https://openapi.naver.com/v1/nid/me', {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            console.log('사용자 정보:', response.data);

            const userInfo = response.data.response;
            localStorage.setItem('isLoggedIn', 'true');
            localStorage.setItem('email', userInfo.email);

            alert(`환영합니다! ${userInfo.name}님`);
            window.location.reload();
        } catch (err) {
            console.error('사용자 정보 요청 실패:', err);

            window.history.replaceState({}, null, window.location.pathname);

            alert('사용자 정보를 가져오지 못했습니다.');
            navigate('/');
        }
    };

    return null;
};

export default NaverCallback;
