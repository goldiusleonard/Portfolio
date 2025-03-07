import React from 'react';
import sample_profile_image from '../../assets/images/avatar.png'
// import './watchlistProfile.scss'
import LoaderAnimation from '../LoaderAnimation';
import formatNumber from "../../Util/NumberFormat";
import { useNavigate } from 'react-router-dom';

const categories = [
    'Hate Speech',
    'scam',
    'racism',
    'Sexual Harassment',
    'Violence',
]

const WatchListProfile = ({ data, loading }) => {
    const navigate = useNavigate();

    return (
      <div className="watchlistProfile-container h-100">
        {loading ? (
          <LoaderAnimation />
        ) : (
          <>
            <p className="seondary-title pb-4">Posted By</p>
            <div className="body">
              <div
                className="watchlistProfile-img"
                style={{ cursor: "pointer" }}
                onClick={() =>
                  navigate("/watch-list/creator", {
                    state: {
                      profile_id: data?.creator_id,
                      user_handle: data?.creator_name,
                    },
                  })
                }
              >
                <img
                  src={
                    !data?.creator_img ||
                    data?.creator_img.includes("https://p16-sign")
                      ? sample_profile_image
                      : data?.creator_img
                  }
                  alt="profile"
                />
              </div>

              <div className="sec">
                <span className="text-capitalize">{data?.creator_name}</span>
                <div className="py-2 gap-2 d-flex w-100">
                  {categories.slice(0, 3).map((item, index) => (
                    <div
                      className="bordered-container align-items-center d-flex"
                      key={index}
                    >
                      {item}
                    </div>
                  ))}
                  {categories.length > 3 && (
                    <div className="bordered-container hover-btn d-flex align-items-center justify-content-center">
                      <div className="trigger ">+{categories.length - 3}</div>
                      <div className="dropdown-content">
                        {categories.slice(3).map((item, index) => (
                          <div className="tag" key={index}>
                            {item}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className="right-side-align ">
                <p className="tertiary-title pb-2">Engagement</p>
                <p>75%</p>
              </div>

              {/* <Button className='btn' color='primary'>Under Watchlist</Button> */}
            </div>
            <div className="watchlistProfile-social-container">
              <div className="watchlistProfile-social sec">
                <span>Following</span>
                <span>{formatNumber(data?.creator_followings)}</span>
              </div>
              <div className="watchlistProfile-social sec">
                <span>Followers</span>
                <span>{formatNumber(data?.creator_followers)}</span>
              </div>
              <div className="watchlistProfile-social sec">
                <span>Posts</span>
                <span>{formatNumber(data?.creator_post)}</span>
              </div>
            </div>
          </>
        )}
      </div>
    );
};

export default WatchListProfile;
