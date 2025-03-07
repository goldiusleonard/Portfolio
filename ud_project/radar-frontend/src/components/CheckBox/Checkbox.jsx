import React from "react";
import "./Checkbox.scss";

const Checkbox = ({ id, checked, name, value, onChange, label }) => {
	return (
		<div className="checkbox-wrapper-46">
			<input
				className="inp-cbx"
				id={id}
				type="checkbox"
				checked={checked}
				name={name}
				value={value}
				onChange={onChange}
			/>
			<label className="cbx" htmlFor={id}>
				<span className={`checkbox-span ${checked ? "checked" : ""}`}>
					<svg width="12px" height="10px" viewBox="0 0 12 10">
						<polyline points="1.5 6 4.5 9 10.5 1"></polyline>
					</svg>
				</span>
				<span>{label}</span>
			</label>
		</div>
	);
};

export default Checkbox;
