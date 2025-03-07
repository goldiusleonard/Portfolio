import React from 'react'
import FunnelChart from '../../components/charts/FunnelChart'
import DateRangePicker from '../../components/DatePicker'
import FilterByRisk from '../../components/FilterCard/FilterByRiskLevel'
import FilterByPlatform from '../../components/FilterCard/FilterByPlatform'
import FilterByCategory from '../../components/FilterCard/FilterByCategory'
import OverallContentTable from '../../components/tables/OverallContentTable'
import { tableDummyData, tableDummyHeaders } from '../../data/table'
import useBreadcrumb from '../../hooks/useBreadcrumb'
// import { tableDummyData, tableDummyHeaders } from '../../dummyData'

const OverallContent = () => {

  const title = 'Workspace: Scam Officer'; 
  const hasBackButton = false;
  const hasDateFilter = true; 

  useBreadcrumb({ title, hasBackButton, hasDateFilter });
    
    return (
			<div className="overall-content-wrapper">
				<section className="filter-section">
					{/* Paste the filter-section component here */}
					<div className="funnel-chart-wrapper card-wrap h-100">
						<FunnelChart />
					</div>
					<div className="calender-wrapper card-wrap h-100">
						<DateRangePicker />
					</div>
					<div className="filter-card-by-platform">
						<div className="filter-cards-card-1 card-wrap">
							<FilterByRisk />
						</div>
						<div className="filter-cards-card-2 card-wrap">
							<FilterByPlatform />
						</div>
					</div>
					<div className="filter-card-by-topic card-wrap h-100">
						<FilterByCategory />
					</div>
				</section>
				{/* <section className="action-cards-section">
                <div className='table-actions-card card-wrap h-100'>

                </div>
                <div className='quantity-card card-wrap h-100'>

                </div>
                <div className='date-card card-wrap h-100'>

                </div>
            </section> */}
            <section className='data-table-section card-wrap'>
                <OverallContentTable values={tableDummyData} headers={tableDummyHeaders} />
            </section>
        </div>
    )
}

export default OverallContent
