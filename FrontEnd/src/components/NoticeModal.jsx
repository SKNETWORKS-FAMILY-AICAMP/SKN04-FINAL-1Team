import '../styles/NoticeModal.css'

const NoticeModal = ({ isOpen, onClose, notice }) => {
    if (!isOpen || !notice) return null;

    return (
        <div className="noticemodal-overlay" onClick={onClose}>
            <div className="noticemodal-modal" onClick={(e) => e.stopPropagation()}>
                <div className='noticemodal-header'>
                    <h2>{notice.title}</h2>
                    <button onClick={onClose}>
                        &times;
                    </button>
                </div>
                <div className='noticemodal-text-main'>
                    <span>
                        {notice.content}
                    </span>
                </div>
            </div>
        </div>
    );
};

export default NoticeModal;