import React from 'react'

const DownArrowIcon = ({fill='black',size="10",deg}) => {
  return (
		<svg
			xmlns="http://www.w3.org/2000/svg"
			width={size}
			height={size}
			viewBox="0 0 10 6"
			fill={fill}
			style={{transform: `rotateZ(${deg})`}}

		>
			<path
				d="M5 4.0375L8.1625 0.875L9.125 1.8375L5 5.9625L0.875001 1.8375L1.8375 0.875L5 4.0375Z"
				fill={fill}
			/>
		</svg>
	);
}

export default DownArrowIcon