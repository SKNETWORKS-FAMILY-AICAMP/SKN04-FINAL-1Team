import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import '../styles/ChatWindow.css';

const ChatWindow = ({ session = { messages: [] }, updateSession = () => { } }) => {
    const [messages, setMessages] = useState(session.messages);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isOpen, setIsOpen] = useState(true)
    const textarea = useRef();
    const messagesEndRef = useRef(null);

    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages]);

    const sendMessage = async () => {
        if (input.trim()) {
            const userMessage = { role: 'user', content: input };
            const updatedMessages = [...messages, userMessage];
            setMessages(updatedMessages);
            setInput('');
            handleResizeHeight();
            setIsLoading(true);

            updateSession({ ...session, messages: updatedMessages });

            try {
                const response = await fetch('http://localhost:8000/real_estate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: input }),
                });
                const data = await response.json();
                const botMessage = { role: 'assistant', content: data.messages };

                const newMessages = [...updatedMessages, botMessage];
                setMessages(newMessages);
                updateSession({ ...session, messages: newMessages });
            } catch (error) {
                console.error('Error:', error);
                const errorMessage = { role: 'assistant', content: '오류 발생. 다시 시도해주세요.' };
                const newMessages = [...updatedMessages, errorMessage];
                setMessages(newMessages);
                updateSession({ ...session, messages: newMessages });
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
        isOpen && (
            <div className="chat-window">
                <div className="chat-window-messages">
                    <button className="notice-closebtn" onClick={() => setIsOpen(false)}>
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
                </div>
            </div>
        )
    );

};

export default ChatWindow;
