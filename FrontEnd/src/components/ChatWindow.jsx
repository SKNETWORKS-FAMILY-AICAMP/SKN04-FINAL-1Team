import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import '../styles/ChatWindow.css';

const ChatWindow = ({ session = { messages: [] }, updateSession = () => { }, closeChatWindow }) => {
    const [messages, setMessages] = useState(session.messages);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const textarea = useRef();
    const messagesEndRef = useRef(null);

    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages]);

    useEffect(() => {
        const loggedInStatus = localStorage.getItem('isLoggedIn') === 'true';
        setIsLoggedIn(loggedInStatus);
    }, []);

    const sendMessage = async () => {
        if (!isLoggedIn) {
            alert('로그인이 필요합니다.');
            return;
        }

        if (input.trim()) {
            const userMessage = { role: 'user', content: input };
            const updatedMessages = [...messages, userMessage];
            setMessages(updatedMessages);
            setInput('');
            handleResizeHeight();
            setIsLoading(true);

            updateSession({ ...session, messages: updatedMessages });

            try {
                const response = await fetch('http://localhost:8001/real_estate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: input }),
                });
                // const data = await response.text();

                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                if (!response.body) throw new Error('No response body');

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let botMessage = { role: 'assistant', content:'' };

                setMessages(prev => [...prev, botMessage]);

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    const chunk = decoder.decode(value, { stream: true });
                    botMessage.content += chunk;
                    setMessages(prev => [...prev.slice(0, -1), botMessage]);
                }
                
                
                localStorage.setItem('chatMessages', JSON.stringify([...updatedMessages, botMessage]));
                // const newMessages = [...updatedMessages, botMessage];
                // setMessages(newMessages);
                // updateSession({ ...session, messages: newMessages });
            } catch (error) {
                console.error('Error:', error);
                const errorMessage = { role: 'assistant', content: '오류 발생. 다시 시도해주세요.' };
                // const newMessages = [...updatedMessages, errorMessage];
                setMessages(prev => [...prev, errorMessage]);
                localStorage.setItem('chatMessages', JSON.stringify([...updatedMessages, errorMessage]));

                // setMessages(newMessages);
                // updateSession({ ...session, messages: newMessages });
            } finally {
                setIsLoading(false);
            }
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    const handleResizeHeight = () => {
        textarea.current.style.height = 'auto';
        textarea.current.style.height = textarea.current.scrollHeight + 'px';
    };

    return (
        <div className="chat-window">
            <div className="chat-window-messages">
                <button className="notice-closebtn" onClick={closeChatWindow}>
                    &times;
                </button>
                {messages.map((msg, index) => (
                    <div key={index} className={`chat-window-message ${msg.role}`}>
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                    </div>
                ))}
                {isLoading && <div className="chat-window-message loading">로딩 중...</div>}
                <div ref={messagesEndRef} />
            </div>

            <div className="chat-window-input">
                {!isLoggedIn ? (
                    <p className="chat-login-message">로그인 후 채팅을 이용할 수 있습니다.</p>
                ) : (
                    <>
                        <textarea
                            ref={textarea}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="메시지를 입력하세요."
                            onKeyUp={handleKeyDown}
                            rows={1}
                        />
                        <button onClick={sendMessage} disabled={isLoading}>
                            {isLoading ? '전송 중...' : '전송'}
                        </button>
                    </>
                )}
            </div>
        </div>
    );
};

export default ChatWindow;
