import React from 'react'
import CarouselCrawlerAiAgentPreview from "./CarouselCrawlerAiAgentPreview"
import useApiData from '../../hooks/useApiData'
import endpoints from '../../config/config.dev'

const CrawlerAiAgentPreviewStep1 = ({
  data, agentID
}) => {
  const previewDataStep1 = useApiData(`${endpoints.postCrawlerPreviewStep1}${agentID}/crawler-preview`)

  return (
    <div className="crawler-ai-agent-step-1">
      <div className="left-side">
        <CarouselCrawlerAiAgentPreview images={data.images} />
      </div>

      <div className="right-side">
        <div className="card-content">
          <h2 className="title">
            Category Detail
          </h2>

          <div className="card-category-detail">
            <span className="label">Category</span>
            <span className="value">{previewDataStep1.data?.categoryDetail.category}</span>
          </div>
          <div className="card-category-detail">
            <span className="label">Sub-Category</span>
            <span className="value">{previewDataStep1.data?.categoryDetail.subCategory}</span>
          </div>
          <div className="card-category-detail">
            <span className="label">Total Scanned Content</span>
            <span className="value">{previewDataStep1.data?.categoryDetail.totalScannedContent}</span>
          </div>
        </div>

        <div className="card-content">
          <h2 className="title">
            Evaluation Summary
          </h2>
          <div className="card-category-detail align-vertical">
            <span className="label">Content Summary</span>
            <span className="value">
              {previewDataStep1.data?.videoDetails[0]["evaluationSummary"]["contentSummary"]}
            </span>
          </div>
        </div>

        {data.keywordListContent && data.keywordListContent.length &&
          <div className="card-content">
            <h2 className="title">
              The keyword related to this content
            </h2>
            {data.keywordListContent.map((v, idx) =>
              <div
                key={idx}
                className="card-category-detail"
              >
                <span className="label">{v.keyword}</span>
                <span className="value">
                  {v.total}/{data.totalContent.toLocaleString()}
                </span>
              </div>
            )}
          </div>
        }
      </div>
    </div>
  )
}

export default CrawlerAiAgentPreviewStep1