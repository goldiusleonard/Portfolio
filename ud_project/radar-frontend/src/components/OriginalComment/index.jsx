import React, { useState } from "react";
import "./originalComment.scss";
import { Timeline } from "primereact/timeline";
import sample_content from "../../assets/images/sample_content_image.png";
import sample_commenter from '../../assets/images/sample_comment_image.png';
import Collapse from "./Collapse";
import Comment from "./Comment";
import moment from "moment";
import LoaderAnimation from "../LoaderAnimation";
import OpenContentModal from "../Modal/OpenContentModal";
import { useCallback } from "react";

import { commentImage } from "../../assets/images";


const OriginalComment = ({ data, loading, showComments }) => {
	// const [activeTab, setActiveTab] = useState("originalContent");
	// const { data: lawData, loadingData } = useApiData(endpoints.getLaws);
	const [isOpenContentPreviewModal, setOpenContentPreviewModal] = useState(false);
	const [language, setLanguage] = useState('en');

	const handleLanguageChange = (e) => {
		setLanguage(e.target.value);
	};

	// const handleTabClick = (tab) => {
	// 	setActiveTab(tab);
	// };

	const toggleContentPreview = useCallback(() => {
		setOpenContentPreviewModal(prevState => !prevState);
	}, []);

	// this is temprory fix for wrong data format
	const safeJsonParse = (jsonString) => {

		try {
			return JSON.parse(jsonString)['Video Summary'];
		} catch (error) {
			console.error('JSON parsing error:', error);
			return jsonString?.replace(/^\{"Video Summary":"|"\}$/g, '')
		}
	};
	const parsedSummary = safeJsonParse(data?.video_summary)

	return (
    <div className="original-comment-container h-100">
      {loading ? (
        <LoaderAnimation />
      ) : (
        <>
          <div className="original-content-bottom-container ">
            <img
              src={commentImage}
              alt="content"
              className="h-30 object-scale-down"
              height={"45%"}
            />
            <div>
              <div className="original-content-tags-container d-flex overflow-x-scroll">
                {data?.content_tags?.[0] ? (
                  data.content_tags[0].split(",").map((tag, index) => (
                    <div className="original-content-tag" key={index}>
                      {tag}
                    </div>
                  ))
                ) : (
                  <div className="no-tags"></div>
                )}
              </div>
              <div className="original-content-details ">
                <Collapse title="Content Summary">
                  {data?.video_summary ? (
                    <div className="justification">
                      <p>{parsedSummary}</p>
                    </div>
                  ) : (
                    <div className="empty-comment">No summary found </div>
                  )}
                </Collapse>
                <Collapse title="Content Caption">
                  <div className="justification">
                    <p>{data?.content_description}</p>
                  </div>
                </Collapse>
                {showComments && (
                  <Collapse title="Content Comments">
                    {data && data?.comment_content?.length > 0 ? (
                      <div className="comment-content">
                        <div className="comment-time-stamp">
                          <span>Latest Update:</span>
                          <span>
                            {moment(data?.scrappedDate).format("D/MM/YYYY")}
                          </span>
                        </div>
                        {data?.comment_content?.map((item) => {
                          return (
                            <Comment
                              img_url={
                                item.img_url ? item.img_url : sample_commenter
                              }
                              name={item.user_handle}
                              comment={item.comment_text}
                              likes={item.comment_like_count}
                              shares={item.shares}
                              key={item?.user_handle}
                            />
                          );
                        })}
                      </div>
                    ) : (
                      <div className="empty-comment">No comments found </div>
                    )}
                  </Collapse>
                )}
                <Collapse title="Justification" expandableButton={false}>
                  <div className="language-toggle">
                    <div className="language-toggle-wrapper">
                      <label
                        className={`radio-label ${
                          language === "en" ? "active" : ""
                        }`}
                      >
                        <input
                          type="radio"
                          value="en"
                          checked={language === "en"}
                          onChange={handleLanguageChange}
                        />
                        English
                      </label>
                      <label
                        className={`radio-label ${
                          language === "ms" ? "active" : ""
                        }`}
                      >
                        <input
                          type="radio"
                          value="ms"
                          checked={language === "ms"}
                          onChange={handleLanguageChange}
                        />
                        Malay
                      </label>
                    </div>
                  </div>
                  <div className="justification">
                    <ul>
                      {language === "en"
                        ? data?.content_justifications?.map((item) => (
                            <li
                              key={item.justification}
                              className="justification-item"
                            >
                              <span className="justification-number">
                                {item.justification}.
                              </span>
                              <div className="justification-text">
                                {item.justification_text}
                              </div>
                            </li>
                          ))
                        : data?.malay_justification?.map((item) => (
                            <li
                              key={item.justification}
                              className="justification-item"
                            >
                              <span className="justification-number">
                                {item.justification}.
                              </span>
                              <div className="justification-text">
                                {item.justification_text}
                              </div>
                            </li>
                          ))}
                    </ul>
                  </div>
                </Collapse>

                <Collapse
                  title="Standards & Regulations"
                  expandableButton={false}
                >
                  <div className="law-violations">
                    <h4>Law Violations</h4>
                    {data?.content_law_regulated &&
                    data.content_law_regulated["Law Violations"] &&
                    Object.keys(data.content_law_regulated["Law Violations"])
                      .length > 0 ? (
                      Object.entries(
                        data.content_law_regulated["Law Violations"]
                      ).map(([law, details]) => {
                        const header =
                          law.replace(/_/g, " ").toUpperCase() ===
                          "AKTA HASUTAN"
                            ? "SEDITION ACT"
                            : law.replace(/_/g, " ").toUpperCase();

                        return (
                          <div key={law} className="law-violation-item">
                            <h4>{header}</h4>
                            <ul>
                              <li>
                                <strong>Sections Violated: </strong>
                                {details["Sections Violated"] || "N/A"}
                              </li>
                              <li>
                                <strong>Violation Analysis: </strong>
                                {typeof details["Violation Analysis"] ===
                                "string"
                                  ? details["Violation Analysis"]
                                  : Object.entries(
                                      details["Violation Analysis"]
                                    ).map(([section, analysis]) => (
                                      <p key={section}>
                                        <strong>{section}: </strong>
                                        {analysis}
                                      </p>
                                    ))}
                              </li>
                            </ul>
                          </div>
                        );
                      })
                    ) : (
                      <div className="law-violation-item">
                        <p>
                          No law violations available or data is still loading.
                        </p>
                      </div>
                    )}
                  </div>
                </Collapse>
              </div>
            </div>
          </div>
        </>
      )}
      <OpenContentModal
        isOpen={isOpenContentPreviewModal}
        data={data}
        toggle={toggleContentPreview}
      />
    </div>
  );
};

