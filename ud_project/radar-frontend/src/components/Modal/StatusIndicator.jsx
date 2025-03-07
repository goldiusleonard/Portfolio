import React from "react";
import "./StatusIndicator.scss"; // Import the SCSS file for styles

const data = {
	id: "FB240228CBMM00013",
	time: "16:29 11/10/24",
	label: "Crypto Curr...",
	flagged: "AI Flagged",
	level: "High",
};

const StatusIndicator = () => {
	return (
		<div className="status-container">
			<span className="status-id">FB240228CBMM00013</span>
			<span className="status-time">16:29 11/10/24</span>
			<span className="close-button">×</span>
			<span className="status-label">Crypto Curr...</span>
			<span className="status-flagged">AI Flagged</span>
			<button className="status-level">High</button>

			{/* {Object.keys(data).map((key) => (
				<span className={`status-${key}`}>{data[key]}</span>
			))}
		 */}
		</div>
	);
};

export default StatusIndicator;
