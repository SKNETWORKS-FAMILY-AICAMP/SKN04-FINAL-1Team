import { useState, useEffect } from 'react';
import ChatWindow from './ChatWindow';
import '../styles/ChatLog.css';

const ChatLog = () => {
    const [chatSessions, setChatSessions] = useState([]);
    const [currentSessionId, setCurrentSessionId] = useState(null);
    const [isOpen, setIsOpen] = useState(true);
    useEffect(() => {
        const storedChats = localStorage.getItem('chatSessions');
        if (storedChats) {
            setChatSessions(JSON.parse(storedChats));
        }
    }, []);

    useEffect(() => {
        localStorage.setItem('chatSessions', JSON.stringify(chatSessions));
    }, [chatSessions]);

    const createNewChat = () => {
        const newSession = { id: Date.now(), messages: [] };
        setChatSessions(prevSessions => [newSession, ...prevSessions]);
        setCurrentSessionId(newSession.id);
    };

    const selectChat = (sessionId) => {
        setCurrentSessionId(sessionId);
    };

    const currentSession = chatSessions.find(session => session.id === currentSessionId) || { id: currentSessionId, messages: [] };

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
                                {chatSessions.map(session => {
                                    const summary = session.messages.length > 0
                                        ? session.messages[0].content.slice(0, 30) + (session.messages[0].content.length > 30 ? '...' : '')
                                        : '새 대화';
                                    return (
                                        <li
                                            key={session.id}
                                            className={`chat-session-item ${session.id === currentSessionId ? 'active' : ''}`}
                                            onClick={() => selectChat(session.id)}
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
                                updateSession={(updatedSession) => {
                                    setChatSessions(prevSessions =>
                                        prevSessions.map(session =>
                                            session.id === updatedSession.id ? updatedSession : session
                                        )
                                    );
                                }}
                            />
                        )}
                    </div>
                </>
            )}
        </>
    );

};

export default ChatLog;
