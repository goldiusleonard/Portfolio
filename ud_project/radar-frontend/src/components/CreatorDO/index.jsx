import React from 'react'
import { useNavigate } from "react-router-dom";
import data from './categoryDO.json'
import useApiData from '../../hooks/useApiData';
import endpoints from '../../config/config.dev';
import LoaderAnimation from '../LoaderAnimation';
import avatarImage from '../../assets/icons/user.svg'

const CreatorDO = ({ creatorName }) => {
  const apiEndpoint = `${endpoints.getProfileDO}?userName=${creatorName}`
  const { loadingData } = useApiData(apiEndpoint)
  const navigate = useNavigate();

  const goToCreator = (id, name) => {
    navigate('/watch-list/creator', { state: { profile_id: id, user_handle: name } })
  }

  const isMoreItems = data?.length === 5;
  const noSimilar = data?.length === 1;



  const Tooltip = ({ text }) => {
    return (
      <div className="tooltip-text">
        <p>Similar By</p>
        <p className='desc'>{text}</p>
      </div>
    );
  };

  return (
    <div className='p-3 do-container'>
      {loadingData ? <LoaderAnimation /> : (
        <div className='do-parent'>
          {noSimilar ?
            (<div className='noSimilar-msg'>
              No similar creators found
            </div>)
            :
            (<ul className={`similar-list ${isMoreItems ? 'normal-list' : 'limited-list'}`}>
              {data?.slice(0, 5).map((item, index) => {
                return (
                  <li
                    key={item.id}
                    className={`creator-card $middle-card'}`}
                    // style={itemStyles[index]}
                    onClick={() => goToCreator(item.id, item.label)}
                  >
                    <div className='d-flex align-items-center'>
                      <img src={item.picture === "" ? avatarImage : item.picture} className='prof-image' alt={item.name.substring(0, 5)} />
                      <p className='prof-label'>{item.name}</p>
                    </div>
                    <p className='prof-percentage'>{item.percentage?.toFixed(1)}%</p>
                    { item.connection && <Tooltip text={item.connection} />}
                  </li>
                )
              })
              }
            </ul>)}
        </div>
      )
      }
    </div>
  )
}

export default CreatorDO
