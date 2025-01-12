import axios from 'axios';
import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';

const NaverCallback = () => {
    const navigate = useNavigate();
    const isCalled = useRef(false); // 중복 호출 방지

    useEffect(() => {
        if (isCalled.current) return; // 중복 호출 방지
        isCalled.current = true; // 호출 여부 설정

        const code = new URL(window.location.href).searchParams.get('code'); // 인가 코드 추출
        const state = new URL(window.location.href).searchParams.get('state'); // CSRF 공격 방지용 상태값 확인

        if (code && state) {
            getToken(code, state); // 인가 코드로 액세스 토큰 요청
        }
    }, []);

    const getToken = async (code, state) => {
        const CLIENT_ID = 'HaY3V1fzfW0wBsqWdwyF'; // 네이버 클라이언트 ID
        const CLIENT_SECRET = 'PYYXh95Wmx'; // 네이버 클라이언트 시크릿
        const REDIRECT_URI = 'http://127.0.0.1:3000/naver/callback'; // 네이버 리다이렉트 URI

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

            // URL에서 인가 코드 제거
            window.history.replaceState({}, null, window.location.pathname);

            const accessToken = response.data.access_token;
            console.log('액세스 토큰:', accessToken);

            // 사용자 정보 요청
            getUserInfo(accessToken);
        } catch (err) {
            console.error('토큰 요청 실패:', err);

            // 실패 시에도 URL에서 인가 코드 제거
            window.history.replaceState({}, null, window.location.pathname);

            alert('로그인에 실패했습니다.');
            navigate('/'); // 실패 시 메인 페이지로 이동
        }
    };

    const getUserInfo = async (token) => {
        try {
            const response = await axios.get('https://openapi.naver.com/v1/nid/me', {
                headers: {
                    Authorization: `Bearer ${token}`, // 액세스 토큰 전달
                },
            });

            console.log('사용자 정보:', response.data);

            // 사용자 정보 저장 (로컬 스토리지)
            const userInfo = response.data.response;
            localStorage.setItem('isLoggedIn', 'true');
            localStorage.setItem('email', userInfo.email); // 이메일 저장

            alert(`환영합니다! ${userInfo.name}님`);
            window.location.reload(); // 페이지 새로고침
        } catch (err) {
            console.error('사용자 정보 요청 실패:', err);

            // 사용자 정보 요청 실패 시 URL 정리
            window.history.replaceState({}, null, window.location.pathname);

            alert('사용자 정보를 가져오지 못했습니다.');
            navigate('/'); // 실패 시 메인 페이지로 이동
        }
    };

    return null;
};

export default NaverCallback;
