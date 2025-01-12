import { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { motion, useMotionValue } from 'framer-motion';
import '../styles/ChatWindow.css';

const ChatWindow = ({ isSidebarOpen }) => {
    const [messages, setMessages] = useState([]);
    const [favorites, setFavorites] = useState([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isOpen, setIsOpen] = useState(true);
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const headerRef = useRef(null);

    const pos = useRef({ x: 0, y: 0, offsetX: 0, offsetY: 0, dragging: false });
    const onMouseDown = (e) => {
        pos.current.dragging = true;
        pos.current.offsetX = e.clientX - pos.current.x;
        pos.current.offsetY = e.clientY - pos.current.y;

        document.body.style.userSelect = 'none';
        headerRef.current.style.cursor = 'grabbing';

        window.addEventListener('mousemove', onMouseMove);
        window.addEventListener('mouseup', onMouseUp);
    };
    const chatWindowRef = useRef(null);
    const onMouseMove = (e) => {
        if (!pos.current.dragging) return;
        pos.current.x = e.clientX - pos.current.offsetX;
        pos.current.y = e.clientY - pos.current.offsetY;
        chatWindowRef.current.style.transform = `translate(${pos.current.x}px, ${pos.current.y}px)`;
    };
    const onMouseUp = () => {
        pos.current.dragging = false;
        document.body.style.userSelect = 'auto';
        headerRef.current.style.cursor = 'grab';
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('mouseup', onMouseUp);
    };

    const API_KEY = '...'; // API_KEY는 안전하게 보관하세요!
    const textarea = useRef();

    // 메시지 창 마지막 요소에 대한 참조
    const messagesEndRef = useRef(null);

    // 초기 데이터 불러오기
    useEffect(() => {
        const storedMessages = localStorage.getItem('chatMessages');
        const storedFavorites = localStorage.getItem('favorites');
        if (storedMessages) setMessages(JSON.parse(storedMessages));
        if (storedFavorites) setFavorites(JSON.parse(storedFavorites));

        const loggedInStatus = localStorage.getItem('isLoggedIn');
        setIsLoggedIn(loggedInStatus === 'true');
    }, []);

    // 메시지가 업데이트될 때마다 스크롤 맨 아래로 이동
    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages]);

    // 메시지 전송 및 저장
    const sendMessage = async () => {
        if (input.trim()) {
            const userMessage = { role: 'user', content: input };
            const updatedMessages = [...messages, userMessage];
            setMessages(updatedMessages);
            setInput('');
            handleResizeHeight();
            setIsLoading(true);
            localStorage.setItem('chatMessages', JSON.stringify(updatedMessages));

            try {
                const response = await axios.post('http://127.0.0.1:8080/real_estate', 
                    { query: input },
                    { headers: { 'Content-Type': 'application/json' } }
                );

                const botMessage = {
                    role: 'assistant',
                    content: response.data.messages,
                };
                const newMessages = [...updatedMessages, botMessage];
                setMessages(newMessages);
                localStorage.setItem('chatMessages', JSON.stringify(newMessages));
            } catch (error) {
                console.error('Error:', error);
                const errorMessage = { role: 'assistant', content: '오류 발생. 다시 시도해주세요.' };
                setMessages([...updatedMessages, errorMessage]);
                localStorage.setItem('chatMessages', JSON.stringify(updatedMessages));
            } finally {
                setIsLoading(false);
            }
        }
    };

    // 즐겨찾기 추가 함수
    const toggleFavorite = (message) => {
        const updatedFavorites = favorites.includes(message)
            ? favorites.filter(fav => fav !== message)
            : [...favorites, message];
        setFavorites(updatedFavorites);
        localStorage.setItem('favorites', JSON.stringify(updatedFavorites));
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
        <div>
            {isLoggedIn && (
                <button className="chat-window-toggle-btn" onClick={() => setIsOpen(!isOpen)}>
                    {isOpen ? '채팅 닫기' : '채팅 열기'}
                </button>
            )}

            {isOpen && (
                <div
                    ref={chatWindowRef}
                    className={`chat-window ${isSidebarOpen ? 'open' : 'closed'}`}>
                    <div
                        className="chat-window-header"
                        onMouseDown={onMouseDown}
                        ref={headerRef}
                    >
                        <h3>서집사</h3>
                        <button onClick={() => setIsOpen(false)}>&times;</button>
                    </div>

                    <div className="chat-window-messages">
                        {messages.map((msg, index) => (
                            <div key={index} className={`chat-window-message ${msg.role}`}>
                                {msg.content}
                                <span
                                    className={`star-icon ${favorites.includes(msg.content) ? 'filled' : 'empty'}`}
                                    onClick={() => toggleFavorite(msg.content)}
                                >
                                    {favorites.includes(msg.content) ? '★' : '☆'}
                                </span>
                            </div>
                        ))}
                        {isLoading && <div className="chat-window-message loading">로딩 중...</div>}
                        {/* 스크롤 기준점 */}
                        <div ref={messagesEndRef} />
                    </div>

                    <div className="chat-window-input">
                        <textarea
                            ref={textarea}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="메시지를 입력하세요."
                            onKeyDown={handleKeyDown}
                            rows={1}
                        />
                        <button onClick={sendMessage} disabled={isLoading}>
                            {isLoading ? '전송 중...' : '전송'}
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ChatWindow;
