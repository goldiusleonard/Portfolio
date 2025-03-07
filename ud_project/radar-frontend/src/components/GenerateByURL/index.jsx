import React, { useEffect, useState } from "react";
// import './GenerateByURL.scss';
import { CloseIcon } from "../../assets/icons";
import pasteIcon from "../../assets/icons/clipboard-paste.svg";
import { useGlobalData } from "../../App";

const GenerateByURL = ({ URLList, setEditedAgentData, editedAgentData }) => {
 const [url, setURL] = useState("");
  const [urls, setURLs] = useState(URLList || []);
  const [error, setError] = useState(false);

  const isValidTikTokURL = (url) => {
    const tiktokRegex = /^https:\/\/(www\.)?tiktok\.com\/@[\w.-]+\/video\/\d+$/;
    return tiktokRegex.test(url);
  };

  const handleURLChange = (e) => {
    setURL(e.target.value);
    setError(false);
  };

  const addNewURL = () => {
    if (!url.trim() || !isValidTikTokURL(url)) {
      setError(true);
      return;
    }
  
    setURLs((prevURLs) => {
      const updatedURLs = [...prevURLs, url];
      setEditedAgentData((prev) => ({ ...prev, URLList: updatedURLs }));
  
      return updatedURLs;
    });
  
    setURL("");
    setError(false);
  };
  
  const removeURL = (index) => {
    setURLs((prevURLs) => {
      const updatedURLs = prevURLs.filter((_, i) => i !== index);
      setEditedAgentData((prev) => ({ ...prev, URLList: updatedURLs }));
  
      return updatedURLs;
    });
  };

  useEffect(() => {
    setEditedAgentData((prev) => ({ ...prev, URLList: urls }));
  }, [urls, setEditedAgentData]); 
  
  
  const truncateURL = (url) => {
    const maxLength = Math.ceil(url.length / 1.5);
    return `${url.substring(0, maxLength)}...`;
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      addNewURL();
    }
  };

  return (
    <div className="generate-by-url-wrapper">
      <h2 className="title-type-3 mb-2">Generate by URL</h2>

      <div className="d-flex flex-column justify-content-between">
        <div>
          <div className="url-input-container">
            <input
              type="text"
              value={url}
              onChange={handleURLChange}
              onKeyDown={handleKeyPress}
              placeholder="Copy and paste the URL"
              className={`url-input ${error ? "error" : ""}`}
            />
            <img
              src={pasteIcon}
              alt="paste icon"
              className="add-url-arrow"
              onClick={addNewURL}
              role="button"
              tabIndex={0}
            />
          </div>
          {error && (
            <div className="url-error-msg">
              This URL is invalid. Please check URL or content availability.
            </div>
          )}
        </div>
      </div>
      <div className="url-tags overflow-auto key-words-ul ">
        {urls?.map((savedUrl, index) => (
          <div key={index} className="url-tag category-breadcrumb mb-1">
            {truncateURL(savedUrl)}
            <span onClick={() => removeURL(index)} className="close-icon">
              <CloseIcon fill="#fff" />
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default GenerateByURL;
