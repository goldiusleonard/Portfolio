import React from 'react';
import './scrollableList.scss';
import useApiData from '../../hooks/useApiData';
import endpoints from '../../config/config.dev';
import { avatar } from '../../assets/images';
import LoaderAnimation from '../LoaderAnimation';
import { useNavigate } from 'react-router-dom';



const WatchlistRankingList = () => {
    const { data, loadingData } = useApiData(endpoints.getPostContents);
    const navigate = useNavigate()
    const dateFormatter = (date) => {
        const d = new Date(date);

        const options = {
            hour: 'numeric',
            minute: 'numeric',
            hour12: true
        };

        return {
            date: `${d.getDate()} ${d.toLocaleString('default', { month: 'short' })}, ${d.getFullYear()}`,
            time: d.toLocaleTimeString('en-US', options).toLowerCase()
        };
    };

    const handleContentClick = (video_id) => {
        navigate('/category-details/content-details', { state: { video_id } });
    }

    const handleProfileClick = (user_handle) => {
        navigate('/watch-list/creator', { state: { user_handle } }); // all row.data is passed for now we might need to pass only the id or userName 
    };

    return (
        <div className='watchlist-list'>
            <h1>Latest Content</h1>
            <div className='watchlist-scroll'>
                {loadingData ? <LoaderAnimation /> : data?.map((data, index) => {
                    const date = dateFormatter(data.video_posted_timestamp);
                    return (

                        <div className='watchlist-content' key={data.video_id}>
                            <div className='watchlist-header-section'>
                                <div className='watchlist-list-header' style={{ cursor: 'pointer' }} onClick={() => handleProfileClick(data?.user_handle)}>
                                    <img src={!data.creator_photo_link || data.creator_photo_link.includes("https://p16-sign") ? avatar : data.creator_photo_link} alt="profile pic" />
                                    <h4>{data.user_handle}</h4>
                                </div>
                                <div className='watchlist-list-dateTime'>
                                    <h5>{date.date}</h5>
                                    <h5>{date.time}</h5>
                                </div>
                            </div>
                            <div className="watchlist-post-content" style={{ cursor: 'pointer' }} onClick={() => handleContentClick(data?.video_id)} >
                                <h4>{data.video_description}</h4>
                            </div>
                            <div className='watchlist-video'>
                                <a href={data.video_url} target="_blank" rel="noopener noreferrer">
                                    {/* {data.video_url} */}
                                    Download Content
                                </a>
                                <CustomBox riskRate={data.risk_status} />
                            </div>
                        </div>
                    )
                }
                )}
            </div>
        </div>
    )
};

const CustomBox = ({ riskRate }) => {
    const color = riskRate?.toLowerCase() === 'low' ? '#FFE700' : riskRate?.toLowerCase() === 'medium' ? '#FF8C00' : '#F12D2D';
    const borderColor = riskRate?.toLowerCase() === 'low' ? '#FFE700' : riskRate?.toLowerCase() === 'medium' ? '#FF8C00' : '#F12D2D';
    const backgroundColor = riskRate?.toLowerCase() === 'low' ? "rgba(255, 231, 0, 0.20) " : riskRate?.TolowerCase === 'medium' ? "rgba(255, 140, 0, 0.20) " : 'rgba(241, 45, 45, 0.20)';

    return (
        <button className='table-button' style={{ color, borderColor, backgroundColor, width: 122, textTransform: 'capitalize' }}>{riskRate}</button>
    );
};

export default WatchlistRankingList;