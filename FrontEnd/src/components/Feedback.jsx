import '../styles/Feedback.css';
import { useState } from 'react';
import { FaStar } from 'react-icons/fa';
import { postFeedback } from '../api.jsx';

const Feedback = ({ isOpen, closeModal }) => {
    if (!isOpen) return null;

    const [starsQ1, setStarsQ1] = useState(0);
    const [starsQ2, setStarsQ2] = useState(0);
    const [starsQ3, setStarsQ3] = useState(0);
    const [sliderValue, setSliderValue] = useState(0);
    const [text, setText] = useState('');

    const Star = ({ selected, onClick }) => (
        <FaStar color={selected ? 'blue' : 'gray'} onClick={onClick} />
    );

    const createArray = (length) => [...Array(length)];

    const isButtonActive =
        starsQ1 !== 0 &&
        starsQ2 !== 0 &&
        starsQ3 !== 0 &&
        Number(sliderValue) !== 0 &&
        text.trim() !== '';

    const handleOverlayClick = (e) => {
        if (e.target.classList.contains('feedback-overlay')) {
            closeModal();
        }
    };

    const StarRating = ({ totalStars = 5, selectedStars, setSelectedStars }) => (
        <div
            className="feedback-star-container"
            style={{
                display: 'flex',
                justifyContent: 'center',
                gap: '10px',
                fontSize: '35px'
            }}
        >
            {createArray(totalStars).map((_, i) => (
                <Star key={i} selected={selectedStars > i} onClick={() => setSelectedStars(i + 1)} />
            ))}
        </div>
    );
    const handleSubmit = async () => {
        const token = localStorage.getItem('token');
        if (!token) {
            alert('로그인 후 피드백을 제출할 수 있습니다.');
            return;
        }
        const feedbackData = {
            homepage_rating: Number(sliderValue),
            q1_accuracy: starsQ1,
            q2_naturalness: starsQ2,
            q3_resolution: starsQ3,
            feedback_text: text
        };

        try {
            await postFeedback(feedbackData);
            alert('피드백이 제출되었습니다.');
            closeModal();
        } catch (error) {
            console.error('피드백 제출 중 오류 발생:', error);
            alert('피드백 제출 중 오류가 발생했습니다.');
        }
    };
    return (
        <div className="feedback-overlay" onClick={handleOverlayClick}>
            <div className="feedback-modal">
                <div className="feedback-header">
                    <h3>피드백</h3>
                    <button className="feedback-closebtn" onClick={closeModal}>
                        &times;
                    </button>
                </div>
                <div className="feedback-first-container">
                    <h2>홈페이지 점수를 입력해 주세요.</h2>
                    <div className="feedback-slider-container">
                        <div className="feedback-slider-img">
                            <img src="/images/bad.png" alt="bad" />
                            <img src="/images/good.png" alt="good" />
                        </div>
                        <div className="feedback-slider-p">
                            <p>0</p>
                            <p>10</p>
                        </div>
                        <input
                            type="range"
                            min={0}
                            max={10}
                            value={sliderValue}
                            onChange={(e) => setSliderValue(e.target.value)}
                        />
                        <p className="feedback-slider-container-p">{sliderValue}</p>
                    </div>
                </div>
                <div className="feedback-second-container">
                    <h2>챗봇을 평가해 주세요!</h2>
                    <p>1. 챗봇의 응답이 이해하기 쉬웠나요?</p>
                    <StarRating totalStars={5} selectedStars={starsQ1} setSelectedStars={setStarsQ1} />

                    <p>2. 챗봇과의 대화가 자연스럽고 매끄러웠나요?</p>
                    <StarRating totalStars={5} selectedStars={starsQ2} setSelectedStars={setStarsQ2} />

                    <p>3. 챗봇을 통해 원하는 문제를 해결할 수 있었나요?</p>
                    <StarRating totalStars={5} selectedStars={starsQ3} setSelectedStars={setStarsQ3} />
                </div>
                <div>
                    <textarea
                        placeholder="피드백을 입력해 주세요."
                        className="feedback-text-main"
                        onChange={(e) => setText(e.target.value)}
                    />
                </div>
                <div className="feedback-modal-btn">
                    <button
                        className={`feedback-sendbtn ${isButtonActive ? 'active' : ''}`}
                        disabled={!isButtonActive}
                        onClick={handleSubmit}
                    >
                        제출하기
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Feedback;