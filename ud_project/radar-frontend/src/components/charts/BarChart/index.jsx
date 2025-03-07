import React from "react";
// import "./Leaderboard.scss";
import UserBar from "./UserBar";
import kathryn from "./../../../assets/images/sample_profile_image.png";

const LeaderBoard = ({ height, width, topRankers }) => {
	return (
		<div className="leader-board" style={{width: width, height: height }}>
			{topRankers?.map((user) => (
				<UserBar
					key={user.profile_id}
					id={user.profile_id}
					name={user.user_handle}
					imgSrc={user.creator_photo_link}
					percentage={user.ProfileThreatLevel}
					position={user.rank}
					height={user.ProfileThreatLevel}
				/>
			))}
		</div>
	);
}

export default LeaderBoard;
