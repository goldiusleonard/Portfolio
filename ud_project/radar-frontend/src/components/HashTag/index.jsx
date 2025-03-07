import React, { useState, useEffect, useRef } from 'react';
// import './hashTag.scss';

const HashTag = ({ hashtag, hashTags, handleHashTagChange }) => {
    const [startIndex, setStartIndex] = useState(0);
    const [visibleCount, setVisibleCount] = useState(10); // Default maximum visible count
    const containerRef = useRef(null);

    useEffect(() => {
        const updateVisibleCount = () => {
            if (containerRef.current) {
                const containerWidth = containerRef.current.offsetWidth - 40; // Adjust for nav buttons' width
                const buttonWidths = Array.from(containerRef.current.querySelectorAll('.hashTag-btn'))
                    .map(button => button.offsetWidth);
                let totalWidth = 0;
                let count = 0;
                for (const width of buttonWidths) {
                    if (totalWidth + width > containerWidth) break;
                    totalWidth += width;
                    count++;
                }
                setVisibleCount(count < 10 ? count : 10);
            }
        };

        updateVisibleCount();
        window.addEventListener('resize', updateVisibleCount);

        return () => {
            window.removeEventListener('resize', updateVisibleCount);
        };
    }, [hashTags]);

    const handleNext = () => {
        setStartIndex((prevIndex) => (prevIndex + visibleCount) % hashTags.length);
    };

    const handlePrevious = () => {
        setStartIndex((prevIndex) => (prevIndex - visibleCount + hashTags.length) % hashTags.length);
    };

    if (!hashTags || hashTags.length === 0) return null;

    return (
        <div className="hashTag-wrapper">
                <button 
                    className="nav-btn" 
                    onClick={handlePrevious}
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 18 18" fill="none">
                        <path d="M12 15.75L6 9L12 2.25" stroke="#8A8A8A" strokeWidth="0.75"/>
                    </svg>
                </button>

            <div className="hashTag-container" ref={containerRef}>
                {hashTags.slice(startIndex, startIndex + visibleCount).map((item, index) =>
                    <button
                        className={`hashTag-btn ${'#'+hashtag === item ? 'active' : ''}`}
                        key={item + index}
                        onClick={() => handleHashTagChange(item)}
                        style={{ opacity: !hashtag || `#${hashtag}` === item ? 1 : 0.5 }}
                    >
                        {item}
                    </button>
                )}
                {/* To handle the case when the visible count exceeds the available tags */}
                {startIndex + visibleCount > hashTags.length && hashTags.slice(0, (startIndex + visibleCount) % hashTags.length).map((item, index) =>
                    <button
                        className={`hashTag-btn ${'#'+hashtag === item ? 'active' : ''}`}
                        key={item + index + hashTags.length} // Ensure unique key
                        onClick={() => handleHashTagChange(item)}
                        style={{ opacity: !hashtag || `#${hashtag}` === item ? 1 : 0.5 }}
                    >
                        {item}
                    </button>
                )}
            </div>

                <button 
                    className="nav-btn" 
                    onClick={handleNext}
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 18 18" fill="none">
                        <path d="M6 2.25L12 9L6 15.75" stroke="#8A8A8A" strokeWidth="0.75"/>
                    </svg>
                </button>
        </div>
    );
};

export default HashTag;
