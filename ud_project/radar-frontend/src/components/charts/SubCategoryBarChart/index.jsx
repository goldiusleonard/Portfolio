import React from 'react';
import './SubCategoryBarChart.scss';
import LoaderAnimation from '../../LoaderAnimation';
import { useNavigate } from 'react-router-dom';

const SubCategoryBarChart = ({ yData, data, loading }) => {
  const navigation = useNavigate();

  const values = yData?.data;
  const categories = data ? data["x-axis"] : [];
  const totalScanned = data?.scanned_content;

  // Sorting the categories based on values
  const sortedData =
    categories &&
    categories
      .map((category, index) => ({
        category,
        value: values[index],
      }))
      .sort((a, b) => b.value - a.value);

  return loading ? (
    <LoaderAnimation />
  ) : (
    <div className="subCategory-charts-wrapper">
      <div className="subCategory-title">Sub Category (10)</div>
      <div className="subCategory-charts">
        {sortedData &&
          sortedData.map(({ category, value }, index) => (
            <div
              className="subCategory-chart"
              key={index}
              onClick={() =>
                navigation(`/category-insight`, {
                  state: { subCategoryRoute: category },
                })
              }
            >
              <div className="chart-component">
                <div className="chart-title">
                  <div className="main-title">{category}</div>
                  <div className="sub-title">{value}</div>
                </div>
                <div className="bar-chart-wrapper">
                  <SingleBarChart
                    size={(value / Math.max(...values)) * 100}
                    category={category}
                  />
                </div>
              </div>
              <svg
                width="32"
                height="33"
                viewBox="0 0 32 33"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                // onClick={() => navigation(`/category`, { state: { subCategoryRoute: category } })}
              >
                <g filter="url(#filter0_b_4209_28964)">
                  <path
                    opacity="0.8"
                    fillRule="evenodd"
                    clipRule="evenodd"
                    d="M18.5977 16.4754L12.6006 22.5229C12.1567 22.971 12.1567 23.6939 12.6006 24.142C12.8121 24.3561 13.1006 24.4766 13.4015 24.4766C13.7024 24.4766 13.9909 24.3561 14.2024 24.142L21.0004 17.2861C21.4456 16.8385 21.4456 16.1147 21.0004 15.667L14.2027 8.81108C13.9909 8.59699 13.7024 8.47656 13.4015 8.47656C13.1006 8.47656 12.8121 8.59699 12.6003 8.81108C12.1568 9.25932 12.1568 9.98216 12.6009 10.4303L18.5977 16.4754Z"
                    fill="white"
                  />
                </g>
                <defs>
                  <filter
                    id="filter0_b_4209_28964"
                    x="-180"
                    y="-179.523"
                    width="392"
                    height="392"
                    filterUnits="userSpaceOnUse"
                    colorInterpolationFilters="sRGB"
                  >
                    <feFlood floodOpacity="0" result="BackgroundImageFix" />
                    <feGaussianBlur in="BackgroundImageFix" stdDeviation="90" />
                    <feComposite
                      in2="SourceAlpha"
                      operator="in"
                      result="effect1_backgroundBlur_4209_28964"
                    />
                    <feBlend
                      mode="normal"
                      in="SourceGraphic"
                      in2="effect1_backgroundBlur_4209_28964"
                      result="shape"
                    />
                  </filter>
                </defs>
              </svg>
            </div>
          ))}
      </div>
    </div>
  );
};

const SingleBarChart = ({ size, category }) => {
  const navigation = useNavigate();
  return (
    <div className="bar-container">
      <div className="background-template"></div>
      <div
        className="bar"
        style={{ width: `${size}%` }}
        onClick={() =>
          navigation(`/category-insight`, {
            state: { subCategoryRoute: category },
          })
        }
      ></div>
    </div>
  );
};

export default SubCategoryBarChart;
