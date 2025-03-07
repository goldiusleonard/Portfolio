import React from "react";
import "./UserCard.scss";
import manager from './../../assets/images/officer-pp.jpeg'
import officer from './../../assets/images/manager_pp.jpeg'
// import smallLogo from './../../assets/images/RR_logo1.png'
import smallLogo from './../../assets/images/RR_logo3.png'
import logo from './../../assets/images/RR_logo2.png'
import officerIcon from './../../assets/icons/officerIcon.svg'
import managerIcon from './../../assets/icons/managerIcon.svg'

const AvatarText = ({name, color, icon}) => {
	return (
		<div className="avt-text" style={{ backgroundColor: color }}>
			{name}
			<img className="align-img" src={icon} alt="UserIcon" />
		</div>
	)
}

const UserCard = ({ isOpen, isOfficer,name }) => {
	const initials=getFirstLetters(name)
	return (
		<>
		<div className="app-logo p-2">
				<img className={`w-100 small ${isOpen ? 'visible' : 'hidden'}`} src={smallLogo} alt="App Logo"/>
				<img className={`${isOpen ? 'hidden' : 'visible'}`} src={logo} alt="App Logo"/>
			</div>
		<div className="user-profile">
			<div className="avatar">
				{/* <img src={isOfficer ? officer : manager } alt="user"/> */}
				{isOfficer ? <AvatarText name={initials} color="#2d3e53bf" icon={officerIcon} /> : <AvatarText name={initials} color="#000" icon={managerIcon} /> } 
			</div>
			{!isOpen && (
				<div className="user-details">
					<div className="role">{isOfficer ? "OFFICER" : "SENIOR LEADER"}</div>
					<div className="name">{name}</div>
				</div>
			)}
		</div>
		</>
	);
};

export default UserCard;

function getFirstLetters(name) {
	if(!name) return '';
	const words = name.split(/[\s.]+/); // Split on spaces and dots
	const initials = words.map(word => word[0].toUpperCase()).join('');
	return initials;
  }
  