import '../styles/RegisterModal.css'; // 별도의 스타일 파일 사용 (필요시)
import RegisterForm from './RegisterForm';

const RegisterModal = ({ isOpen, closeModal }) => {
    if (!isOpen) return null;

    const handleOverlayClick = (e) => {
        if (e.target.classList.contains('register-modal-overlay')) {
            closeModal();
        }
    };

    return (
        <div className="register-modal-overlay" onClick={handleOverlayClick}>
            <RegisterForm closeModal={closeModal} />
        </div>
    );
};

export default RegisterModal;