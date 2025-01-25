import '../styles/ChatLog.css';
import ReactMarkdown from 'react-markdown'


const ChatLog = ({ isOpen, closeModal, loadSelectedChat }) => {
    if (!isOpen) return null;

    const savedMessages = JSON.parse(localStorage.getItem('chatMessages')) || [];

    const handleOverlayClick = (e) => {
        if (e.target.classList.contains('chatlog-overlay')) {
            closeModal();
        }
    };

    const handleSelectChat = () => {
        loadSelectedChat(savedMessages);
        closeModal();
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
                            onClick={handleSelectChat}
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
