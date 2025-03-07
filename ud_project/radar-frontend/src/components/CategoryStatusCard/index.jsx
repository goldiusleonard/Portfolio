import React from 'react'
// import './CategoryStatusCard.scss'
import { Category } from '../OriginalContent'
import endpoints from '../../config/config.dev';
import useApiData from '../../hooks/useApiData';
import LoaderAnimation from '../LoaderAnimation';
import arrowUp from '../../assets/icons/arrow_up.svg'
import arrowDown from '../../assets/icons/arrow_down.svg'

const CategoryStatusCards = ({ subCategoryRoute, subCategoryTopic }) => {

  const apiEndpoint = `${endpoints.getScannedDetails}?category=hate%20speech${subCategoryRoute ? `&subCategory=${subCategoryRoute}` : ''}${subCategoryTopic ? `&topic=${subCategoryTopic}` : ''}`;
  const { data, loadingData } = useApiData(apiEndpoint);
  const trendIndicator = item => {
    if (item?.trendIndicator) {
      const trendValue = parseFloat(item.trendIndicator);
      if (!isNaN(trendValue)) {
        return trendValue;
      }
    }
    return 0;
  };

  return (
    <div className='category-status-wrapper'>
      <Category subCategoryRoute={subCategoryRoute} subCategoryTopic={subCategoryTopic} />
      <div className='category-status-container'>
        {loadingData &&
          <LoaderAnimation />
        }
        {data?.data?.map((item) => {
          return (
            <div className='category-status' key={item?.title}>
              <div className='category-status-title'>{item.title === 'Total AI Flagged' ? 'AI Flagged' : item?.title} Content</div>
              <div className='category-status-number'>{item?.value?.toLocaleString()}</div>
              <div className='category-status-percentage'>
                {Math.abs(trendIndicator(item).toFixed(1))}%
                <div>
                  <span className='mx-1'>
                    {trendIndicator(item) > 0 ?
                      <img src={arrowUp} alt='arrowUp'/> :
                      trendIndicator(item) < 0 ?
                        <img src={arrowDown} alt='arrowDown'/> : ''}
                  </span>
                </div>
                {/* <div>{trendIndicator(item) > 0 ? trendIndicator(item).toFixed(1) : trendIndicator(item) < 0 ? Math.abs(trendIndicator(item).toFixed(1)) : trendIndicator(item)}%</div> */}
                {/* <div>{item?.trendIndicator > 0 ? 'More than' : item?.trendIndicator < 0 ? 'Less than' : 'Same as'} 7 days ago</div> */}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}


export default CategoryStatusCards