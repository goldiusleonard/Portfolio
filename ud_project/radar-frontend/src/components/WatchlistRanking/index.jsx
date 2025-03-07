import './WatchListRanking.scss';
import {useNavigate} from "react-router-dom";
import { useGlobalData } from "../../App";
import { avatar } from '../../assets/images';
import moment from 'moment';
import formatNumber from '../../Util/NumberFormat';

const WatchListRanking = ({topRankers}) => {
    const navigate = useNavigate();
    const { setCreatorUsername } = useGlobalData()
    const goToCreator = (name,id) => {
		setCreatorUsername(name) 
		navigate('/watch-list/creator', { state: { profile_id: id, user_handle: name } })
    }
    
return( 
        <div className='watchlist-ranking-container'>
            {topRankers?.map((user,index) =>
                <div className='watchlist-ranking' key={index} onClick={() => goToCreator(user.profileData[0].user_handle,user.profileData[0].profile_id)}>
                    <div className='ranking'>#{index+1}</div>
                    <div className='image_name'>
                        <img src=    {!user.profileData[0].creator_photo_link || user.profileData[0].creator_photo_link.includes("https://p16-sign") ? avatar : user.profileData[0].creator_photo_link} alt='profile' />
                        <h4>{user.profileData[0].user_handle}</h4>
                    </div>
                    <div className='following'>
                        <h4>Following</h4>
                        {/* <h5>{moment(user?.profileData[0]?.LatestVideoPostedDate).format('D MMM YY')}</h5> */}
                        <h5>{formatNumber(user.profileData[0].user_following_count)}</h5>
                    </div>
                    <div className='followers'>
                        <h4>Followers</h4>
                        <h5>{formatNumber(user.profileData[0].user_followers_count)}</h5>
                    </div>
                    <div className='posts'>
                        <h4>Posts</h4>
                        {/* <h5>{user?.profileData[0]?.TotalEngagementRisk?.toFixed(1)}</h5> */}
                        <h5>{user.profileData[0].user_total_videos?.toLocaleString()}</h5>
                    </div>
                    <div className='posts'>
                        <h4>Engagement</h4>
                        {/* <h5>{user?.profileData[0]?.TotalEngagementRisk?.toFixed(1)}</h5> */}
                        <h5>{user.profileData[0]?.ProfileEngagement_score?.toFixed(1)}%</h5>
                    </div>
                    <div className='following'>
                        <h4>Last Post</h4>
                        <h5>{moment(user?.profileData[0]?.LatestVideoPostedDate).format('D MMM YY')}</h5>
                    </div>
                    {/* <div className='threat-level'>
                        <h4>Threat Level</h4>
                        <h5>{user.profileData[0]?.ProfileThreatLevel.toFixed(1)}%</h5>
                    </div> */}
                </div>
            )}
        </div>
    
)}
export default WatchListRanking;