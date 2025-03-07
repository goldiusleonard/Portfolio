import React from "react";
import sample_profile_image from "../../assets/images/sample_profile_image.png";

const PDFAccountDetailUserInfo = () => {
  return (
    <div className="account-details-stats">
      <div className="account-details-info-cards">
        <img src={sample_profile_image} alt="notification-profile" />
        <div className="account-details-info">
          <div className="account-details-info-title">#1 Jane Cooper</div>
          <div className="account-details-info-tags">
            <span>Scam</span>
            <span>Hate Speech</span>
            <span>3R</span>
          </div>
        </div>
      </div>
      <div className="account-details-cards">
        <div className="account-details-cards-title">Following</div>
        <div className="account-details-cards-content">9M</div>
      </div>
      <div className="account-details-cards">
        <div className="account-details-cards-title">Followers</div>
        <div className="account-details-cards-content">908</div>
      </div>
      <div className="account-details-cards">
        <div className="account-details-cards-title">Posts</div>
        <div className="account-details-cards-content">789</div>
      </div>
      <div className="account-details-cards">
        <div className="account-details-cards-title">Engagement</div>
        <div className="account-details-cards-content">85%</div>
      </div>
      <div className="account-details-cards">
        <div className="account-details-cards-title">Last Post Date</div>
        <div className="account-details-cards-content">30 May 2024</div>
      </div>
    </div>
  );
};

export default PDFAccountDetailUserInfo;
