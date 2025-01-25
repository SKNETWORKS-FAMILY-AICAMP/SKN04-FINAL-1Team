import { useEffect } from 'react'
import '../styles/Userguide.css'

const Userguide = ({ isOpen, closeModal }) => {
    if (!isOpen) return null;

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