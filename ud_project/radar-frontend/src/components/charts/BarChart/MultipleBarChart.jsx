import React, { useMemo } from 'react'
import Chart from "react-apexcharts";
import formatNumber from '../../../Util/NumberFormat'

const MultipleBarChart = ({
  width,
  height,
  categories = [],
  data = [],
  colors = [],
  xAxisLabel = []
}) => {
  const defaultColors = colors.length ? colors : [
    "#F4BE37",
    "#5388D8",
    "#53D6F4",
    "#F453EC"
  ]

  const barOptions = useMemo(() => ({
    xaxis: {
      categories: xAxisLabel,
      axisBorder: {
        show: false
      },
      axisTicks: {
        show: false
      },
      labels: {
        style: {
          colors: '#9CA3AF'
        }
      }
    },
    yaxis: {
      labels: {
        style: {
          colors: '#9CA3AF'
        },
        formatter: (value) => formatNumber(value)
      },
    },
    legend: {
      show: false
    },
    chart: {
      type: 'bar',
      toolbar: {
        show: false
      }
    },
    dataLabels: {
      enabled: false
    },
    stroke: {
      colors: ["transparent"],
      width: 4
    },
    grid: {
      borderColor: '#9CA3AF4D'
    },
    tooltip: {
      theme: 'dark'
    },
    colors: defaultColors.map(v => `${v}4D`)
  }), [])

  return (
    <div className="multiple-bar-chart-wrapper">
      <Chart
        type='bar'
        series={data}
        options={barOptions}
        width={width}
        height={height}
      />

      <div className="legend-container">
        {data.map((v, idx) => (
          <div
            key={idx}
            className="wrapper"
          >
            <div className="label-container">
              <div style={{
                border: `1px solid ${defaultColors[idx]}`,
                backgroundColor: `${defaultColors[idx]}4D`
              }} />
              <span>{categories[idx]}</span>
            </div>
            <span className="subtitle">
              {v.total?.toLocaleString() || ''}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default MultipleBarChart