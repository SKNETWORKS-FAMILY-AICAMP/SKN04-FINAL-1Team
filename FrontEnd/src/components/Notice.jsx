import { useEffect } from "react";
import '../styles/Notice.css';
import { useState } from "react";
import NoticeModal from "./NoticeModal";
import { fetchNotices } from "../api";

const Notice = ({ isOpen, closeModal }) => {
    if (!isOpen) return null;

    const [isOpenNoticeModal, setIsOpenNoticeModal] = useState('');
    const [notices, setNotices] = useState([])
    const [selectedNotice, setSelectedNotice] = useState(null)

    useEffect(() => {
        const getNotices = async () => {
            try {
                const data = await fetchNotices();
                setNotices(data);
            } catch (error) {
                console.error(error);
            }
        };

        getNotices();
    }, []);

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

    const openNoticeModal = (notice) => {
        setSelectedNotice(notice);
        setIsOpenNoticeModal(true);
    };
    const closeNoticeModal = () => {
        setIsOpenNoticeModal(false);
        setSelectedNotice(null);
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
                    {notices.length > 0 ? (
                        notices.map((notice) => (
                            <button
                                key={notice.id}
                                className="notice-btn1"
                                onClick={() => openNoticeModal(notice)}
                            >
                                <div className="notice-body-title">
                                    {notice.title || "공지사항 제목"}
                                </div>
                                <div className="notice-body-date">
                                    {new Date(notice.created_at).toLocaleDateString() || "날짜"}
                                </div>
                                <br />
                                <div className="notice-body-text">
                                    {notice.content?.substring(0, 100) || "공지사항 내용"}
                                </div>
                            </button>
                        ))
                    ) : (
                        <p>공지사항이 없습니다.</p>
                    )}
                </div>
            </div>
            <NoticeModal isOpen={isOpenNoticeModal} onClose={closeNoticeModal} notice={selectedNotice} />
        </div>
    );
};

export default Notice;