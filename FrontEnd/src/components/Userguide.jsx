import { useEffect } from 'react'
import '../styles/Userguide.css'

const Userguide = ({ isOpen, closeModal }) => {
    if (!isOpen) return null; // 모달이 닫혀있으면 렌더링하지 않음

    // Esc 키를 눌러 모달 닫기
    const handleKeyDown = (e) => {
        if (e.key === 'Escape') {
            closeModal();
        }
    };

    useEffect(() => {
        document.addEventListener('keydown', handleKeyDown);
        return () => {
            document.removeEventListener('keydown', handleKeyDown);
        };
    }, []);

    // 모달 내부 클릭 시 이벤트 전파 차단
    const handleModalClick = (e) => {
        e.stopPropagation();
    };

    return (
        <div className="guide-backdrop" onClick={closeModal}>
            <div className="guide-modal" onClick={handleModalClick}>
                <div className="guide-header">
                    <h3>이용안내</h3>
                    <button className="closebtn" onClick={closeModal}>
                        &times;
                    </button>
                </div>
                <div className="guide-modal-body">
                    <div className='title'>
                        챗봇 이렇게 활용해보세요!
                    </div>
                    <div>
                        내용 추가 예정
                    </div>
                </div>
            </div>
        </div>
    );
};


export default Userguide;