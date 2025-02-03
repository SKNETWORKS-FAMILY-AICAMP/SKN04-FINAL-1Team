import { useState, useRef, useEffect } from 'react';
import ReactDOM from 'react-dom';
import '../styles/Tooltip.css';

const Tooltip = ({ text, tooltipText }) => {
    const [visible, setVisible] = useState(false);
    const tooltipRef = useRef(null);
    const iconRef = useRef(null);
    const [position, setPosition] = useState({ top: 0, left: 0 });

    useEffect(() => {
        if (visible && iconRef.current && tooltipRef.current) {
            const iconRect = iconRef.current.getBoundingClientRect();
            const tooltipRect = tooltipRef.current.getBoundingClientRect();

            const top = iconRect.top - tooltipRect.height - 8;
            const left = iconRect.left + (iconRect.width / 2) - (tooltipRect.width / 2);

            setPosition({
                top: top < 0 ? iconRect.bottom + 8 : top,
                left: left < 0 ? 8 : left,
            });
        }
    }, [visible]);

    const tooltipElement = visible ? (
        ReactDOM.createPortal(
            <div
                className="tooltip-text"
                ref={tooltipRef}
                style={{
                    top: `${position.top}px`,
                    left: `${position.left}px`,
                }}
            >
                {tooltipText}
            </div>,
            document.body
        )
    ) : null;

    return (
        <div
            className="tooltip-container"
            onMouseEnter={() => setVisible(true)}
            onMouseLeave={() => setVisible(false)}
            style={{ position: 'relative', display: 'inline-block' }}
        >
            <span className="tooltip-icon" ref={iconRef}>
                {text}
            </span>
            {tooltipElement}
        </div>
    );
};

export default Tooltip;
