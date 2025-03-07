import React, { useState } from "react";
import arrowDown from "../../assets/icons/select_arrow.svg";
import KeywordList from "../../components/KeywordList";
import moment from "moment";
import RangeDatePicker from "../../components/DatePicker/RangeDatePicker";

//Options
// {
//   startDate: string
//   endDate: string
//   keywords: [] of string
//   usernames: [] of string
//   onChangeStartDate: (date) => void
//   onChangeEndDate: (date) => void
//   onChangeKeywords: (list of keywords) => void
//   onChangeUsernames: (list of usernames) => void
// }

const KeywordSection = ({
  startDate,
  endDate,
  keywords,
  usernames,
  onChangeStartDate,
  onChangeEndDate,
  onChangeKeywords,
  onChangeUsernames,
  showEditableScreen,
  isKeywordCrawler,
  isUsernameCrawler,
  setEditedAgentData
}) => {
  const [showDates, setShowDates] = useState(false);

  const handleDateToggle = () => {
    setShowDates(!showDates);
  };

  return (
    <div className="right-align">
      <div
        className="calendar-wrapper"
        style={{ marginBottom: "1rem", marginLeft: 4 }}
      >
        <div className="calendar-title">Crawling Progress Period</div>
        <div
          className="validity-date-text"
          style={{ width: "fit-content" }}
          onClick={handleDateToggle}
        >
          {startDate
            ? `${moment(startDate).format("D MMM YYYY")} - ${moment(
                endDate
              ).format("D MMM YYYY")}`
            : "Select Crawling Progress Period"}
          <img className="arrow-icon" src={arrowDown} alt="arrowDown" />
        </div>
        {showDates && (
          <RangeDatePicker
            handleShow={handleDateToggle}
            showDates={showDates}
            sDate={onChangeStartDate}
            eDate={onChangeEndDate}
            startValue={startDate}
            endValue={endDate}
          />
        )}
      </div>

      <KeywordList
        keywords={keywords}
        usernames={usernames}
        onChangeKeywords={onChangeKeywords}
        onChangeUsernames={onChangeUsernames}
        isKeywordCrawler={isKeywordCrawler}
        isUsernameCrawler={isUsernameCrawler}
        setEditedAgentData={setEditedAgentData}
      />
    </div>
  );
};

export default KeywordSection;
