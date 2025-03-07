import React from "react";

import {

	activityTableData,
	activityTabHeaders
} from "../../data/workspaceTableData";
import useBreadcrumb from "../../hooks/useBreadcrumb";

import TableWithSearchbar from '../../components/tables/TableWithSearchbar';

// const loadingData = false;
const ActivityPage = () => {
	const title = 'Activity';
	const hasBackButton = false;
	const hasDateFilter = true;
	useBreadcrumb({ title, hasBackButton, hasDateFilter });
	const ref=React.useRef()
	const scrollHeight = ref.current?.offsetHeight
	const tableProps = {
		tableProps: {
		  headers: activityTabHeaders,
		  scrollHeight: scrollHeight-100,
		  emptyMessage: 'No offer found',
		  rowClassName :'activity-table-row'
	
		},
		searchProps: {
		  placeholder: 'Search',
		  onSearchChange: () => {},
		},
		data:  activityTableData,
		loadingData: false,
		
	
		
		
	  };


	return (

		<div className="overall-content-wrapper"  >

			<section className="activity-card-wrap card-wrap" ref={ref}>
			<TableWithSearchbar {...tableProps} />
	
			</section>
			

		</div>
	);
};

export default ActivityPage;


