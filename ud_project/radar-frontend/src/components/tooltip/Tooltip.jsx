import React from 'react'; // Ensure React is in scope when using JSX
import PropTypes from 'prop-types';

export const Tooltip = ({ visible, onClose, children, tooltipPosition, content, x }) => {


	return (
		<div className={`tooltip-modal ${visible ? "show" : ""}`} style={{ position: 'absolute', top: tooltipPosition + 60, left: x ? x : '50%', }}>
			{!!children ? children : <div className="tooltip-modal-content">
				<div className="tooltip-modal-header">

				</div>
				<div className="tooltip-modal-title">Justification</div>

				<div className="tooltip-modal-body">
				<ol>

						{Array.isArray(content) ? content.map((item, index) => (
							<li key={index}>
								<p>{item.justification_text}</p>
							</li>
						)) : null}

					</ol>
				</div>
			</div>}
		</div>
	);
};
Tooltip.propTypes = {
	visible: PropTypes.bool,
	onClose: PropTypes.func,
	children: PropTypes.node,
	tooltipPosition: PropTypes.object
};;