import React from 'react';
import endpoints from '../../config/config.dev';
import useApiData from '../../hooks/useApiData';
import LoaderAnimation from '../LoaderAnimation';

const titleToChoose = {
    'Total AI Flagged': 'AI Flagged Content',
    'Reported': 'Reported',
    'Resolved': 'Resolved',
}

function TotalScannedContent({ activeTitle }) {
    const apiUrl = `${endpoints.getScannedDetails}?dummy_data=1` 
    const { data, loadingData } = useApiData(apiUrl);
    const activeIndex = data?.data?.findIndex(item => titleToChoose[item.title] === activeTitle)
    const formatValue=data?.data[activeIndex]?.value?.toLocaleString();
    const trandIndicatorText = data?.data[activeIndex]?.trendIndicator>0?'More than last week':'Less than 7 days ago'
   const withoutOperator = data?.data[activeIndex]?.trendIndicator.toString().replace(/[-+]/g, '')+'%';
    
    if(!data) return <></>

    return (
        <div className='tsc'>
            {loadingData ? <LoaderAnimation /> : <> <h3 className='tsc-title'>
                {data?.data[activeIndex]?.title}
            </h3>
                <div className='tsc-section'>
                    <div>
                        <p className='tsc-section-title'>{formatValue}</p>
                        <p className='tsc-section-subtitle'>{data?.subCategoryCount} Sub-Category Test</p>
                        <p className='tsc-section-subtitle'>{data?.topicCount} Topic</p>
                    </div>
                    <div className='tsc-section-right'>
                        <p className='tsc-section-right-text'>{ withoutOperator}</p>
                        <p className='tsc-section-subtitle'>{trandIndicatorText}</p>
                    </div>

                </div>
                <div className='tsc-section'>
                    {data.data.map((item, index) => (
                        <Card key={index} {...item} index={index} active={activeIndex === index} />
                    ))}
                </div>
            </>}
        </div>
    )
}

export default TotalScannedContent



const Card = ({ title, value, trendIndicator, active }) => {
    const conatinerClass = active ? 'card-active' : 'card-container'
// const formatValue= formatNumber(value)
const formatValue = value.toLocaleString();
const trendIndicatorText = trendIndicator>0?'More than last week':'Less than 7 days ago'
const withoutOperator = trendIndicator.toString().replace(/[-+%]/g, '')+'%';
    return (
        <div className={conatinerClass} >

            <h5 className='card-title'>{title}</h5>
            <div className='card-content'>
            <p className='card-value'>{formatValue}</p>
            <div>
                <p className='card-text'>{withoutOperator}</p>
                <p className='card-subtext'>{trendIndicatorText}</p>
            </div>
            </div>
        </div>
    )
}
