import moment from "moment";
import React, { useState } from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";

const RangeDatePicker = ({
  sDate,
  eDate,
  startValue,
  endValue,
  handleShow,
}) => {
  const [startDate, setStartDate] = useState(new Date());
  const [endDate, setEndDate] = useState(null);
  const onChange = (dates) => {
    const [start, end] = dates;

    if (start !== null) {
      sDate(start);
      setStartDate(start);
    }

    if (end !== null) {
      eDate(end);
      setEndDate(end);
      handleShow(false);
    }
  };

  return (
    <div className="date-range-picker">
      <div className="date-labels">
        <div className="date-label">
          <div className="date-display">
            {startDate ? moment(startDate).format("D MMM YYYY") : "Start Date"}
          </div>
        </div>
        <div className="date-label">
          <div className="date-display">
            {endDate ? moment(endDate).format("D MMM YYYY") : "End Date"}
          </div>
        </div>
      </div>
      <div className="calendars">
        <div className="calendar">
          <DatePicker
            selected={startDate}
            onChange={onChange}
            startDate={startDate}
            endDate={endDate}
            selectsRange
            inline
          />
        </div>
      </div>
    </div>
  );
};

export default RangeDatePicker;
