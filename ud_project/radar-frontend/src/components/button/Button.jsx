import React from "react";
// import "./Button.scss";

const Button = ({ text, variant, onClick , className, disable}) => {
	return (
		<button className={`custom-button ${variant} ${disable && 'disable'} ${className}`} onClick={onClick} disabled={disable}>
			{text}
		</button>
	);
};

export default Button;
