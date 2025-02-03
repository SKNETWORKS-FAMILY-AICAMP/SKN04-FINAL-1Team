import '../styles/LoadingPage.css'

const LoadingPage = ({ isOpen, closeModal }) => {

    return (
        <div className="overlay">
            <div className="loading-modal">
                <img src='/images/Spinner.gif' alt='로딩' />
                <h2>Loading....</h2>
                <span>
                    부동산 꿀팁:알고 계셨나요?
                    서울에서 가장 비싼 곳은 강남입니다~
                </span>
            </div>
        </div>
    )
}

export default LoadingPage;
