import '../styles/SocialNaver.css'

const SocialNaver = ({ isOpen, closeModal }) => {
    const NAVER_CLIENT_ID = 'HaY3V1fzfW0wBsqWdwyF';
    const REDIRECT_URI = 'http://127.0.0.1:3000/naver/callback';
    const STATE = 'false';
    const NAVER_AUTH_URL = `https://nid.naver.com/oauth2.0/authorize?response_type=code&client_id=${NAVER_CLIENT_ID}&state=${STATE}&redirect_uri=${REDIRECT_URI}`;

    const NaverLogin = () => {
        window.location.href = NAVER_AUTH_URL
    }

    return (
        <button
            onClick={NaverLogin}
            className='naverloginbtn'
        >
            <img
                src="/images/naver.png"
                alt="네이버"
                className='naverlogin'
            />
        </button>
    )
};

export default SocialNaver;
