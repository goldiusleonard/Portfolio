// src/Collapse.js
import React, { useState } from "react";
import "./Collapse.scss";
import { DownArrowIcon, UpArrowIcon } from "../../assets/icons";


const Collapse = ({ title, description, children, expandableButton=true }) => {
	const [isVisible, setIsVisible] = useState(false);

	const toggleVisibility = () => {
		setIsVisible(!isVisible);
	};

	return (
		<div className="collapse-container">
			{isVisible && expandableButton ? (
				<div className="collapse-button-wrapper" onClick={toggleVisibility}>
					<div className={`collapse-button-visible`}>
						<span>{title}</span>
						<div className="arrow-down">{<UpArrowIcon fill="#A9A9A9" />}</div>
					</div>
				</div>
			) : (
				<>
					{isVisible ? (
						<div className={`collapse-button`} onClick={toggleVisibility}>
							<span>{title}</span>
							<UpArrowIcon fill="#A9A9A9" />
						</div>
					) : (
						<div className={`collapse-button`} onClick={toggleVisibility}>
							<span>{title}</span>
							<DownArrowIcon fill="#A9A9A9" />
						</div>
					)}
				</>
			)}

			<div className={`collapse-content ${isVisible ? "visible" : ""}`}>
				{children}
			</div>
		</div>
	);
};

export default Collapse;
