import React from 'react';
import Chart from 'react-apexcharts';

const RiskLevelChart = () => {
    const options = {
        chart: {
            type: 'rangeBar',
            height: 150,
            toolbar: {
                show: false
            }
        },
        plotOptions: {
            bar: {
                horizontal: true,
                barHeight: '100%',
                rangeBarGroupRows: true
            }
        },
        series: [{
            data: [{
                x: 'Overall Risk Level',
                y: [0, 10]
            }]
        }],
        xaxis: {
            min: 0,
            max: 10,
            labels: {
                show: false
            },
            axisTicks: {
                show: false
            },
            axisBorder: {
                show: false
            }
        },
        yaxis: {
            labels: {
                show: false
            }
        },
        fill: {
            type: 'gradient',
            gradient: {
                shade: 'dark',
                type: 'horizontal',
                shadeIntensity: 0.5,
                gradientToColors: ['#f05d23', '#ff3f34'],
                inverseColors: true,
                stops: [0, 50, 100]
            }
        },
        annotations: {
            xaxis: [
                {
                    x: 0,
                    strokeDashArray: 0,
                    borderColor: 'transparent',
                    label: {
                        position: 'bottom',
                        offsetY: 5,
                        style: {
                            color: '#00E396',
                            background: 'transparent',
                            fontSize: '12px',
                        },
                        text: 'Low'
                    }
                },
                {
                    x: 5,
                    strokeDashArray: 0,
                    borderColor: 'transparent',
                    label: {
                        position: 'bottom',
                        offsetY: 5,
                        style: {
                            color: '#00E396',
                            background: 'transparent',
                            fontSize: '12px',
                        },
                        text: 'Medium'
                    }
                },
                {
                    x: 10,
                    strokeDashArray: 0,
                    borderColor: 'transparent',
                    label: {
                        position: 'bottom',
                        offsetY: 5,
                        style: {
                            color: '#00E396',
                            background: 'transparent',
                            fontSize: '12px',
                        },
                        text: 'High'
                    }
                },
                {
                    x: 8, // This is where you place your marker
                    borderColor: '#00E396',
                    label: {
                        borderColor: '#00E396',
                        style: {
                            color: '$white',
                            background: '#00E396'
                        },
                        text: 'Current Level'
                    }
                }
            ]
        }
    };

    return (
        <div>
            <Chart
                options={options}
                series={options.series}
                type="rangeBar"
                height={100}
            />
        </div>
    );
};

export default RiskLevelChart;
