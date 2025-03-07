import React from "react";



function KeywordListNotEditable({keywordList, isUsernameCrawler, isKeywordCrawler}) {
  return (
    <div className="keyword-list-simple">
      <div className="category-breadcrumb-title">
   
        {isUsernameCrawler ? "Username" : "Keyword"}
        </div>
      <ul className="overflow-auto key-words-ul mt-2">
        {keywordList && keywordList.map((keyword, index) => (
          <li key={index} className="category-breadcrumb mb-1">
            {keyword}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default KeywordListNotEditable;
