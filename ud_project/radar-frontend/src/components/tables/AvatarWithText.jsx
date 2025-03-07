import React from 'react';
import avatar from '../../assets/images/avatar.png';


export const AvatarWithText = ({ creator_photo_link, user_handle, profile_picture_link }) => {
  const avatarUrl =
    (profile_picture_link?.includes("https://p16-sign") ||
      creator_photo_link?.includes("https://p16-sign"))
      ? avatar
      : (profile_picture_link || creator_photo_link || avatar);
  
  return (
    <div className="avatar-row">
      <img className="avatar" src={avatarUrl} alt='creator image' width='32' height={30} />
      <span className="avatar-text">{user_handle}</span>
    </div>
  )
};

