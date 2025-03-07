import React, { useState } from 'react'
// import TopCards from '../../components/TopCards';
import PieChart from "../../components/charts/PieChart/index";
// import StackedBarChart from '../../components/charts/StackedBarChart/index';
import useBreadcrumb from '../../hooks/useBreadcrumb';
import useApiData from '../../hooks/useApiData';
import endpoints from '../../config/config.dev';
import LoaderAnimation from '../../components/LoaderAnimation';
import { Wordcloud, LineChart } from '../../components';
import SubCategoryBarChart from '../../components/charts/SubCategoryBarChart';
// import TotalScannedContent from '../../components/total-scanned-content/TotalScannedContent';
import FunnelContent from '../../components/Funnel';
import { getUserFromLocalStorage } from '../../Util'; 



const Dashboard = () => {
  const [filterValue, setFilter] = useState('AI Flagged Content');
  const user=getUserFromLocalStorage()
  const title = user?.user_name
  const hasBackButton = false;
  const hasDateFilter = true;
  const hasCategoryFilter = true;

  useBreadcrumb({ title, hasBackButton, hasDateFilter, hasCategoryFilter });
  // api calls for data
  const { data: wordClouds, loadingData: wordCloudsLoading } = useApiData(endpoints.getWordCloud);
  // const { data :watchListData, loadingData: watchListDataLoading} = useApiData(endpoints.getWatchList);
  const apiEndpoint = endpoints.getMediaPercents
  const { data: piechart, loadingData: piechartLoading } = useApiData(apiEndpoint);

  const { data, loadingData } = useApiData(endpoints.getStakedBarChart)

  const handleClick = (filterName) => {
    setFilter((prev) => {
      if (prev === filterName) {
        return prev; 
      }
      return filterName; 
    });
  };

  
  const barChartData = data ? data['y-axis']?.find(item => item.name === filterValue) : [];
  
  return (
    <div className='dashboard-wrapper'>
      {/* <section className='top-filter-section'>
        <TopCards handleClick={handleClick} filterValue={filterValue} data={data}/>
      </section> */}

      <section className='charts-section'>
        <div className='stack-bar-wrapper card-wrap'>
          {/* <SubCategoryBarChart filterValue={filterValue} yData={barChartData} data={data} loading={loadingData} /> */}
          <FunnelContent handleClick={handleClick} filterValue={filterValue} data={data} loading={loadingData}/>
        </div>
        <div className='all-charts-wrapper'>
          <section className='chart-wrapper'>
            <div className='main-chart-container card-wrap'>
              {/* <TotalScannedContent activeTitle={filterValue}/> */}
              
              <SubCategoryBarChart filterValue={filterValue} yData={barChartData} data={data} loading={loadingData} />
            </div>

            <div className='sub-chart-wrapper'>
            <div className='pie-chart-container card-wrap'>
                {/* <div className="wrap-card-title">
                  highest social media threats
                </div> */}
                {piechartLoading ? <LoaderAnimation /> :
                  <PieChart data={piechart} />
                }
              </div>
            <div className='word-cloud-container card-wrap'>
                {wordCloudsLoading ? <LoaderAnimation /> :
                  <Wordcloud words={wordClouds} onWordClick={undefined} />
                }
              </div>
           
            
            </div>
          </section>
          <section className='multiline-chart-container card-wrap' >
            <LineChart  />
          </section>
        </div>
      </section>

    </div>
  )
}

export default Dashboard
