import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import axios from 'axios';
import '../styles/ChatWindow.css';

const API_BASE_URL = 'http://localhost:8000/api/';
const FASTAPI_URL = 'http://localhost:8001/real_estate';
const PROPERTIES_URL = 'http://localhost:8001/properties';

function ChatWindow({
    session = { session_id: '', messages: [] },
    updateSession = () => { },
    closeChatWindow,
    setProperties
}) {
    const [messages, setMessages] = useState(session.messages || []);
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

    const fetchProperties = async () => {
        try {
            const response = await axios.get(PROPERTIES_URL);
            console.log('FastAPI /properties 응답:', response.data);
            setProperties(response.data.properties);
        } catch (error) {
            console.error("Error fetching properties:", error);
        }
    };

    const sendMessage = async () => {
        if (!isLoggedIn) {
            alert('로그인이 필요합니다.');
            return;
        }
        if (!input.trim()) return;

        setIsLoading(true);
        const token = localStorage.getItem('token');
        if (!token) {
            alert('로그인 후 이용 가능합니다.');
            setIsLoading(false);
            return;
        }

        let userMessage;
        try {
            const userRes = await axios.post(
                `${API_BASE_URL}chats/`,
                {
                    session_id: session.session_id || Date.now().toString(),
                    message: input,
                    message_type: 'user'
                },
                {
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    withCredentials: true,
                }
            );
            userMessage = userRes.data;
            const updatedMessages = [...messages, userMessage];
            setMessages(updatedMessages);
            updateSession({ ...session, messages: updatedMessages });
        } catch (error) {
            console.error('Error saving user message:', error);
            setIsLoading(false);
            return;
        }

        let botResponseText = "";
        try {
            const response = await fetch(FASTAPI_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query: input }),
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            if (!response.body) throw new Error('No response body');
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                botResponseText += decoder.decode(value, { stream: true });
            }
        } catch (error) {
            console.error('Error fetching assistant response:', error);
            botResponseText = '오류 발생. 다시 시도해주세요.';
        }

        try {
            const botRes = await axios.post(
                `${API_BASE_URL}chats/`,
                {
                    session_id: session.session_id || userMessage.session_id,
                    message: botResponseText,
                    message_type: 'bot'
                },
                {
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    withCredentials: true,
                }
            );
            const botMessage = botRes.data;
            const finalMessages = [...messages, userMessage, botMessage];
            setMessages(finalMessages);
            updateSession({ ...session, messages: finalMessages });
        } catch (error) {
            console.error('Error saving assistant message:', error);
            const errorMessage = {
                role: 'assistant',
                content: '오류 발생. 다시 시도해주세요.'
            };
            const finalMessages = [...messages, userMessage, errorMessage];
            setMessages(finalMessages);
            updateSession({ ...session, messages: finalMessages });
        } finally {
            setIsLoading(false);

            fetchProperties();
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    const fetchPropertiesByIds = async (propertyIds) => {
        try {
            const response = await axios.get(`${PROPERTIES_URL}`, {
                params: { property_ids: propertyIds.join(",") }
            });
            console.log('📍 FastAPI에서 가져온 매물:', response.data);
            setProperties(response.data.properties);  // ✅ 부모 컴포넌트에서 Kakao 지도 업데이트
        } catch (error) {
            console.error("🚨 Error fetching properties:", error);
        }
    };



    return (
        <div className="chat-window">
            <div className="chat-window-messages">
                <button className="notice-closebtn" onClick={closeChatWindow}>
                    &times;
                </button>
                {messages.map((msg, index) => {
                    const role = msg.message_type === 'user' ? 'user' : 'assistant';
                    return (
                        <div key={index} className={`chat-window-message ${role}`}>
                            <ReactMarkdown>{msg.message || msg.content}</ReactMarkdown>
                        </div>
                    );
                })}
                {isLoading && (
                    <div className="chat-window-message loading">로딩 중...</div>
                )}
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
                            onKeyDown={handleKeyDown}
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
}

export default ChatWindow;
