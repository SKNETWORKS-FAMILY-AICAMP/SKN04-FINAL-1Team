import { useEffect } from 'react'
import '../styles/Userguide.css'

const Userguide = ({ isOpen, closeModal }) => {
    if (!isOpen) return null;

    const handleModalClick = (e) => {
        e.stopPropagation();
    };

    return (
        <div className="guide-backdrop" onClick={closeModal}>
            <div className="guide-modal" onClick={handleModalClick}>
                <div className="guide-header">
                    <h3>이용안내</h3>
                    <button className="closebtn" onClick={closeModal}>
                        &times;
                    </button>
                </div>
                <div className="guide-modal-body">
                    <div className='title'>
                        챗봇 이렇게 활용해보세요!
                    </div>
                    <div>
                        로그인 후 채팅로그 클릭!
                        <br />
                        New Chat을 클릭하면 채팅창이 나와요!
                        <br />
                        <br />
                        채팅을 이런식으로 입력해보세요.
                        <br />
                        <br />
                        "신림역이랑 가까운 원룸중에서 에어컨이랑 엘리베이터 있는 월세 매물 추천해줄래?"
                    </div>
                </div>
            </div>
        </div>
    );
};


export default Userguide;