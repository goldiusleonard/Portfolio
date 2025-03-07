import React, { useMemo } from 'react'
import Chart from "react-apexcharts";
import formatNumber from '../../../Util/NumberFormat'

const AreaSplineChart = ({
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

  const splineOptions = useMemo(() => ({
    xaxis: {
      categories: xAxisLabel,
      tickAmount: 1000,
      labels: {
        style: {
          colors: '#fff'
        },
        formatter: (value) => value + 1
      },
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
      type: 'area',
      toolbar: {
        show: false
      }
    },
    dataLabels: {
      enabled: false
    },
    stroke: {
      curve: 'smooth'
    },
    tooltip: {
      theme: 'dark'
    },
    colors: colors.length ? colors : ["#F4BE37", "#5388D8", "#53D6F4", "#F453EC"]
  }), [])

  return (
    <div className="area-spline-chart-wrapper">
      <Chart
        type='area'
        series={data}
        options={splineOptions}
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

export default AreaSplineChart
