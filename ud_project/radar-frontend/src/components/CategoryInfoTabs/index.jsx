import React, { useEffect, useMemo, useState } from "react";
import News from "../CategoryNews/News";
import VisualCharts from "../VisualCharts";

const TabUI = ({ categories, subCategory, currentCategory, categoryDetails, words, justification, totalReportedCases }) => {
  const [activeTab, setActiveTab] = useState("Description");

  const tabs = ["Description", "Visuals"];
  if (!currentCategory || currentCategory?.length === 1) {
    tabs.push("News");
  }

  useEffect(() => {
    if (activeTab === "News" && currentCategory?.length > 1) {
      setActiveTab("Description");
    }
  }, [currentCategory?.length, activeTab]);

  const uppercaseFirstLetter = (v) => {
    if (!v.length) return v

    return `${v[0].toUpperCase()}${v.substr(1)}`
  }

  const shouldTabAutoScrollVertiacal = useMemo(() => {
    if (activeTab === 'Description' && currentCategory?.length > 1) {
      return true
    }

    return false
  }, [activeTab, currentCategory])

  return (
    <div className="tabs-wrapper">
      {/* Tabs Navigation */}
      <div className="tabs-container">
        {tabs.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`tab ${activeTab === tab ? "active" : ""}`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className={`tab-content ${shouldTabAutoScrollVertiacal ? 'overflow-y-auto' : ''}`}>
        {activeTab === "Description" && (
          <div>
            {/* Category Detail */}
            {currentCategory?.length == 1 ? (
              <h2 className="title-type-3 section-title">Category Detail</h2>
            ) : (
              <h2 className="title-type-3 section-title">Cases Summary</h2>
            )}
            {currentCategory?.length > 1 && (
              <div className="detail-row">
                <span className="label">Total Reported Cases</span>
                <span className="value">{totalReportedCases}</span>
              </div>
            )}
            {currentCategory?.length == 1 && (
              <>
                <div className="detail-row">
                  <span className="label">Category</span>
                  <span className="value">{categoryDetails[0]?.name}</span>
                </div>
                <div className="detail-row">
                  <span className="label">Sub-Category</span>
                  <span className="value">{subCategory.subCategory || '-'}</span>
                </div>
                <div className="detail-row">
                  <span className="label">Topic</span>
                  <span className="value">{subCategory.topic || '-'}</span>
                </div>
                <div className="about-category">
                  <h3 className="title-type-3">About Category</h3>
                  <p>
                    {categoryDetails[0]?.about ? categoryDetails[0]?.about : 'N/A'}
                  </p>
                </div>

                {/* Evaluation Summary */}
                <h2 className="title-type-3 section-title pt-3">
                  Evaluation Summary
                </h2>
                <div className="detail-row">
                  <span className="label">Sentiment</span>
                  <span className="value">
                    {categoryDetails[0]?.sentiment ? uppercaseFirstLetter(categoryDetails[0]?.sentiment) : "N/A"}
                  </span>
                </div>
              </>
            )}
            <div className="about-category">
              <h3 className="title-type-3">Justification</h3>
              <p className="justification-note">
                {justification ??
                  "No justification for this category"}
              </p>
            </div>

            {/* Keyword Trends */}
            <h2 className="title-type-3 section-title pt-3">Keyword Trends</h2>
            <div className="keyword-container">
              {words.length ?
                words?.map((keyword, idx) => (
                  <span key={idx} className="keyword">
                    {keyword}
                  </span>
                )) : 'N/A'}
            </div>

            {currentCategory?.length > 1 && (
              <div className="pt-3 news-list-container">
                <News
                  categories={currentCategory}
                />
              </div>
            )}
          </div>
        )}

        {activeTab === "Visuals" && (
          <VisualCharts categories={categories} />
        )}

        {activeTab === "News" && (
          <News
            categories={currentCategory}
          />
        )}
      </div>
    </div>
  );
};

export default TabUI;
