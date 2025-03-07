import React ,{useCallback} from "react";
import WorkspaceContentTable from '../../components/tables/WorkspaceContentTable';
import TableHeaderSelector from "./TableHeaderSelector";
import {
	dummyWorkspaceTableData,
	similarContentsListHeaders,
} from "../../data/workspaceTableData";
import useBreadcrumb from "../../hooks/useBreadcrumb";
import Alert from "../../components/Alert";
import endpoints from '../../config/config.dev';
import useApiData from '../../hooks/useApiData';
import LoaderAnimation from '../../components/LoaderAnimation';
import {Tooltip} from '../../components';

// const loadingData = false;
const Workspace = () => {
	const title = 'Workspace';
	const hasBackButton = false;
	const hasDateFilter = true;

	const contentListUrl = `${endpoints.getContentList}`;
	const { data ,loadingData } = useApiData(contentListUrl);

	useBreadcrumb({ title, hasBackButton, hasDateFilter });

	const [tooltipVisible, setTooltipVisible] = React.useState(false);
	const [tooltipPosition, setTooltipPosition] = React.useState({ x: 0, y: 0 });
	const [tooltipContent, setTooltipContent] = React.useState("");


// Inside your component
// const handleTooltip = useCallback((e) => {
// if(e.data){
//     setTooltipPosition({ x: e.originalEvent.clientX, y: e.originalEvent.clientY });
//     setTooltipVisible(true);
// 	setTooltipContent(e.data.justification);
// }
// }, [tooltipPosition, tooltipContent, tooltipVisible, setTooltipPosition, setTooltipContent, setTooltipVisible]);

// const handleTooltipClose = useCallback(() => {
	
// 	setTooltipVisible(false);
// }, []);

	return (

		<div className="overall-content-wrapper" >
			<div>
				<Alert
					message="Creator has been successfully reported"
					info="success"
					duration={25000}
					visible={false}
				/>
			</div>
			<section className="workspace-status-container">
				<div className="workspace-status-container">
					<div className="card workspace-status-card">All Data</div>
					<div className="card workspace-status-card">AI Flagged</div>
					<div className="card workspace-status-card">Reported</div>
					<div className="card workspace-status-card">Resolved</div>
				</div>
				<div className="update-container">
					<p>
						Latest Update <span> 8 May 2024</span>
					</p>
					<p>
						Content Quantity <span>65</span>
					</p>
				</div>
			</section>
			<section className="workspace-card-wrap card-wrap">
				<TableHeaderSelector />
				{loadingData ? <LoaderAnimation /> : <WorkspaceContentTable
					values={ data.slice(0,10)}
					// values={dummyWorkspaceTableData}
					headers={similarContentsListHeaders}
					scrollable
				
					// onRowMouseEnter={handleTooltip}
					// onRowMouseLeave={handleTooltipClose}
				/>}
			</section>
			
<Tooltip visible={tooltipVisible} tooltipPosition={tooltipPosition.y} content={tooltipContent} />
		</div>
	);
};

export default Workspace;


