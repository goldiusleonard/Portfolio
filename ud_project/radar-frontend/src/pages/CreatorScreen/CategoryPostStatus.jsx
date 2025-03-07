import React from 'react'

//Props
// {
// data=[] of {title: string, total: number}
// maxProgress: number
// minHigh: number
// minMedium: number
// progressLabelFormatter: (value) => void 
// }

const CategoryPostStatus = ({
  data = [],
  maxProgress = 100,
  minHigh,
  minMedium,
  progressLabelFormatter
}) => {
  const colorVariant = {
    high: {
      bg: '#F12D2D66',
      color: '#F12D2DCC'
    },
    medium: {
      bg: '#FF8C0066',
      color: '#FF8C00CC'
    },
    low: {
      bg: '#FFE70066',
      color: '#FFE700CC'
    }
  }
  const labelVariant = {
    high: 'High',
    medium: 'Medium',
    low: 'Low'
  }

  const getVariant = (value) => {
    let variant = {
      color: colorVariant.low,
      label: labelVariant.low
    }

    if (value >= minHigh) {
      variant.color = colorVariant.high
      variant.label = labelVariant.high
      return variant
    }
    if (value >= minMedium) {
      variant.color = colorVariant.medium
      variant.label = labelVariant.medium
    }
    return variant
  }

  const ProgressBar = ({ progress, color }) => {
    return (
      <div className="progress-bar">
        <div
          className="progress"
          style={{ width: `${progress}%`, backgroundColor: color }} />
      </div>
    )
  }

  return (
    <div className="category-post-status">
      <p className="title">Category Post Status</p>

      <div className="post-list">
        {data.map((v, idx) =>
          <div
            idx={idx}
            className="post-container"
          >
            <div className="flex-row gap-10 title">
              <span>{v.title}</span>
              <span className="bold">
                {progressLabelFormatter ? progressLabelFormatter(v.value) : v.value}
              </span>
            </div>
            <div className="flex-row ">
              <div className="progress-bar-wrapper">
                <ProgressBar
                  progress={v.value / maxProgress * 100}
                  color={getVariant(v.value).color.bg}
                />
              </div>
              <span style={{ color: getVariant(v.value).color.color }}>
                {getVariant(v.value).label}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default CategoryPostStatus