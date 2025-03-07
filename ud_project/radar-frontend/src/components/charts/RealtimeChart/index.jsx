import React, { useState, useEffect } from "react";
import ReactApexChart from "react-apexcharts";
import ApexCharts from "apexcharts";

const generateFixedData = () => {
  const startTime = new Date("2024-06-17T00:00:00Z").getTime();
  const interval = 30 * 1000; // 30 seconds in milliseconds
  const data = [];

  for (let i = 0; i <= 10; i++) {
    const x = new Date(startTime + i * interval).toISOString();
    const y = Math.floor(Math.random() * 3) + 1; // Random value: 1 (Low), 2 (Medium), or 3 (High)
    data.push({ x, y });
  }

  return data;
};

const RealtimeChart = ({ height }) => {
  const [state, setState] = useState({
    series: [
      {
        name: "Variable Data",
        data: generateFixedData(),
      },
    ],
    options: {
      chart: {
        id: "realtime",
        type: "line",
        animations: {
          enabled: true,
          easing: "linear",
          dynamicAnimation: {
            speed: 300,
          },
        },
        toolbar: {
          show: false,
        },
      },
      colors: ["#FFFFFF"],
      tooltip: {
        enabled: false,
      },
      dataLabels: {
        enabled: false,
      },
      stroke: {
        curve: "smooth",
      },
      markers: {
        size: 0,
      },
      xaxis: {
        type: "datetime",
        labels: {
          formatter: function (value) {
            const date = new Date(value);
            const minutes = date.getMinutes().toString().padStart(2, "0");
            const seconds = date.getSeconds().toString().padStart(2, "0");
            return `${minutes}:${seconds}`;
          },
          style: {
            colors: "#FFFFFF",
          },
        },
        range: 300000,
      },
      yaxis: {
        tickAmount: 2,
        labels: {
          formatter: function (value) {
            if (value === 1) return "Low";
            if (value === 2) return "Medium";
            if (value === 3) return "High";
            return value;
          },
          style: {
            colors: "#FFFFFF",
          },
        },
        range: 5 * 60 * 1000,
      },
      legend: {
        show: false,
      },
    },
  });

  useEffect(() => {
    let chartData = [...state.series[0].data];

    const updateChart = () => {
      // Get the last timestamp
      const lastTimestamp = new Date(chartData[chartData.length - 1].x);

      // Add 30 seconds to create new timestamp
      const newTimestamp = new Date(lastTimestamp.getTime() + 30000);

      // Generate random y value between 1 and 3
      const newY = Math.floor(Math.random() * 3) + 1;

      // Create new data point
      const newDataPoint = {
        x: newTimestamp.toISOString(),
        y: newY,
      };

      // Remove oldest point and add new point
      chartData = [...chartData.slice(1), newDataPoint];

      // Update the state
      setState((currentState) => ({
        ...currentState,
        series: [
          {
            ...currentState.series[0],
            data: chartData,
          },
        ],
      }));

      // Update the chart using ApexCharts.exec
      ApexCharts.exec("realtime", "updateSeries", [
        {
          data: chartData,
        },
      ]);
    };

    // Set up interval to update every 30 seconds
    const intervalId = setInterval(updateChart, 300);

    // Clean up interval on component unmount
    return () => clearInterval(intervalId);
  }, []); // Empty dependency array means this effect runs once on mount

  return (
    <ReactApexChart
      options={state.options}
      series={state.series}
      type="line"
      height={height}
    />
  );
};

export default RealtimeChart;
