import React from 'react'

const CategoryDetailCard = ({
  category,
  totalSubCategory,
  totalTopics,
  aboutCategory,
  sentiment,
  risk,
}) => {
  return (
    <div className="card-category-detail">
      <h2 className="title-type-3 title">Category Detail</h2>
      <div className="card-category-detail-content">
        <div className="card-category-content row-justify-between">
          <span className="label">Category</span>
          <span className="value">{category}</span>
        </div>

        <div className="card-category-content row-justify-between">
          <span className="label">Total Sub-Category</span>
          <span className="value">{totalSubCategory}</span>
        </div>

        <div className="card-category-content row-justify-between">
          <span className="label">Total Topic</span>
          <span className="value">{totalTopics}</span>
        </div>
      </div>

      <div className="card-category-content sentiment">
        <span className="label">Sentiment</span>
        <span className="value">
          {sentiment.charAt(0).toUpperCase() + sentiment.slice(1)}
        </span>
      </div>

      <div className="risk-levels card-wrap">
        <div className="high">
          <span className="r-label">High</span>
          <span>{risk.high}%</span>
        </div>
        <div className="medium">
          <span className="r-label">Medium</span>
          <span>{risk.medium}%</span>
        </div>
        <div className="low">
          <span className="r-label">Low</span>
          <span>{risk.low}%</span>
        </div>
      </div>

      <div className="card-category-content col">
        <span className="label">About Category</span>
        <span className="value">{aboutCategory}</span>
      </div>
    </div>
  );
};

export default CategoryDetailCard