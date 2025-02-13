import '../styles/ErrorBoundary.css'
import { Component } from 'react';

class ErrorBoundary extends Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true };
    }

    componentDidCatch(error, errorInfo) {
        console.error("Error caught by ErrorBoundary:", error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className='errorboundary-overlay'>
                    <div className='errorboundary-modal'>
                        <h2>
                            404
                        </h2>
                        <span className='errorboundary--span1'>
                            페이지를 찾을 수 없습니다.
                        </span>
                        <span className='errorboundary--span2'>
                            요청하신 페이지가 삭제되었거나 잘못된 경로입니다.
                        </span>
                        <button
                            className='errorboundary--home-btn'
                            onClick={() => window.location.reload()}
                        >
                            홈으로 돌아가기
                        </button>
                    </div>
                    <div className='errorboundary-img'>
                        <img src='/images/home.png' alt='서집사.png' />
                        <span>서집사</span>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}

export default ErrorBoundary;