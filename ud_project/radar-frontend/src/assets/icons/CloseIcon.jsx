import React from 'react'

const CloseIcon = ({fill, onClick}) => {
  return (
		<svg
			xmlns="http://www.w3.org/2000/svg"
			width="32"
			height="32"
			viewBox="0 0 32 32"
			fill={fill}
			onClick={onClick}
		>
			<g clipPath="url(#clip0_1813_38858)">
				<path
					d="M25.3327 8.54699L23.4527 6.66699L15.9993 14.1203L8.54602 6.66699L6.66602 8.54699L14.1193 16.0003L6.66602 23.4537L8.54602 25.3337L15.9993 17.8803L23.4527 25.3337L25.3327 23.4537L17.8793 16.0003L25.3327 8.54699Z"
					fill={fill}
				/>
			</g>
			<defs>
				<clipPath id="clip0_1813_38858">
					<rect width="32" height="32" fill={fill} />
				</clipPath>
			</defs>
		</svg>
	);
}

export default CloseIcon