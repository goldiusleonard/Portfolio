import "./HeatMap.scss";
import React, { useState, useEffect } from "react";
import CalendarHeatmap from "react-calendar-heatmap";
import "react-calendar-heatmap/dist/styles.css";
import endpoints from "../../config/config.dev";
import useApiData from "../../hooks/useApiData";
import moment from "moment";
import { UncontrolledTooltip } from "reactstrap";
import ToggleChart from "../charts/line-chart/ToggleChart";

function HeatMap({
  setHighlightedContent,
  handleToggle,
  setDate,
  year,
  profileName,
  engagementDate,
}) {
  const [show, setShow] = useState(false);
  const [popupPosition, setPopupPosition] = useState({ x: 0, y: 0 });
  const [activeColorScale, setActiveColorScale] = useState(null);
  const [showHeatmapData, setShowHeatmapData] = useState(null);
  const [filteredData, setFilteredData] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);
  const [highlightedDays, setHighlightedDays] = useState([]);

  const apiEndpoint = `${endpoints.getCreatorHeatMap}?userName=${profileName}`;
  const { data } = useApiData(apiEndpoint);

  const currentDate = new Date();
  const rawStartDate = new Date(
    currentDate.getFullYear(),
    currentDate.getMonth() - 11,
    1
  );
  const rawEndDate = new Date(
    currentDate.getFullYear(),
    currentDate.getMonth() + 1,
    0
  );

  const formatAnnualDate = (date) => date.toISOString().split("T")[0];

  const startDate = formatAnnualDate(rawStartDate);
  const endDate = formatAnnualDate(rawEndDate);

  const daysOfWeek = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];

  function formatDate(value) {
    if (!value?.date) {
      return null;
    }
    const { date, count } = value;
    const [year, month, day] = date.split("-");
    return `${count.toString().padStart(2, "0")} Flagged content on ${parseInt(
      day
    )} ${new Date(date).toLocaleString("default", {
      month: "short",
    })} ${year}`;
  }

  function getClassName(value) {
    if (!value) return "color-empty";

    const isHighlighted = selectedDate && highlightedDays.includes(value.date);
    const baseClass = `color-scale-${value.color}`;
    if (isHighlighted) {
      return `highlighted-day ${baseClass}`;
    } else if (selectedDate) {
      return `non-highlighted-day ${baseClass}`;
    } else if (activeColorScale !== value.color && activeColorScale !== null) {
      return `non-highlighted-day ${baseClass}`;
    } else {
      return activeColorScale !== null && activeColorScale === value.color
        ? `active-color-scale ${baseClass}`
        : `normal-day ${baseClass}`;
    }
  }

  const handleMouseHoverColor = (scale) => {
    setActiveColorScale(scale.toString());
  };

  const handleMouseLeaveColor = () => {
    setActiveColorScale(null);
  };

  const handleMouseHover = (event, value) => {
    setShowHeatmapData(value);
    if (value?.color === "4") {
      setShow(false);
    } else {
      setShow(true);
    }

    const offsetX = 10;
    const offsetY = 10;
    setPopupPosition({
      x: event.clientX + offsetX,
      y: event.clientY + offsetY,
    });
  };

  const handleMouseLeave = () => {
    setShow(false);
  };

  function filterCalendarByDateRange(data, startDate, endDate) {
    const start = new Date(startDate);
    const end = new Date(endDate);

    return (
      data?.calendar?.filter((entry) => {
        const entryDate = new Date(entry.date);
        return entryDate >= start && entryDate <= end;
      }) || []
    );
  }

  const handleClick = (value) => {
    setDate(null);
    if (value?.date) {
      setDate(moment(value.date).format("ddd, DD MMM, YYYY"));
    }
  };

  useEffect(() => {
    setHighlightedContent([]);
    if (data) {
      const filteredCalendar = filterCalendarByDateRange(
        data,
        startDate,
        endDate
      );
      setFilteredData(filteredCalendar);
    }
  }, [data]);

  useEffect(() => {
    if (engagementDate) {
      setSelectedDate(moment(engagementDate).format("YYYY-MM-DD"));
      handleDateChange(moment(engagementDate).format("YYYY-MM-DD"));
    }
  }, [engagementDate]);

  const handleDateChange = (date) => {
    if (selectedDate === date) {
      setSelectedDate(null);
      setHighlightedDays([]);
      setHighlightedContent([]);
    } else {
      const selectedDateData = filteredData.find((d) => d.date === date);
      if (selectedDateData) {
        setHighlightedDays([
          moment(selectedDateData.top_video_1_posted_timestamp).format(
            "yyyy-MM-DD"
          ),
          moment(selectedDateData.top_video_2_posted_timestamp).format(
            "yyyy-MM-DD"
          ),
          moment(selectedDateData.top_video_3_posted_timestamp).format(
            "yyyy-MM-DD"
          ),
        ]);
        const highlightedContent = [
          selectedDateData.top_video_1_id,
          selectedDateData.top_video_2_id,
          selectedDateData.top_video_3_id,
        ];
        setHighlightedContent(highlightedContent);
      }
      setSelectedDate(date);
    }
  };

  const totalPosts = filteredData?.reduce((sum, item) => sum + item.count, 0);

  return (
    <div className="heap-div">
      <div className="heap-box d-flex justify-content-between w-100 align-items-center">
        <p className="">
          {totalPosts || 0} Potential Risk Contents in 12 months
        </p>
        <ToggleChart active={"isHeatMap"} onClick={handleToggle} />
      </div>
      <div className="heap-div-inner-container">
        <div className="calendar-border">
          <div className="week-labels">
            {daysOfWeek.map((day) => (
              <span key={day} className="day-label" style={{ color: "grey " }}>
                {day}
              </span>
            ))}
          </div>
          <div style={{ width: "100%" }}>
            <CalendarHeatmap
              startDate={startDate}
              endDate={endDate}
              values={filteredData || []}
              classForValue={getClassName}
              onMouseOver={(event, value) => handleMouseHover(event, value)}
              onMouseLeave={handleMouseLeave}
              onClick={(value) => handleClick(value)}
              horizontal={true}
              gutterSize={8}
              showOutOfRangeDays={true}
              tooltipDataAttrs={(value) => ({
                "data-tip": formatDate(value),
              })}
            />
          </div>
          {show && (
            <div
              style={{
                display: formatDate(showHeatmapData) == null ? "none" : "flex",
                position: "absolute",
                left: `${popupPosition.x}px`,
                top: `${popupPosition.y}px`,
                zIndex: 1000,
              }}
              className="heat-map-popup"
            >
              <h5>{formatDate(showHeatmapData)}</h5>
            </div>
          )}
        </div>
        <div className="description">
          <h5>More</h5>
          {Array.from({ length: 4 }).map((_, index) => (
            <span
              key={index}
              className={`color-scale-${index + 1}`}
              onMouseOver={() => handleMouseHoverColor(index + 1)}
              onMouseLeave={handleMouseLeaveColor}
            ></span>
          ))}
          <h5>Less</h5>
          <svg
            id="legend"
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <mask
              id="mask0_4793_124792"
              maskUnits="userSpaceOnUse"
              x="0"
              y="0"
              width="16"
              height="16"
            >
              <rect width="15.8535" height="15.8535" fill="#D9D9D9" />
            </mask>
            <g mask="url(#mask0_4793_124792)">
              <path
                d="M7.26538 11.2288H8.58651V7.26538H7.26538V11.2288ZM7.92594 5.94425C8.1131 5.94425 8.26999 5.88095 8.3966 5.75434C8.5232 5.62773 8.58651 5.47085 8.58651 5.28369C8.58651 5.09653 8.5232 4.93965 8.3966 4.81304C8.26999 4.68643 8.1131 4.62313 7.92594 4.62313C7.73878 4.62313 7.5819 4.68643 7.45529 4.81304C7.32868 4.93965 7.26538 5.09653 7.26538 5.28369C7.26538 5.47085 7.32868 5.62773 7.45529 5.75434C7.5819 5.88095 7.73878 5.94425 7.92594 5.94425ZM7.92594 14.5316C7.01216 14.5316 6.15343 14.3582 5.34975 14.0114C4.54606 13.6646 3.84697 13.1939 3.25246 12.5994C2.65795 12.0049 2.1873 11.3058 1.84051 10.5021C1.49371 9.69845 1.32031 8.83972 1.32031 7.92594C1.32031 7.01216 1.49371 6.15343 1.84051 5.34975C2.1873 4.54606 2.65795 3.84697 3.25246 3.25246C3.84697 2.65795 4.54606 2.1873 5.34975 1.84051C6.15343 1.49371 7.01216 1.32031 7.92594 1.32031C8.83972 1.32031 9.69845 1.49371 10.5021 1.84051C11.3058 2.1873 12.0049 2.65795 12.5994 3.25246C13.1939 3.84697 13.6646 4.54606 14.0114 5.34975C14.3582 6.15343 14.5316 7.01216 14.5316 7.92594C14.5316 8.83972 14.3582 9.69845 14.0114 10.5021C13.6646 11.3058 13.1939 12.0049 12.5994 12.5994C12.0049 13.1939 11.3058 13.6646 10.5021 14.0114C9.69845 14.3582 8.83972 14.5316 7.92594 14.5316ZM7.92594 13.2104C9.4012 13.2104 10.6508 12.6985 11.6746 11.6746C12.6985 10.6508 13.2104 9.4012 13.2104 7.92594C13.2104 6.45069 12.6985 5.20112 11.6746 4.17725C10.6508 3.15338 9.4012 2.64144 7.92594 2.64144C6.45069 2.64144 5.20112 3.15338 4.17725 4.17725C3.15338 5.20112 2.64144 6.45069 2.64144 7.92594C2.64144 9.4012 3.15338 10.6508 4.17725 11.6746C5.20112 12.6985 6.45069 13.2104 7.92594 13.2104Z"
                fill="#22F1BF"
              />
            </g>
          </svg>
          <UncontrolledTooltip
            placement="top"
            target="legend"
            style={{ maxWidth: "100%", whiteSpace: "normal" }}
          >
            <ul
              style={{
                padding: "0 10px",
                margin: "0",
                listStylePosition: "inside",
                textAlign: "left",
              }}
            >
              <li style={{ listStyleType: "disc", paddingLeft: "15px" }}>
                Red (High Risk): Immediate action required.
              </li>
              <li style={{ listStyleType: "disc", paddingLeft: "15px" }}>
                Orange (Medium Risk): Review and monitor closely.
              </li>
              <li style={{ listStyleType: "disc", paddingLeft: "15px" }}>
                Yellow (Low Risk): Minimal concern, monitor occasionally.
              </li>
              <li style={{ listStyleType: "disc", paddingLeft: "15px" }}>
                Gray (No Risk): No action needed.
              </li>
            </ul>
          </UncontrolledTooltip>
        </div>
      </div>
    </div>
  );
}

export default HeatMap;
