import '../styles/ChatLog.css';
import ReactMarkdown from 'react-markdown'


const ChatLog = ({ isOpen, closeModal, loadSelectedChat }) => {
    if (!isOpen) return null;

    // 로컬 스토리지에서 저장된 채팅 기록 불러오기
    const savedMessages = JSON.parse(localStorage.getItem('chatMessages')) || [];

    const handleOverlayClick = (e) => {
        if (e.target.classList.contains('chatlog-overlay')) {
            closeModal();
        }
    };

    // 클릭 시 대화 불러오기
    const handleSelectChat = () => {
        loadSelectedChat(savedMessages); // 선택한 기록 불러오기
        closeModal(); // 모달 닫기
    };

    return (
        <div className='chatlog-overlay' onClick={handleOverlayClick}>
            <div className='chatlog-modal' onClick={(e) => e.stopPropagation()}>
                <div className='chatlog-header'>
                    <h3>채팅 로그</h3>
                    <button className="chatlog-closebtn" onClick={closeModal}>
                        &times;
                    </button>
                </div>
                <div className='chatlog-content'>
                    {savedMessages.map((msg, index) => (
                        <div
                            key={index}
                            className={`chatlog-message ${msg.role}`}
                            onClick={handleSelectChat} // 클릭 이벤트 추가
                        >
                            <ReactMarkdown>{msg.content}</ReactMarkdown>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default ChatLog;
