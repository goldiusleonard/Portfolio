import React from 'react';
import './topCard.scss'
import { Button } from 'reactstrap';
import { avatar } from '../../assets/images'
import '../Modal/modal.scss'
import moment from 'moment';
import formatNumber from '../../Util/NumberFormat';
import TagList from "./TagList";


const HeatMapTopCard = ({ data, toggle }) => {
    return (
        <div className="heatmap-top-card">
            <div className='heatmap-profile'>
                <img style={{ cursor: 'pointer' }} onClick={(event) => {
                    event.preventDefault();
                    event.stopPropagation();
                    window.open(`https://www.tiktok.com/@${data[0]?.user_handle}`, '_blank', 'noopener,noreferrer');
                }} src={!data[0]?.creator_photo_link || data[0]?.creator_photo_link.includes("https://p16-sign") ? avatar : data[0]?.creator_photo_link} alt='profile' />
                <div className='content-id-container'>
                    <p className='content-id text-capitalize' style={{ cursor: 'pointer' }} onClick={(event) => {
                        event.preventDefault();
                        event.stopPropagation();
                        window.open(`https://www.tiktok.com/@${data[0]?.user_handle}`, '_blank', 'noopener,noreferrer');
                    }}>{data[0]?.user_handle}</p>
                    <TagList
                        data={[
                            'Scam',
                            'Hate Speech',
                            '3R',
                            'Category #1',
                            'Category #2',
                            'Category #3',
                            'Category #4'
                        ]}
                    />
                    <Button className='w-100 text-black' onClick={toggle}>Report</Button>
                </div>
            </div>
            <div className='content-details-cards'>
                <div className='content-details-cards-title'>Following</div>
                <div className='content-details-cards-content'>{formatNumber(data[0]?.user_following_count)}</div>
            </div>
            <div className='content-details-cards'>
                <div className='content-details-cards-title'>Followers</div>
                <div className='content-details-cards-content'>{formatNumber(data[0]?.user_followers_count)}</div>
            </div>
            <div className='content-details-cards'>
                <div className='content-details-cards-title'>Posts</div>
                <div className='content-details-cards-content'>{data[0]?.user_total_videos?.toLocaleString()}</div>
            </div>
            <div className='content-details-cards'>
                <div className='content-details-cards-title'>Engagement</div>
                <div className='content-details-cards-content'>{data[0]?.ProfileEngagement_score?.toFixed(1)}%</div>
            </div>
            <div className='content-details-cards'>
                <div className='content-details-cards-title'>Last Post</div>
                <div className='content-details-cards-content'>{moment(data[0]?.LatestVideoPostedDate).format('D MMM YY')}</div>
            </div>
        </div>
    );
};

export default HeatMapTopCard;