export function Category({ subCategoryRoute, subCategoryTopic }) {
	return (
		<div className="categories-wrapper">
			<div className="categories-container">
				<div>Category</div>
				<div style={{ marginLeft: '10px' }}>Hate Speech</div>
			</div>
			<div className="categories-container">
				<div>Sub-Category</div>
				<div className="text-capitalize text-truncate">{subCategoryRoute || '___'}</div>
			</div>
			<div className="categories-container">
				<div>Topic</div>
				<div className="text-capitalize text-truncate">{subCategoryTopic || '___'}</div>
			</div>
		</div>
	);
}

export function CategoryDisplay({ categories, subCategories, topics }) {
	return (
		<div className="category-display">
			<div className="category-row">
				<div className="category-label">Category</div>
				<div className="category-value">
					{categories.map((category, index) => (
						<span key={index} className={`category-tag ${category.toLowerCase().replace(/\s+/g, '')}`}>
							{category}
						</span>
					))}
				</div>
			</div>
			<div className="category-row">
				<div className="category-label">Sub-Category</div>
				<div className="category-value">
					{subCategories.map((subcategory, index) => (
						<span key={index}>{subcategory}</span>
					))}
				</div>
			</div>
			<div className="category-row">
				<div className="category-label">Topic</div>
				<div className="category-value">{topics.join(", ")}</div>
			</div>
		</div>
	);
};

export default OriginalComment;
