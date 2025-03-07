import moment from 'moment';
import React, { useState } from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';
// import './dataPicker.scss';

const DateRangePicker = ({ sDate, eDate, startValue, endValue }) => {
  const [startDate, setStartDate] = useState(startValue);
  const [endDate, setEndDate] = useState(endValue);

  const handleStartDateChange = (date) => {
    setStartDate(date);
    sDate(date);
    if (endDate && date && endDate < date) {
      setEndDate(null);
      eDate(null);
    }
  };

  const handleEndDateChange = (date) => {
    setEndDate(date);
    eDate(date);
  };

  const getHighlightDates = () => {
    if (!startDate || !endDate) {
      return [];
    }
    const dates = [];
    let currentDate = new Date(startDate);
    while (currentDate <= endDate) {
      dates.push(new Date(currentDate));
      currentDate.setDate(currentDate.getDate() + 1);
    }
    return dates;
  };

  return (
    <div className="date-range-picker">
      <div className="date-labels">
        <div className="date-label">
          <span>Start date:</span>
          <div className="date-display">
            {startDate
              ? moment(startDate).format("D MMM YYYY")
              : "Select start date"}
          </div>
        </div>
        <div className="date-label">
          <span>End Date:</span>
          <div className="date-display">
            {endDate ? moment(endDate).format("D MMM YYYY") : "Select end date"}
          </div>
        </div>
      </div>
      <div className="calendars">
        <div className="calendar">
          <DatePicker
            selected={startDate}
            onChange={handleStartDateChange}
            startDate={startDate}
            endDate={endDate}
            selectsStart
            inline
            calendarClassName="custom-datepicker"
            highlightDates={getHighlightDates()}
          />
        </div>
        <div className="calendar">
          <DatePicker
            selected={endDate}
            onChange={handleEndDateChange}
            startDate={startDate}
            endDate={endDate}
            selectsEnd
            minDate={startDate}
            inline
            calendarClassName="custom-datepicker"
            highlightDates={getHighlightDates()}
            disabled={!startDate}
          />
        </div>
      </div>
    </div>
  );
};

export default DateRangePicker;
