// utils/chatStorage.js
import { v4 as uuidv4 } from 'react-uuid';

// 채팅 저장 함수
export const saveChat = (chatID, messages) => {
    const chats = JSON.parse(localStorage.getItem('chats')) || {};
    chats[chatID] = messages;
    localStorage.setItem('chats', JSON.stringify(chats));
};

// 채팅 목록 가져오기 함수
export const getChatList = () => {
    const chats = JSON.parse(localStorage.getItem('chats')) || {};
    return Object.keys(chats);
};

// 특정 채팅 가져오기 함수
export const getChatByID = (chatID) => {
    const chats = JSON.parse(localStorage.getItem('chats')) || {};
    return chats[chatID] || [];
};

// 새로운 채팅 생성 함수
export const createNewChat = () => {
    const chatID = uuidv4();
    saveChat(chatID, []); // 초기 메시지 배열로 저장
    return chatID;
};

// 메시지 추가 함수
export const addMessageToChat = (chatID, message) => {
    const chats = JSON.parse(localStorage.getItem('chats')) || {};
    if (!chats[chatID]) {
        chats[chatID] = [];
    }
    chats[chatID].push(message);
    localStorage.setItem('chats', JSON.stringify(chats));
};
