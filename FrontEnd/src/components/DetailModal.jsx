import ReactDOM from 'react-dom';
import '../styles/DetailModal.css';

const DetailModal = ({ isOpen, closeModal, markerInfo }) => {
    if (!isOpen || !markerInfo) return null;

    const depositMatch = markerInfo.description.match(/보증금[^\d]*([\d,]+만원)/);
    const deposit = depositMatch ? depositMatch[1] : "정보 없음";

    return ReactDOM.createPortal(
        <div className="detail-overlay" onClick={closeModal}>
            <div className="detail-modal" onClick={(e) => e.stopPropagation()}>
                <div className="detail-header">
                    <h3>매물 상세정보</h3>
                    <button className="detail-closebtn" onClick={closeModal}>
                        &times;
                    </button>
                </div>
                <div className="detail-content">
                    <p><strong>이름:</strong> {markerInfo.name}</p>
                    <p><strong>전세가:</strong> {deposit}</p>
                    <p><strong>설명:</strong> {markerInfo.description}</p>
                </div>
            </div>
        </div>,
        document.body
    );
};

export default DetailModal;
