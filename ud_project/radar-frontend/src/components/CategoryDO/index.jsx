import React from 'react'
import { useLocation } from 'react-router-dom';
import useApiData from '../../hooks/useApiData'
import endpoints from '../../config/config.dev';
import LoaderAnimation from '../LoaderAnimation';

const CategoryDO = () => {
  const location = useLocation()
  const { video_id: contentID } = location.state ? location.state : [];
  const apiEndpoint = `${endpoints.getCategoryDO}?video_id=${contentID}`
  const { data, loadingData } = useApiData(apiEndpoint)

  const noSimilar = !data?.nodes || data?.nodes?.length === 0;

  return (
    <div className='do-container p-3'>
      {loadingData ? (
        <LoaderAnimation />
      ) : (
        <div className='do-parent-cat'>
          {noSimilar ?
            (<div className='noSimilar-msg'>
              No similar keywords found
            </div>)
            :
            (<ul className={`similar-list`}>
              {/* {data?.nodes?.slice(0, 6).map((item, index) => {
                return (
                    <li key={item.id} 
                      className={`keyword-card`}
                    >
                      <p className='keyword-label'>{item.label}</p>
                    </li>
                )
              })
            } */}
              {[...new Map(data?.nodes?.slice(0, 6).map((item) => [item.label, item])).values()].map((item, index) => {
                return (
                  <li key={item.id} className={`keyword-card`}>
                    <p className='keyword-label'>{item.label}</p>
                  </li>
                );
              })}
            </ul>)}
        </div>
      )}
    </div>
  )
}

export default CategoryDO
