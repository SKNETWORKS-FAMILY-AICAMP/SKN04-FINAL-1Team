import { useState, useEffect } from 'react';
import '../styles/RegisterForm.css';
import { registerUser } from '../api'; // 회원가입 API 호출 함수

const RegisterForm = ({ isOpen, closeModal }) => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [email, setEmail] = useState('');
    const [nickname, setNickname] = useState('');
    const [gender, setGender] = useState('');
    const [age, setAge] = useState('');

    const [isFormValid, setIsFormValid] = useState(false);
    const [errors, setErrors] = useState({
        username: '',
        password: '',
        email: '',
    });

    // 약관/개인정보 처리 관련 상태 (필요시)
    const [isTermsOpen, setIsTermsOpen] = useState(false);
    const [isPrivacyOpen, setIsPrivacyOpen] = useState(false);
    const [termsAgreed, setTermsAgreed] = useState(false);
    const [privacyAgreed, setPrivacyAgreed] = useState(false);

    // 폼 유효성 검사 함수
    const validateForm = () => {
        let newErrors = {};

        if (!username) {
            newErrors.username = '아이디를 입력하세요.';
        } else if (username.length < 8) {
            newErrors.username = '아이디는 최소 8자리 이상이어야 합니다.';
        }

        if (!password) {
            newErrors.password = '비밀번호를 입력하세요.';
        }

        if (!email) {
            newErrors.email = '이메일을 입력하세요.';
        } else if (!email.includes('@')) {
            newErrors.email = '유효한 이메일 주소를 입력하세요.';
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    // 폼 상태 변경에 따라 유효성 업데이트
    useEffect(() => {
        if (
            username.length >= 8 &&
            password &&
            email.includes('@') &&
            nickname &&
            gender &&
            age &&
            termsAgreed &&
            privacyAgreed
        ) {
            setIsFormValid(true);
        } else {
            setIsFormValid(false);
        }
    }, [username, password, email, nickname, gender, age, termsAgreed, privacyAgreed]);

    // 회원가입 API 호출하는 핸들러
    const handleRegister = async (e) => {
        e.preventDefault(); // 폼 기본 제출 이벤트 방지
        if (!validateForm()) return;

        // API에 보낼 회원가입 데이터 구성 (age는 숫자로 변환)
        const registrationData = {
            username,
            password,
            email,
            nickname,
            gender,
            age: Number(age)
        };

        try {
            // 회원가입 API 호출 (registerUser 함수는 백엔드의 '/api/auth/register/' 엔드포인트와 연동되어야 함)
            const response = await registerUser(registrationData);
            console.log('회원가입 성공:', response);
            alert('회원가입이 성공적으로 완료되었습니다.');
            closeModal();
        } catch (error) {
            console.error('회원가입 중 오류 발생:', error);
            alert('회원가입 중 오류가 발생했습니다. 다시 시도해 주세요.');
        }
    };

    return (
        <form onSubmit={handleRegister} className="registerform">
            <div className='register-header'>
                <h2>회원가입</h2>
                <button className="register-closebtn" onClick={closeModal}>
                    &times;
                </button>
            </div>

            {/* 약관 동의 섹션 */}
            <div className="terms-section">
                <div className="terms-item">
                    <label className="checkbox-container">
                        <input type="checkbox" checked={termsAgreed} onChange={() => setTermsAgreed(!termsAgreed)} />
                        <span className="checkmark"></span>
                        <span>[필수] 서비스 이용 약관 동의</span>
                    </label>
                    <button type="button" className="terms-toggle" onClick={() => setIsTermsOpen(!isTermsOpen)}>
                        {isTermsOpen ? "▲" : "▼"}
                    </button>
                </div>
                {isTermsOpen && (
                    <div className="terms-content">
                        고객님께서는 본 서비스를 이용함에 있어 다음의 이용 약관을 준수해야 합니다.
                        본 서비스는 개인 및 기업 사용자를 위한 서비스입니다.
                        이용자는 허위 정보 제공, 타인의 계정 도용, 불법적인 목적의 사용을 금지합니다.
                        당사는 서비스 운영 및 개선을 위해 필요 시 서비스 내용을 변경하거나 중단할 수 있습니다.
                        기타 법적 책임은 대한민국 법률을 따릅니다.
                    </div>
                )}

                <div className="terms-item">
                    <label className="checkbox-container">
                        <input type="checkbox" checked={privacyAgreed} onChange={() => setPrivacyAgreed(!privacyAgreed)} />
                        <span className="checkmark"></span>
                        <span>[필수] 개인정보 수집 및 이용 동의</span>
                    </label>
                    <button type="button" className="terms-toggle" onClick={() => setIsPrivacyOpen(!isPrivacyOpen)}>
                        {isPrivacyOpen ? "▲" : "▼"}
                    </button>
                </div>
                {isPrivacyOpen && (
                    <div className="terms-content">
                        서집사는 회원가입 및 서비스 제공을 위해 다음과 같은 개인정보를 수집 및 이용합니다.
                        수집 항목: 이메일, 닉네임, 성별, 나이
                        수집 목적: 회원 식별, 서비스 제공, 고객 지원
                        보유 기간: 회원 탈퇴 후 30일까지 보관 후 삭제
                        개인정보 처리방침에 대한 자세한 내용은 개인정보 처리방침에서 확인할 수 있습니다.
                    </div>
                )}
            </div>

            {/* 가입 폼 */}
            <div className="register-group">
                <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} maxLength={15} required />
                <label>아이디</label>
                {errors.username && <p className="error-message">{errors.username}</p>}
            </div>

            <div className="register-group">
                <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} maxLength={15} required />
                <label>비밀번호</label>
                {errors.password && <p className="error-message">{errors.password}</p>}
            </div>

            <div className="register-group">
                <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} maxLength={15} required />
                <label>이메일</label>
                {errors.email && <p className="error-message">{errors.email}</p>}
            </div>

            <div className="register-group">
                <input type="text" id="nickname" placeholder=" " value={nickname} onChange={(e) => setNickname(e.target.value)} maxLength={15} required />
                <label htmlFor="nickname">닉네임</label>
            </div>

            <div className="register-group">
                <select id="gender" value={gender} onChange={(e) => setGender(e.target.value)} required>
                    <option value="" hidden>성별 선택</option>
                    <option value="M">남성</option>
                    <option value="F">여성</option>
                    <option value="O">기타</option>
                </select>
                <label htmlFor="gender">성별</label>
            </div>

            <div className="register-group">
                <input type="number" id="age" placeholder=" " value={age} onChange={(e) => setAge(e.target.value)} min={1} max={100} required />
                <label htmlFor="age">나이</label>
            </div>

            <button type="submit" className={`registersubmit ${isFormValid ? "active" : ""}`} disabled={!isFormValid}>
                가입하기
            </button>
        </form>
    );
};

export default RegisterForm;
