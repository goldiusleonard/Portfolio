import React from 'react';
import ContentCategorySelection from '../../components/ContentCategorySelection';
import { RadarCarousel } from '../../components';
import AgentOutputParameters from '../../components/AgentOutputParameters';


function ReviewStatus() {
    return (
        <div className='review-body'>
            <section className='upper-section'>
                <div className=' card left'> <ContentCategorySelection  category='Scam' subcategory='Crypto Currency' topic='Bit Coin'/></div>
                <div className='card right '>
                    <p>Sample of Scanned Content Results</p>
                    <RadarCarousel/>
                </div>

            </section>
            <section className='lower-section'> <AgentOutputParameters /></section>

        </div>
    )
}

export default ReviewStatus
