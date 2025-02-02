import '../styles/NoticeModal.css'

const NoticeModal = ({ isOpen, onClose }) => {
    if (!isOpen) return null;

    return (
        <div className="noticemodal-overlay" onClick={onClose}>
            <div className="noticemodal-modal" onClick={(e) => e.stopPropagation()}>
                <div className='noticemodal-header'>
                    <h2>Test-Notice1</h2>
                    <button onClick={onClose}>
                        &times;
                    </button>
                </div>
                <div className='noticemodal-text-main'>
                    <span>
                        test
                    </span>
                </div>
            </div>
        </div>
    );
};

export default NoticeModal;