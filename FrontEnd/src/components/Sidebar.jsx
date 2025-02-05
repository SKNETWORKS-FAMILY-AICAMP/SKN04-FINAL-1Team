import { useState, useEffect } from 'react';
import '../styles/Sidebar.css';
import LoginModal from './LoginModal';
import RegisterModal from './RegisterModal';
import Notice from './Notice';
import Userguide from './Userguide';
import Feedback from './Feedback';
import ChatLog from './ChatLog';

const Sidebar = ({ isOpen, toggleSidebar, setProperties }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isRegisterModalOpen, setIsRegisterModalOpen] = useState(false);
  const [isNoticeOpen, setIsNoticeOpen] = useState(false);
  const [isGuideOpen, setIsGuideOpen] = useState(false);
  const [isFeedbackOpen, setIsFeedbackOpen] = useState(false);
  const [isChatLogOpen, setIsChatLogOpen] = useState(false);

  const [isLoggedIn, setIsLoggedIn] = useState(
    localStorage.getItem('isLoggedIn') === 'true'
  );

  useEffect(() => {
    const storedLoginStatus = localStorage.getItem('isLoggedIn') === 'true';
    setIsLoggedIn(storedLoginStatus);
  }, []);

  const openModal = () => {
    closeAllModal();
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
  };

  const openRegisterModal = () => {
    closeAllModal();
    setIsRegisterModalOpen(true);
  };

  const closeRegisterModal = () => {
    setIsRegisterModalOpen(false);
  };

  const closeNotice = () => {
    setIsNoticeOpen(false);
  };

  const closeGuide = () => {
    setIsGuideOpen(false);
  };


  const closeFeedback = () => {
    setIsFeedbackOpen(false);
  };
  const closeChatLog = () => {
    setIsChatLogOpen(false);
  };

  const toggleNotice = () => {
    closeAllModal();
    setIsNoticeOpen(!isNoticeOpen);
  };

  const toggleGuide = () => {
    closeAllModal();
    setIsGuideOpen(!isGuideOpen);
  };

  const toggleFeedback = () => {
    closeAllModal();
    setIsFeedbackOpen(!isFeedbackOpen);
  };


  const handleLogOut = () => {
    localStorage.removeItem('isLoggedIn');
    localStorage.setItem('isChatOpen', 'false');
    setIsLoggedIn(false);
    alert('안녕히 가세요!');
    setTimeout(() => {
      window.location.reload();
    }, 100);
  };

  const closeAllModal = () => {
    setIsModalOpen(false);
    setIsRegisterModalOpen(false);
    setIsNoticeOpen(false);
    setIsGuideOpen(false);
    setIsFeedbackOpen(false);
    setIsChatLogOpen(false);
    localStorage.setItem('isChatOpen', 'false');
  };

  return (
    <>
      <div className={`sidebar ${isOpen ? 'open' : 'closed'}`}>
        <div className='btn'>
          <button className='btn-home' onClick={() => window.location.reload()}>
            <img className='icon-home' src="/images/home.png" alt="홈" />
            <span>홈</span>
          </button>
          {isLoggedIn ? (
            <button onClick={handleLogOut}>
              <img className='icon-logout' src='/images/logout.png' alt='로그아웃' />
              <span>로그아웃</span>
            </button>
          ) : (
            <button onClick={openModal}>
              <img className='icon-login' src='/images/login.png' alt="로그인" />
              <span>로그인</span>
            </button>
          )}
          <button onClick={toggleNotice}>
            <img className='icon-notice' src='/images/notice.png' alt="공지사항" />
            <span>공지사항</span>
          </button>
          <button onClick={toggleGuide}>
            <img className='icon-userGuide' src='/images/userGuide.png' alt="이용안내" />
            <span>이용안내</span>
          </button>
          <button onClick={toggleFeedback}>
            <img className='icon-feedback' src='/images/feedback.png' alt="피드백" />
            <span>피드백</span>
          </button>

          <hr />

          <button onClick={() => setIsChatLogOpen(!isChatLogOpen)}>
            <img className='icon-chatlog' src='/images/chatLog.png' alt="채팅로그" />
            <span>채팅로그</span>
          </button>
        </div>
      </div>

      <button className='sidebarToggle' onClick={toggleSidebar}>
        {isOpen ? '<<' : '>>'}
      </button>

      <LoginModal
        isOpen={isModalOpen}
        closeModal={closeModal}
        openRegisterModal={openRegisterModal}
        onLoginSuccess={() => setIsLoggedIn(true)}
      />
      <RegisterModal
        isOpen={isRegisterModalOpen}
        closeModal={closeRegisterModal}
      />
      <Notice isOpen={isNoticeOpen} closeModal={closeNotice} />
      <Userguide isOpen={isGuideOpen} closeModal={closeGuide} />
      <Feedback isOpen={isFeedbackOpen} closeModal={closeFeedback} />
      {isChatLogOpen && <ChatLog isOpen={isChatLogOpen} closeModal={closeChatLog} setProperties={setProperties} />}
    </>
  );
};

export default Sidebar;