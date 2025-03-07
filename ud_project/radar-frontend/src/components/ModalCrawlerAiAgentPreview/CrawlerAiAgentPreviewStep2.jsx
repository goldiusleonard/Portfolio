import React, { useState } from 'react'
import Select from "../Select/Select"
import DateRangePicker from "../DatePicker"
import moment from "moment"
import arrowDown from '../../assets/icons/select_arrow.svg'

const CrawlerAiAgentPreviewStep2 = ({
  category,
  subCategory,
  riskPriorityOptions,
  fileNameOptions,
  riskPriority,
  postDate,
  fileName,
  onChangeRiskPriority,
  onChangePostDate,
  onChangeFileName
}) => {
  const selectCategories = ["Scam", "3R", "ATIPSOM", "Sexual and Family"]
  const showRiskPriorityAsInput = selectCategories.includes(selectCategories)
  const [showDates, setShowDates] = useState(false);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");

  const onShowDate = () => {
    setShowDates((prevState) => !prevState);
  };

  const TextInput = ({ placeholder, value, onChange }) => {
    return (
      <input
        className="input"
        placeholder={placeholder}
        value={value}
        onChange={onChange}
      />
    );
  };

  const handleEndDate = (date) => {
    setEndDate(date);
    if (startDate) {
      setShowDates(false);
    }
  };

  const handleStartDate = (date) => {
    setStartDate(date);
  };
  return (
    <div className="crawler-ai-agent-step-2">
      <div className="card">
        <div>
          <h2 className="title">Risk Priority in Classification</h2>
          <span className="text-info-card">
            Type a description of each risk level category based on the
            parameters you want.
          </span>
        </div>

        <div className="risk-priority-container">
          <div className="risk-priority-content">
            <span className="left-section text-info-card">High</span>
            <div className="right-section">
              {showRiskPriorityAsInput ? (
                <TextInput
                  placeholder="Type Priority in Classification for High Risk"
                  value={riskPriority.high}
                  onChange={(e) => onChangeRiskPriority(e.target.value, "high")}
                />
              ) : (
                <Select
                  options={
                    riskPriorityOptions[category][subCategory]["High Risk"]
                  }
                  placeholder="Select Priority in Classification for High Risk"
                  className="StatusDropdown options-w-full"
                  arrowSize={"15"}
                  defaultValue={riskPriority.high}
                  onChange={(v) => onChangeRiskPriority(v, "high")}
                />
              )}
              <span className="text-info-card">
                Example: Explicit Scam Schemes: Promoting or advertising
                fraudulent cryptocurrency investment schemes designed to deceive
                individuals into financial loss.
              </span>
            </div>
          </div>

          <div className="risk-priority-content">
            <span className="left-section text-info-card">Medium</span>
            <div className="right-section">
              {showRiskPriorityAsInput ? (
                <TextInput
                  placeholder="Type Priority in Classification for Medium Risk"
                  value={riskPriority.medium}
                  onChange={(e) =>
                    onChangeRiskPriority(e.target.value, "medium")
                  }
                />
              ) : (
                <Select
                  options={
                    riskPriorityOptions[category][subCategory]["Medium Risk"]
                  }
                  placeholder="Select Priority in Classification for Medium Risk"
                  className="StatusDropdown options-w-full"
                  arrowSize={"15"}
                  defaultValue={riskPriority.medium}
                  onChange={(v) => onChangeRiskPriority(v, "medium")}
                />
              )}
              <span className="text-info-card">
                Example: Unverifiable Claims About Projects: Promoting
                cryptocurrency projects with unsubstantiated claims about
                potential profits, partnerships, or technologies.
              </span>
            </div>
          </div>

          <div className="risk-priority-content">
            <span className="left-section text-info-card">Low</span>
            <div className="right-section">
              {showRiskPriorityAsInput ? (
                <TextInput
                  placeholder="Type Priority in Classification for Low Risk"
                  value={riskPriority.low}
                  onChange={(e) => onChangeRiskPriority(e.target.value, "low")}
                />
              ) : (
                <Select
                  options={
                    riskPriorityOptions[category][subCategory]["Low Risk"]
                  }
                  placeholder="Select Priority in Classification for Low Risk"
                  className="StatusDropdown options-w-full"
                  arrowSize={"15"}
                  defaultValue={riskPriority.low}
                  onChange={(v) => onChangeRiskPriority(v, "low")}
                />
              )}
              <span className="text-info-card">
                Unintentional Sharing of Incorrect Information: Spreading
                outdated or inaccurate details about cryptocurrencies or
                projects without malicious intent.
              </span>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="title">Posting Date</h2>
        <div className="calendar-wrapper">
          <div className="validity-date-text" onClick={onShowDate}>
            <span className="placeholder">
              {startDate
                ? `${moment(startDate).format("D MMM YYYY")} - ${moment(
                    endDate
                  ).format("D MMM YYYY")}`
                : "Select Date Posting"}
            </span>
            <img className="arrow-icon" src={arrowDown} alt="arrowDown" />
          </div>
          {showDates && (
            <div className="calendar-popup">
              <DateRangePicker
                showDates={showDates}
                sDate={handleStartDate}
                eDate={handleEndDate}
                endValue={endDate}
                startValue={startDate}
              />
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <h2 className="title">Upload Supported Legal Document</h2>
        <Select
          options={fileNameOptions}
          placeholder="Select Legal Document"
          className="StatusDropdown options-w-full"
          arrowSize={"15"}
          defaultValue={fileName}
          onChange={onChangeFileName}
        />
      </div>
    </div>
  );
}

export default CrawlerAiAgentPreviewStep2