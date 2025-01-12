import '../styles/Favorite.css';

const Favorite = ({ isOpen, closeModal }) => {
    if (!isOpen) return null;

    // 로컬 스토리지에서 즐겨찾기 불러오기
    const savedFavorites = JSON.parse(localStorage.getItem('favorites')) || [];

    const handleOverlayClick = (e) => {
        if (e.target.classList.contains('favorite-overlay')) {
            closeModal();
        }
    };

    return (
        <div className='favorite-overlay' onClick={handleOverlayClick}>
            <div className='favorite-modal' onClick={(e) => e.stopPropagation()}>
                <div className='favorite-header'>
                    <h3>즐겨찾기</h3>
                    <button className="favorite-closebtn" onClick={closeModal}>
                        &times;
                    </button>
                </div>
                <div className='favorite-content'>
                    {savedFavorites.length === 0 ? (
                        <p>즐겨찾기가 없습니다.</p>
                    ) : (
                        savedFavorites.map((msg, index) => (
                            <div key={index} className="favorite-item">
                                {msg}
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

export default Favorite;
