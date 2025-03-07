import React from 'react'

const UpArrowIcon = ({fill='black',size="10"}) => {
  return (
		<svg
			xmlns="http://www.w3.org/2000/svg"
			width={size}
			height={size*0.6}
			viewBox="0 0 10 6"
			fill={fill}
		>
			<path
				d="M5 2.79844L1.8375 5.96094L0.875 4.99844L5 0.873438L9.125 4.99844L8.1625 5.96094L5 2.79844Z"
				fill={fill}
			/>
		</svg>
	);
}

export default UpArrowIcon