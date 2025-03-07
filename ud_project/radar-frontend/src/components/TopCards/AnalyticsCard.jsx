import React from 'react';
import Chart from 'react-apexcharts';
import LoaderAnimation from '../LoaderAnimation';

const AnalyticsCard = ({ title, number, chartData, handleClick, highlightedSeries }) => {
 
  const chartOptions = {
    chart: {
      type: 'area',
      height: '100%',
      toolbar: {
        show: false,
      },
    },
    stroke: {
      curve: 'smooth',
      width: 4,
    },
    dataLabels: {
      enabled: false,
    },
    xaxis: {
      labels: {
        show: false,
      },
      axisBorder: {
        show: false,
      },
      axisTicks: {
        show: false,
      },
    },
    yaxis: {
      show: false,
    },
    tooltip: {
      enabled: false, 
    },
    grid: {
      show: false,
    },
    fill: {
      type: 'gradient',
      gradient: {
        shadeIntensity: 1,
        gradientToColors: [chartData?.line_color[0] === 'green' ? '#0072C5' : chartData?.line_color[0] === 'gray' ? '#0BC094' : '#FF0D0D'],
        opacityFrom: 0.5,
        opacityTo: 0.5,
        stops: [30, 100],
      },
    },
    colors: [chartData?.line_color[0] === 'green' ? '#0072C5' : chartData?.line_color[0] === 'gray' ? '#0BC094' : '#FF0D0D']
  };
  
  return (
    <div
      className={`card ${highlightedSeries === title && 'active'}`}
      onClick={handleClick ? () => handleClick(title) : undefined}
    >
      <div className={`card-body px-2 py-3 h-100 ${!chartData && `d-flex flex-column align-items-center justify-content-between`}`}>
        <h5 className="card-title text-start">
          {title}
        </h5>
        <div className="chart-wrapper">
          {chartData &&
            <div 
            className='chart-container' 
            
            >
              <Chart
                options={chartOptions}
                series={chartData.series}
                type="area"
                width="120px" 
                height='100px'
              />
            </div>
          }
          {number === undefined ?
            <LoaderAnimation />
            :
            <h6 className={`card-subtitle`}>
              {number}
            </h6>
          }
        </div>
      </div>
    </div>
  );
};

export default AnalyticsCard;
