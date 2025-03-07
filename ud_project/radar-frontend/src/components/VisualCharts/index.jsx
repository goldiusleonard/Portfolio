import React, { useEffect, useState, useMemo } from 'react'
import MultipleRadarChart from '../charts/RadarChart/MultipleRadarChart'
import MultipleBarChart from '../charts/BarChart/MultipleBarChart'
import AreaSplineChart from '../charts/Area/AreaSplineChart'
import Select from '../Select/Select';
import BarChartIcon from "../../assets/icons/BarChartIcon";
import radarChartImage from '../../assets/images/radar-chart.png'
import useApiData from "../../hooks/useApiData"
import endpoints from "../../config/config.dev"
import LoaderAnimation from "../LoaderAnimation/index";

export const currentPredictionOptions = [
  "Current",
  "Prediction"
]

export const riskOptions = [
  "Risk",
  "Engagement"
]

export const monthsOptions = [
  "1 Month",
  "3 Month",
  "6 Month"
]

const VisualCharts = React.memo(({
  categories
}) => {
  const [filterCurrentPrediction, setFilterCurrentPrediction] = useState(currentPredictionOptions[0])
  const [filterRisk, setFilterRisk] = useState(riskOptions[0])
  const [filterMonths, setFilterMonths] = useState(monthsOptions[2])
  const [selectedChart, setSelectedChart] = useState("radar")

  const constructQueryParams = () => {
    const categoryList = categories.map(v => `categories=${v}`).join('&')
    const period = filterMonths.replace(/\D+/, '')
    const chartType = filterRisk.toLowerCase()
    const state = filterCurrentPrediction.toLowerCase()

    return `?period=${period}&chart_type=${chartType}&state=${state}&${categoryList}`
  }

  const { data: visualChartData, loadingData: visualChartLoading, refetch } = useApiData(
    `${endpoints.visualChart}${constructQueryParams()}`
  )

  useEffect(() => {
    refetch()
  }, [filterCurrentPrediction, filterRisk, filterMonths])

  const handleFilterCurrentPrediction = (value) => {
    setFilterCurrentPrediction(value)
  }

  const handleFilterFilterRisk = (value) => {
    setFilterRisk(value)
  }

  const handleFilterMonths = (value) => {
    setFilterMonths(value)
  }

  const handleSelectedChart = () => {
    setSelectedChart(selectedChart === 'radar' ? 'bar' : 'radar')
  }

  const getXaxisLabel = () => {
    if (filterMonths === '1 Month') {
      return Array.from({ length: 31 }, (_, i) => i + 1)
    }

    if (filterMonths === '3 Month') {
      return [
        "October",
        "November",
        "December"
      ]
    }

    return [
      "July",
      "August",
      "September",
      "October",
      "November",
      "December"
    ]
  }

  const RenderChart = React.memo(() => {
    if (filterMonths === '1 Month') return (
      <AreaSplineChart
        width={600}
        height={550}
        categories={categories}
        data={visualChartData?.data}
        xAxisLabel={getXaxisLabel()}
      />
    )

    if (selectedChart === 'radar') return (
      <MultipleRadarChart
        width={600}
        height={550}
        categories={categories}
        data={visualChartData?.data}
        xAxisLabel={getXaxisLabel()}
      />
    )

    return (
      <MultipleBarChart
        width={600}
        height={400}
        categories={categories}
        data={visualChartData?.data}
        xAxisLabel={getXaxisLabel()}
      />
    )
  }, [categories, filterMonths, selectedChart, visualChartData])

  return (
    <div className="visual-charts-container">
      <h2 className="title-type-3 title">Visual Charts</h2>
      <Select
        options={currentPredictionOptions}
        defaultValue={"Current"}
        placeholder={"Current"}
        className="StatusDropdown options-w-full"
        arrowSize={"15"}
        onChange={handleFilterCurrentPrediction}
      />

      <div className="flex-row gap-4">
        <Select
          options={riskOptions}
          defaultValue={"Risk"}
          placeholder={"Current"}
          className="StatusDropdown options-w-full"
          arrowSize={"15"}
          onChange={handleFilterFilterRisk}
        />

        <Select
          options={monthsOptions}
          defaultValue={"6 Month"}
          placeholder={"Current"}
          className="StatusDropdown options-w-full"
          arrowSize={"15"}
          onChange={handleFilterMonths}
        />
      </div>

      <div className="card-chart">
        {filterMonths !== '1 Month' &&
          <button className="btn-switch-chart" onClick={handleSelectedChart}>
            {selectedChart === "radar" ? (
              <BarChartIcon />
            ) : (
              <img src={radarChartImage} alt="radar charts" />
            )}
          </button>
        }

        {visualChartData && !visualChartLoading ?
          <RenderChart />
          :
          <LoaderAnimation />
        }
      </div>
    </div>
  );
})

export default VisualCharts