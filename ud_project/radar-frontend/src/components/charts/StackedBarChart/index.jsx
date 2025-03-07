import React, { useEffect } from 'react';
import ReactApexChart from 'react-apexcharts';
import formatNumber from '../../../Util/NumberFormat';
import { useNavigate } from 'react-router-dom';
import endpoints from '../../../config/config.dev';
import useApiData from '../../../hooks/useApiData';
import { useGlobalData } from '../../../App';
import LoaderAnimation from '../../LoaderAnimation';

const StackedBarChart = ({ highlightedSeries }) => {
  const navigation = useNavigate();
  const { setAnalyticsData } = useGlobalData();
  const apiEndpoint = endpoints.getStakedBarChart
  const { data, loadingData } = useApiData(apiEndpoint)

  useEffect(() => {
    if (data) {
      setAnalyticsData(data);
    }
  }, [data, setAnalyticsData])

  const baseSeries = data ? data["y-axis"].map(series => ({
    name: series.name,
    data: series.data,
    color: highlightedSeries === series.name ? '#8571F4' : '#5C4FA1',
    fill: { opacity: series.name === 'AI Flagged Content' ? 0.25 : series.name === 'Reported' ? 0.75 : 1 }
  })) : [];

  const defaultCategories = data ? data["x-axis"] : [];

  const prioritizeCategories = defaultCategories.slice(0, 3);

  const sortCategories = (categories, prioritize) => {
    const prioritized = categories.filter(category => prioritize.includes(category));
    const others = categories.filter(category => !prioritize.includes(category));
    return [...prioritized, ...others];
  };

  const sortedCategories = sortCategories(defaultCategories, prioritizeCategories);

  const sortSeriesData = (seriesData, sortedCategories, defaultCategories) => {
    return seriesData.map(series => {
      const sortedData = sortedCategories.map(category => {
        const index = defaultCategories.indexOf(category);
        return series.data[index];
      });
      return { ...series, data: sortedData };
    });
  };

  const sortedSeries = sortSeriesData(baseSeries, sortedCategories, defaultCategories);

  const orderedSeries = sortedSeries.sort((a, b) => (a.name === highlightedSeries ? -1 : b.name === highlightedSeries ? 1 : 0));

  const chartData = {
    series: orderedSeries,
    options: {
      chart: {
        type: 'bar',
        height: 250,
        stacked: true,
        toolbar: {
          show: false,
        },
        events: {
          dataPointSelection: (event, chartContext, config) => {
            const { dataPointIndex } = config;
            
            if (dataPointIndex < prioritizeCategories.length) {
              navigation(`/category`, {state:{subCategoryRoute: prioritizeCategories[dataPointIndex]}});
            }
          },
        },
      },
      plotOptions: {
        bar: {
          horizontal: true,
          barHeight: '70%',
          columnWidth: '0%',
          borderRadius: 0,
          enableShades: false,
          distributed: false,
        },
      },
      title: {
        text: 'Scam: Sub Categories',
        align: 'left',
        offsetY: 20,
        offsetX: -5,
        style: {
          fontSize: '16px',
          fontFamily: 'Montserrat-Medium',
          fontWeight: '500',
          color: '#ffffff',
        },
      },
      dataLabels: {
        enabled: false,
      },
      xaxis: {
        categories: sortedCategories,
        axisBorder: {
          show: false,
        },
        axisTicks: {
          show: false,
        },
        labels: {
          formatter: (value) => formatNumber(value),
          style: {
            colors: '#00ffff',
            fontSize: '12px',
            fontFamily: 'Montserrat-Medium',
          },
        },
      },
      yaxis: {
        labels: {
          align: 'left',
          offsetX: -20,
          style: {
            colors: '#00ffff',
            fontSize: '12px',
            fontFamily: 'Montserrat-Medium',
          },
        },
      },
      tooltip: {
        enabled: false,
      },
      grid: {
        show: false,
      },
      stroke: {
        show: false,
      },
      fill: {
        opacity: 1,
      },
      states: {
        hover: {
          filter: {
            type: 'none',
          },
        },
      },
      legend: {
        show: false,
      },
    },
  };


  return (
    <div className='h-100' style={{padding: '0 25px'}}>
      {loadingData ? <LoaderAnimation />
        :
        <ReactApexChart
          options={chartData.options}
          series={chartData.series}
          type="bar"
          height={370}
        />
      }
    </div>
  );
};

export default StackedBarChart;
