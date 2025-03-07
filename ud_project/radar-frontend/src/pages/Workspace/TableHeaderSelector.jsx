import React from 'react'
import { FilterIcon, SearchIcon } from '../../assets/icons';

const TableHeaderSelector = () => {
  return (
		<div className="workspace-select-container">
			<div className="search-item">
				<SearchIcon fill="#FFFFFF99" />
				<input type="text" placeholder="Select Content ID" />
			</div>
			<select>
				<option value="1">Select Date Range</option>
				<option value="2">2</option>
				<option value="3">3</option>
				<option value="4">4</option>
				<option value="5">5</option>
			</select>
			<select>
				<option value="1">Select Social Media</option>
				<option value="2">2</option>
				<option value="3">3</option>
				<option value="4">4</option>
				<option value="5">5</option>
			</select>
			<select>
				<option value="1">Select Sub-Category</option>
				<option value="2">2</option>
				<option value="3">3</option>
				<option value="4">4</option>
				<option value="5">5</option>
			</select>
			<select>
				<option value="1">Select Risk Level</option>
				<option value="2">2</option>
				<option value="3">3</option>
				<option value="4">4</option>
				<option value="5">5</option>
			</select>
			<div className='filter-card'>
				<FilterIcon fill={"white"} />
			</div>
			<div className="report-selected-btn">Report Selected</div>
		</div>
	);
}

export default TableHeaderSelector