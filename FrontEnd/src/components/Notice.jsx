import { useEffect } from "react";
import '../styles/Notice.css';
import { useState } from "react";
import NoticeModal from "./NoticeModal";

const Notice = ({ isOpen, closeModal }) => {
    if (!isOpen) return null;

    const [isOpenNoticeModal, setIsOpenNoticeModal] = useState('');


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

    const openNoticeModal = () => {
        setIsOpenNoticeModal(true);
    };

    const closeNoticeModal = () => {
        setIsOpenNoticeModal(false);
    };

    return (
        <div className="notice-overlay" onClick={closeModal}>
            <div className="notice-modal" onClick={handleModalClick}>
                <div className="notice-header">
                    <h3>공지사항</h3>
                    <button className="notice-closebtn" onClick={closeModal}>
                        &times;
                    </button>
                </div>
                <div className="notice-modal-body">
                    <button className="notice-btn1" onClick={openNoticeModal}>
                        <div className="notice-body-title">
                            첫번째 공지사항 입니다.
                        </div>
                        <br />
                        <div className="notice-body-date">
                            2025.01.08
                        </div>
                        <div className="notice-body-text">
                            첫번째 공지사항 내용입니다.
                        </div>
                    </button>
                </div>
            </div>
            <NoticeModal isOpen={isOpenNoticeModal} onClose={closeNoticeModal} />
        </div>
    );
};

export default Notice;
