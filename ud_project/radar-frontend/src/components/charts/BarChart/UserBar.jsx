import React from "react";
import { useNavigate } from 'react-router-dom';
import { useGlobalData } from "../../../App";

const UserBar = ({ id, name, percentage, position, height, imgSrc }) => {
	const navigate = useNavigate();
	const { setCreatorUsername } = useGlobalData()

	const goToCreator = () => {
		setCreatorUsername(name) // TODO:do not delete
		// we only need userName as it is unique to fetch heatmap data; id will be redundant later.
		navigate('/watch-list/creator', { state: { profile_id: id, user_handle: name } })
	}

	const threatLevelformat = (number) => {
		// const roundedValue = Math.round(number.ProfileThreatLevel);
		const rounded = Math.round(number * 10) / 10;
		const roundedValue =  rounded % 1 === 0 ? rounded.toFixed(0) : rounded.toFixed(1);
		return `${roundedValue}%`;
	};

	return (
		<div className="user-bar">
			<div className="user" style={{ height: height + '%' }}>
				<div className={`user-image bar-width `}>
					<div className={`user-details ${position < 10 ? 'change-position' : ''}`}>{position}</div>
				</div>
				<div className="prof-wrap">
					<img src={imgSrc} alt={name} className="user-image" onClick={goToCreator} />
					<div className="user-name">{name}</div>
					<div className="user-percentage">{threatLevelformat(percentage)}</div>
				</div>
			</div>
		</div>
	);
}

export default UserBar;
