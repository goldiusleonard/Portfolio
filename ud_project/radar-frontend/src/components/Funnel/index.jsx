import React from 'react';
import './Funnel.scss';
import LoaderAnimation from '../LoaderAnimation';
import useApiData from '../../hooks/useApiData';
import endpoints from '../../config/config.dev';
import arrowUp from '../../assets/icons/arrow_up.svg'
import arrowDown from '../../assets/icons/arrow_down.svg'

const FunnelContent = ({ handleClick, filterValue, data, loading }) => {
    const apiUrl = `${endpoints.getScannedDetails}?dummy_data=1`
    const { data: funnelData } = useApiData(apiUrl);

    const trendIndicator = title => {
        const item = funnelData?.data?.find(item => item.title === title);
        if (item?.trendIndicator) {
            const trendValue = parseFloat(item.trendIndicator);
            if (!isNaN(trendValue)) {
                return trendValue;
            }
        }
        return 0;
    };


    const renderFunnelContent = (title, filterKey) => (
        <div className={`funnel-component-content ${filterValue === filterKey ? 'active' : ''}`} onClick={() => handleClick(filterKey)}>
            <div className='funnel-title'>{title}</div>
            <div className='funnel-value'>{funnelData?.data?.find(item => item.title === title)?.value?.toLocaleString()}</div>
            {/* <div className='funnel-content-percentage'>{trendIndicator(title) > 0 ? trendIndicator(title).toFixed(1) : trendIndicator(title) < 0 ? Math.abs(trendIndicator(title).toFixed(1)) : trendIndicator(title)}%</div> */}
            <div className='funnel-content-percentage'>
                <span className='me-1'>{Math.abs(trendIndicator(title).toFixed(1))}%</span>
                <span>{
                    trendIndicator(title) > 0 ?
                        <img className='arrow-icon' src={arrowUp} alt="arrowUp" /> :
                        trendIndicator(title) < 0 ?
                            <img className='arrow-icon' src={arrowDown} alt="arrowDown" /> : ''}
                </span>
            </div>
            {/* <div className='funnel-content-trend'>
                {trendIndicator(title) > 0 ? 'More than' : trendIndicator(title) < 0 ? 'Less than' : 'Same as'} 7 days ago
            </div> */}
        </div>
    );

    return loading ? (
        <LoaderAnimation />
    ) : (
        <div className='h-100 funnel-component-wrapper'>
            <div className="funnel-component-title">Content Stream</div>
            <div className='funnel-component-contents'>
                <div className='funnel-component-content'>
                    <div className='funnel-title'>Total Scanned Content</div>
                    <div className='funnel-value'>{data?.scanned_content?.toLocaleString()}</div>
                    {/* <div className='funnel-content-percentage'>{funnelData?.subCategoryCount} Sub Category</div> */}
                    {/* <div className='funnel-content-percentage' style={{ marginTop: 0, marginBottom: '24px' }}>{funnelData?.topicCount} Topics</div> */}
                </div>
                {renderFunnelContent('Total AI Flagged', 'AI Flagged Content')}
                {renderFunnelContent('Reported', 'Reported')}
                {renderFunnelContent('Resolved', 'Resolved')}
            </div>
        </div>
    );
};

export default FunnelContent;
