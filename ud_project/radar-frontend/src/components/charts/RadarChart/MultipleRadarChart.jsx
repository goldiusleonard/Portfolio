import React, { useMemo } from 'react'
import Chart from "react-apexcharts";
import formatNumber from '../../../Util/NumberFormat'

// Props Options
// {
//   width: number
//   height: number
//   categories: [] of string
//   data = [{
//     name: String,
//     data: [] of number
//     total: number | string
//   }]
//   colors: [] of hex
//   xAxisLabel: [] of string
// }

const MultipleRadarChart = ({
  width,
  height,
  categories = [],
  data = [],
  colors = [],
  xAxisLabel = []
}) => {
  const radarOptions = useMemo(() => ({
    xaxis: {
      categories: xAxisLabel
    },
    yaxis: {
      labels: {
        style: {
          colors: '#fff'
        },
        formatter: (value) => formatNumber(value)
      },
    },
    legend: {
      show: false
    },
    chart: {
      type: 'radar',
      toolbar: {
        show: false
      }
    },
    tooltip: {
      theme: 'dark'
    },
    colors: colors.length ? colors : ["#F4BE37", "#5388D8", "#53D6F4", "#F453EC"]
  }), [])

  return (
    <div className="radar-chart-wrapper">
      <Chart
        options={radarOptions}
        series={data}
        type='radar'
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
                border: `1px solid ${radarOptions.colors[idx]}`,
                backgroundColor: `${radarOptions.colors[idx]}4D`
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

export default MultipleRadarChart