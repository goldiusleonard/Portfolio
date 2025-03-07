import React from 'react'

const OverAllContentTableHeader = () => {
  return (
		<div className="table-top-header">
			<div className="header-button-container">
				<button className="table-button table-button-report">Report</button>
				<button
					className="table-button table-button-selectAll"
					// onClick={selectAllHandler}
				>
					{/* {selectText} */}
				</button>
			</div>
			<div className="header-button-container">
				<button className="table-button table-button-report">
					Remove Filters
				</button>
				<button className="table-button table-button-content">
					Content Quantity
					<span> 65</span>
				</button>
				<button className="table-button table-button-content">
					Latest Update
					<span> 8/05/2024</span>
				</button>
			</div>
		</div>
	);
}

export default OverAllContentTableHeader;