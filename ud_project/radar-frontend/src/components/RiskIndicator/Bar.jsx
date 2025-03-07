import React from 'react';
import './Bar.scss';

const Bar = ({ level }) => {
    // const value = 4 + ((level * (39 - 4)) / 100);
    const value = parseInt(level) >= 3 ? parseInt(level) - 3 : parseInt(level);
    const position = value + '%';

    return (
        <div className="risk-level-container">
            <h1>Overall Risk Level</h1>
            <div className='risk-level-bar-container'>
                <div className="risk-level-bar one" style={{ background: 'linear-gradient(90deg, #FFE700 0%, #998B00 100%)' }}></div>
                <div className="risk-level-bar two" style={{ background: 'linear-gradient(90deg, #FF8C00 0%, #995400 100%)' }}></div>
                <div className="risk-level-bar three" style={{ background: 'linear-gradient(90deg, #F12D2D 0%, #8B1A1A 100%)' }}></div>
                <div className="risk-level-pointer" style={{ left: position }}></div>
            </div>
            <div className='risk-level-bar-label'>
                <h5 className='one'>Low</h5>
                <h5 className='two'>Medium</h5>
                <h5 className='three'>High</h5>
            </div>
        </div>
    );
}

export default Bar;
