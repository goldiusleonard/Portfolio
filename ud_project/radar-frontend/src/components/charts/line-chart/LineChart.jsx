
// import { hover } from '@testing-library/user-event/dist/hover';
import React from 'react';
import ReactApexChart from 'react-apexcharts';
// import { useNavigate } from 'react-router-dom';
// import { useGlobalData } from '../../../App';
import LoaderAnimation from '../../LoaderAnimation';
import formatNumber from '../../../Util/NumberFormat';
import { useRef } from 'react';
import endpoints from '../../../config/config.dev';
import useApiData from '../../../hooks/useApiData';

const colorPalette = ['#0097BA', '#B1E7F5', '#B45248', '#D48C83', '#A89B49', '#FF8C00', '#3BB464', '#836394', '#CFFF04', '#C400C4'];

// let date = '';
export const LineChart = () => {
    // const navigate = useNavigate();
    // const { setCreatorUsername } = useGlobalData();
    const { data, loadingData } = useApiData(endpoints.getWatchList);
   
    const ref = useRef(null);
    // const fullAvailabelHeight = ref.current?.offsetHeight ? ref.current.offsetHeight - 20 : 250;
    //  const threatLevelformat = (number) => {
    //     const rounded = Math.round(number * 10) / 10;
    //     const roundedValue = rounded % 1 === 0 ? rounded.toFixed(0) : rounded.toFixed(1);
    //     return `${roundedValue}%`;
    // };

    // Function to filter data for the last seven days
    // const filterLastSevenDays = (data) => {
    //     if (!data) return [];
    //     const sevenDaysAgo = new Date();
    //     sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
    //     let result = data
    //         .map(user => ({
    //             name: user.name,
    //             data: user.data?.filter(point => new Date(point.x) >= sevenDaysAgo)
    //         }))
    //         .slice(0, 10);
    //     //   result.push(fakeValue);
    //     return result;
    // };

    // const filteredData = filterLastSevenDays(data);
    const filteredData = Array.isArray(data)?data :[]


    const chartData = {
        series: filteredData,
        options: {
            chart: {
                type: 'line',
                toolbar: {
                    show: false,
                },
                zoom: {
                    enabled: false,
                },

                animations: {
                    enabled: true,
                    easing: 'easeinout',
                    speed: 400,
                    animateGradually: {
                        enabled: true,
                        delay: 150,
                    },
                    dynamicAnimation: {
                        enabled: true,
                        speed: 350,
                    },
                },
                dropShadow: {
                    enabled: true,
                    top: 0,
                    left: 0,
                    blur: 3,
                    opacity: 0.5,
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
                        fontFamily: 'Montserrat-Medium',
                        offsetX: 20,
                        offsetY: 20,
                    },
                    formatter: formatNumber,
                    offsetX: -15,

                },
                forceNiceScale: true,


            },
            stroke: {
                curve: 'smooth',
                width: 1.5,
                hover: {
                    width: 5,
                },
            },
            markers: {
                size: 4,
                strokeColors: colorPalette,
                strokeWidth: 4,
                colors: colorPalette,
                cursor: 'pointer',
                hover: {
                    size: 7,
                    sizeOffset: 8,
                  
                   
                },
                dataPointMouseEnter: {
                    size: 7,
                    sizeOffset: 8,
                },

                shape: 'circle',
                // onClick: function (e) {
                //     const index = e.target.getAttribute('index');
                //     const name = filteredData[index].name;
                //     goWatchList(name,date);
                
                // },
          
            },

            tooltip: {
                enabled: true,
                shared: false,
                intersect: true,
                followCursor: true,
                theme: 'dark',
                style: {
                    fontSize: '14px',
                    fontFamily: 'Montserrat-Medium',
                    background: '#000000',
                },
          
                custom: function ({ series, seriesIndex, dataPointIndex, w }) {
                    
                    const pointData = filteredData[seriesIndex]?.data[dataPointIndex]
                    const profileUrl = pointData.urlProfile || 'https://via.placeholder.com/20';
           
                    
                    // date =pointData.x


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

                                <span>${filteredData[seriesIndex].name}</span>
                            </div>
                            <div className="tooltip-body">
                                <div>Engagement: ${formatNumber(pointData.y)}</div>
                            
                            </div>
                        </div>`
                        ;
                },
           
            },

            title: {
                text: 'Watchlist Engagement Count',
                align: 'left',
                style: {
                    fontSize: '20px',
                    fontWeight: 'bold',
                    color: '#A9A9A9',
                    fontFamily: 'inherit',
                    textTransform: 'uppercase'
                },
            },
            fill: {
                type: 'solid',
                opacity: 0.7,
            },
            colors: colorPalette,
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
            foreColor: colorPalette,
            dataLabels: {
                enabled: false,
            },

            legend: {
                show: true, // turn off for now as requirement might be changed.
                position: 'right',
                inverseOrder: true,
                ontFamily: 'Montserrat',
                fontWeight: 700,
                offsetX: -24,
                offsetY:24,

                textAnchor: 'right',
                labels: {
                    useSeriesColors: false,
                    fill: '#A3B9CC',
                  
                    fontSize: 50,
                    fontWeight: 700,
                    padding: 10,
                    fontFamily: 'Montserrat-Medium',
                    colors: '#A3B9CC',
                },

                markers: {
                    show:true,
                    // useSeriesColors: true,
                    fillColors:colorPalette,
                    width: 10,
                    height: 10,
                    // strokeWidth: 10,
                    strokeColor: '#fff',
                    // radius: 12,
                },
                enabled: true, //
            },
            // width: 1000

        },

    };

    // function goWatchList(name) {
    //     // setCreatorUsername(name);
    //     // navigate('/watch-list/creator', { state: { user_handle: name, engagementDate:date } });
    // }

    return (
        <div ref={ref} className='h-100'>
            {loadingData ?
                <LoaderAnimation />
                :
                <ReactApexChart
                    options={chartData.options}
                    series={chartData.series}
                    // type="line"
                    height={'100%'}
                    loading={loadingData}
                    width={'100%'}
                />
            }
        </div>
    );
}

