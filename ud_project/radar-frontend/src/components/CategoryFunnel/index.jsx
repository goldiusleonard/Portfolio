import React from 'react';
import './Funnel.scss';
import LoaderAnimation from '../LoaderAnimation';
import useApiData from '../../hooks/useApiData';
import endpoints from '../../config/config.dev';
import arrowUp from '../../assets/icons/arrow_up.svg'
import arrowDown from '../../assets/icons/arrow_down.svg'

const dummy= [63.4,21.5,7.3]

const CategoryFunnel = ({ handleClick, filterValue, data, loading }) => {
    const apiUrl = `${endpoints.getScannedDetails}?'//day_difference=7` 
    const { data: funnelData } = useApiData(apiUrl);


    // const trendIndicator = title => {
    //     const item = funnelData?.data?.find(item => item.title === title);
    //     if (item?.trendIndicator) {
    //         const trendValue = parseFloat(item.trendIndicator);
    //         if (!isNaN(trendValue)) {
    //             return trendValue;
    //         }
    //     }
    //     return 0;
    // };

    const trendIndicator = index=>  dummy[index]
     

    const renderFunnelContent = (title, filterKey,index) => (
        <div className={`funnel-component-content ${filterValue === filterKey ? 'active' : ''}`}>
            <div className='funnel-title'>{title}</div>
            <div className='funnel-value'>{funnelData?.data?.find(item => item.title === title)?.value?.toLocaleString()}</div>
            {/* <div className='funnel-content-percentage'>{trendIndicator(title) > 0 ? trendIndicator(title).toFixed(1) : trendIndicator(title) < 0 ? Math.abs(trendIndicator(title).toFixed(1)) : trendIndicator(title)}%</div> */}
            <div className='funnel-content-percentage'>
                {/* <p>{Math.abs(trendIndicator(title).toFixed(1))}%</p> */}
                <p>{Math.abs(trendIndicator(index).toFixed(1))}%</p>
                {
                    trendIndicator(title) > 0 ?
                        <img className='arrow-icon' src={arrowUp} alt="arrowUp" /> :
                        trendIndicator(title) < 0 ?
                            <img className='arrow-icon' src={arrowDown} alt="arrowDown" /> : ''
                }
            </div>
            {/* <div className='funnel-content-trend'>
                {trendIndicator(title) > 0 ? 'More than' : trendIndicator(title) < 0 ? 'Less than' : 'Same as'} 7 days ago
            </div> */}
        </div>
    );

    return loading ? (
        <LoaderAnimation />
    ) : (
        <div className='h-100 funnel-wrapper'>
            <div className='h-100' style={{ marginTop: '20px' }}>
                <div className='funnel-component-contents'>
                    {renderFunnelContent('Total AI Flagged', 'AI Flagged Content',0)}
                    {renderFunnelContent('Reported', 'Reported',1)}
                    {renderFunnelContent('Resolved', 'Resolved',2)}
                </div>
            </div>
        </div>
    );
};

export default CategoryFunnel;
