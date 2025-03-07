
import React from 'react'
import ReactApexChart from 'react-apexcharts';
import formatNumber from '../../../Util/NumberFormat';
// import moment from "moment";
import ToggleChart from './ToggleChart';
import Select from '../../Select/Select';
import endpoints from '../../../config/config.dev';
import useApiData from '../../../hooks/useApiData';
import LoaderAnimation from '../../LoaderAnimation';
// const creatorLinechatData = {
//   "name": "maximagoldhedge",
//   "data": [
//       {
//           "x": "2024-06-18",
//           "y": 158,
//           "urlProfile": "https://blobstrgmcmc.blob.core.windows.net/pfpfiles/maximagoldhedge_pfp.jpeg?se=2027-02-21T02%3A29%3A46Z&sp=r&sv=2023-11-03&sr=b&sig=qHq%2BzCIKkcVlak5FbR2GNnpX82to8ZgBaVgd%2B0gFECM%3D",
//           'topVideoIdsList':[1122,748737,7273]
//       },
//       {
//           "x": "2024-06-23",
//           "y": 111,
//           "urlProfile": "https://blobstrgmcmc.blob.core.windows.net/pfpfiles/maximagoldhedge_pfp.jpeg?se=2027-02-21T02%3A29%3A46Z&sp=r&sv=2023-11-03&sr=b&sig=qHq%2BzCIKkcVlak5FbR2GNnpX82to8ZgBaVgd%2B0gFECM%3D",
//           'topVideoIdsList':[1122,748737,7273]
//       },
//       {
//           "x": "2024-06-24",
//           "y": 30,
//           "urlProfile": "https://blobstrgmcmc.blob.core.windows.net/pfpfiles/maximagoldhedge_pfp.jpeg?se=2027-02-21T02%3A29%3A46Z&sp=r&sv=2023-11-03&sr=b&sig=qHq%2BzCIKkcVlak5FbR2GNnpX82to8ZgBaVgd%2B0gFECM%3D",
//           'topVideoIdsList':[1122,748737,7273]
//       },
//       {
//           "x": "2024-06-25",
//           "y": 26,
//           "urlProfile": "https://blobstrgmcmc.blob.core.windows.net/pfpfiles/maximagoldhedge_pfp.jpeg?se=2027-02-21T02%3A29%3A46Z&sp=r&sv=2023-11-03&sr=b&sig=qHq%2BzCIKkcVlak5FbR2GNnpX82to8ZgBaVgd%2B0gFECM%3D",
//           'topVideoIdsList':[1122,748737,7273]
//       },
//       {
//           "x": "2024-06-27",
//           "y": 13,
//           "urlProfile": "https://blobstrgmcmc.blob.core.windows.net/pfpfiles/maximagoldhedge_pfp.jpeg?se=2027-02-21T02%3A29%3A46Z&sp=r&sv=2023-11-03&sr=b&sig=qHq%2BzCIKkcVlak5FbR2GNnpX82to8ZgBaVgd%2B0gFECM%3D",
//           'topVideoIdsList':[1122,748737,7273]
//       }
//   ]
// };

const options1 = [
  "Last 7 Days",
  "Last 1 Month",
  "Last 6 Month",
  "Last 1 Year",

];

let highlighedIndex=null;
export const SingleLinechart = ({  setDate, handleToggle, creatorName,handleHighlightedContent }) => {

  const { data, loadingData } = useApiData(`${endpoints.getCreatorLinechartData}?userName=${creatorName}`);



  const chartData = {

// need to filter data;
    series:[data],
    options: {
      chart: {
        type: 'line',
        toolbar: {
          show: false,
        },
        zoom: {
          enabled: false,
        },
      },
      colors: ['#FFE700'],

      dataLabels: {
        enabled: false
      },

      stroke: {
        curve: 'smooth',
        width: 1.5,
        colors: ['#FFE700'],
      },
      grid: {
        show: true,
        borderColor: 'rgba(255, 255, 255, 0.1)',
        strokeDashArray: 0,
        position: 'front',
        xaxis: {
          lines: {
            show: false,
          },
        },
        yaxis: {
          lines: {
            show: true,

          },
        },
        row: {
          colors: undefined,
          opacity: 0.2,
        },
        column: {
          colors: undefined,
          opacity: 0.2,
        },
        padding: {
          top: 0,
          right: 0,
          bottom: 0,
          left: 0,
        },

      },
      xaxis: {
        type: 'datetime',

        labels: {
          rotateAlways: false,
          style: {
            colors: '#7B7B7B',
            fontSize: 13,
            fontFamily: 'Montserrat-Medium',
            offsetX: 1,
          },
          trim: true,
          hideOverlappingLabels: true,
          show: true,

        },

      },
      yaxis: {

        labels: {
          style: {
            colors: '#7B7B7B',
            fontSize: 13,
            fontFamily: 'inherit',


          },
          offsetX: -15,
          formatter: formatNumber,



        },
        forceNiceScale: true,


      },
      tooltip: {
        shared: false,
        intersect: true,
        show: true,

        theme: 'dark',
        y: {
          formatter: function (val) {
            return (val / 1000000).toFixed(0)
          }
        },
        custom: function ({ series, seriesIndex, dataPointIndex, w }) {
          highlighedIndex=dataPointIndex;
        
          // chosenDate = (moment(data.data[dataPointIndex].x).format('ddd, DD MMM, YYYY'));

          const profileUrl = data.data[dataPointIndex].urlProfile;
          
          


          return `<div className="custom-tooltip"
          style="
              width: 200px;
              height: 74px;
              padding: 12px 16px;
              gap: 8px;
              border-radius: 16px 0px 0px 0px;
              border: 1px 0px 0px 0px;
          "
          >
              <div className="tooltip-header"
              style="
              width: 168px;
              height: 30px;
              gap: 8px;
              "
              >
              <img src="${profileUrl}" alt="Profile Image" style="width: 25px; height: 25px; border-radius: 50%; margin-right: 10px;">

                  <span>${data.name}</span>
              </div>
              <div className="tooltip-body">
                  <div>Engagement: ${formatNumber(data.data[dataPointIndex].y)}</div>
              
              </div>
          </div>`
          ;

        },

      },

      markers: {

        size: 4,
        strokeColors: '#fff',
        strokeWidth: 1,
        colors: '#fff',
        hover: {
          size: 10,
          sizeOffset: 8,
        },
        cursor: PointerEvent,
        dataPointMouseEnter: {
          size: 10,
          sizeOffset: 8,
        },
        shape: 'circle',
        onClick: function (e) {
          handleHighlightedContent(data?.data[highlighedIndex]?.topVideoIdsList)
          // setDate(chosenDate)
          // do something on marker click
        },


      },
    },





  };








  return (
    <div style={{ padding: '1rem', height: '100%', width: '100%', minHeight: loadingData ? '400px' : 'auto' }}>
      <div className='header'>
        <Select
          options={options1}
          defaultValue={options1[0]}
          className="DaysDropdown"
          arrowSize={"15"}
        />
        <ToggleChart active={'isLineChart'} onClick={handleToggle} />
      </div>
      {loadingData ? <LoaderAnimation /> : <ReactApexChart
        options={chartData.options}
        series={chartData.series}
        type="line"
        height={'100%'}
        loading={loadingData}
        width={'100%'}

      />}
    </div>
  )
}
