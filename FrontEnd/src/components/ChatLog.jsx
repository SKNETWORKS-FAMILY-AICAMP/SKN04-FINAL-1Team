import { useState, useEffect } from 'react';
import ChatWindow from './ChatWindow';
import '../styles/ChatLog.css';
import { fetchChatSessions, fetchChatSessionMessages } from '../api';

const ChatLog = ({ setProperties }) => {
    const [chatSessions, setChatSessions] = useState([]);
    const [currentSessionId, setCurrentSessionId] = useState(null);
    const [isOpen, setIsOpen] = useState(true);
    const [isLoggedIn, setIsLoggedIn] = useState(false);

    useEffect(() => {
        const loggedInStatus = localStorage.getItem('isLoggedIn') === 'true';
        setIsLoggedIn(loggedInStatus);
        if (loggedInStatus) {
            fetchChatSessions()
                .then((data) => {
                    setChatSessions(data);
                    if (data.length > 0) {
                        setCurrentSessionId(data[0].session_id);
                    }
                })
                .catch((error) => console.error("채팅 세션 데이터를 가져오는 중 오류:", error));
        }
    }, []);

    useEffect(() => {
        if (currentSessionId) {
            fetchChatSessionMessages(currentSessionId)
                .then((data) => {
                    setChatSessions((prevSessions) =>
                        prevSessions.map((session) =>
                            session.session_id === currentSessionId ? { ...session, messages: data } : session
                        )
                    );
                })
                .catch((error) => console.error("채팅 메시지 데이터를 가져오는 중 오류:", error));
        }
    }, [currentSessionId]);

    const createNewChat = () => {
        if (!isLoggedIn) {
            alert('로그인이 필요합니다.');
            return;
        }
        const newSession = {
            session_id: Date.now().toString(),
            messages: []
        };
        setChatSessions((prev) => [newSession, ...prev]);
        setCurrentSessionId(newSession.session_id);
    };

    const selectChat = (sessionId) => {
        if (!isLoggedIn) {
            alert('로그인이 필요합니다.');
            return;
        }
        setCurrentSessionId(sessionId);
    };

    const currentSession = chatSessions.find(
        (session) => session.session_id === currentSessionId
    ) || { session_id: currentSessionId, messages: [] };

    if (!isLoggedIn) {
        return <p className="chat-login-message">로그인 후 이용 가능합니다.</p>;
    }

    return (
        <>
            {isOpen && (
                <>
                    <div className={`chatlog-module ${currentSessionId ? 'active' : ''}`}>
                        <div className="chatlog-sidebar">
                            <button onClick={createNewChat} className="new-chat-btn">
                                + New Chat
                            </button>
                            <button className="chat-closebtn" onClick={() => setIsOpen(false)}>
                                &times;
                            </button>
                            <ul className="chat-session-list">
                                {chatSessions.map((session) => {
                                    const summary = session.messages?.[0]?.message
                                        ? session.messages[0].message.slice(0, 30) +
                                        (session.messages[0].message.length > 30 ? '...' : '')
                                        : '새 대화';
                                    return (
                                        <li
                                            key={session.session_id}
                                            className={`chat-session-item ${session.session_id === currentSessionId ? 'active' : ''
                                                }`}
                                            onClick={() => selectChat(session.session_id)}
                                        >
                                            {summary}
                                        </li>
                                    );
                                })}
                            </ul>
                        </div>
                    </div>

                    <div className="chatlog-main">
                        {currentSessionId !== null && (
                            <ChatWindow
                                key={currentSessionId}
                                session={currentSession}
                                setProperties={setProperties}
                                updateSession={(updatedSession) => {
                                    setChatSessions((prevSessions) =>
                                        prevSessions.map((session) =>
                                            session.session_id === updatedSession.session_id ? updatedSession : session
                                        )
                                    );
                                }}
                                closeChatWindow={() => setCurrentSessionId(null)}
                            />
                        )}
                    </div>
                </>
            )}
        </>
    );
};

export default ChatLog;
