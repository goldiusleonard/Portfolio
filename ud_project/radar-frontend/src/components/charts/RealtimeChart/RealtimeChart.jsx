import React, { useState, useEffect, useRef, useMemo } from "react";

const RealtimeChart = ({
  data: externalData,
  width = 1200,
  height = 200,
  onDataUpdate,
}) => {
  const [internalData, setInternalData] = useState([]);
  const [isScrolledToEnd, setIsScrolledToEnd] = useState(true);
  const containerRef = useRef(null);
  const prevDataRef = useRef([]);

  // Use external data if provided, otherwise use internal state
  const data = externalData || internalData;

  const TIME_WIDTH = 120;
  const LABEL_WIDTH = 80;
  const TIME_LABEL_MARGIN = 5;
  const PADDING_LEFT = 20;

  const STATUS_LEVELS = {
    high: height * 0.1,
    medium: height * 0.5,
    low: height * 0.9,
  };

  const styles = useMemo(
    () => ({
      wrapper: {
        marginTop: "5px",
        position: "relative",
        width: "100%",
        maxWidth: `${width / 16}rem`, // 1200px / 16
        height: `${(height + 40) / 16}rem`, // (200px + 40px) / 16
        backgroundColor: "#0F1114",
        borderRadius: "5px",
      },
      container: {
        width: "100%",
        height: `${(height + 40) / 16}rem`, // (200px + 40px) / 16
        backgroundColor: "#0F1114",
        position: "relative",
        overflow: "hidden",
      },
      scrollContainer: {
        width: `calc(100% - ${LABEL_WIDTH / 16}rem)`, // 80px / 16
        height: "100%",
        overflowX: "auto",
        scrollbarWidth: "none",
        msOverflowStyle: "none",
        position: "absolute",
        left: `${LABEL_WIDTH / 16}rem`, // 80px / 16
        "&::-webkit-scrollbar": {
          display: "none",
        },
      },
      fixedLabels: {
        position: "absolute",
        left: 0,
        top: 0,
        width: `${LABEL_WIDTH / 16}rem`, // 80px / 16
        height: `${height / 16}rem`, // 200px / 16
        backgroundColor: "#0F1114",
        zIndex: 2,
      },
      horizontalLine: {
        stroke: "#333",
        strokeWidth: "1",
      },
      timeText: {
        fill: "#9CA3AF",
        fontSize: "12px",
      },
      statusText: {
        fill: "#9CA3AF",
        fontSize: "14px",
        dominantBaseline: "middle",
      },
      dataLine: {
        fill: "none",
        stroke: "#fff",
        strokeWidth: "2",
        strokeLinecap: "round",
        strokeLinejoin: "round",
        transition: "d 0.3s ease-in-out",
      },
    }),
    [height, width]
  );

  const handleScroll = () => {
    if (containerRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = containerRef.current;
      const isAtEnd = Math.abs(scrollWidth - clientWidth - scrollLeft) < 10;
      setIsScrolledToEnd(isAtEnd);
    }
  };

  useEffect(() => {
    if (data.length > 0) {
      prevDataRef.current = data;
    }
  }, [data]);

  useEffect(() => {
    if (externalData) return;

    const interval = setInterval(() => {
      const now = new Date();
      setInternalData((prevData) => {
        const lastStatus =
          prevData.length > 0 ? prevData[prevData.length - 1].y : "low";
        const possibleStatus = getPossibleNextStatus(lastStatus);
        const newStatus =
          possibleStatus[Math.floor(Math.random() * possibleStatus.length)];

        const newData = [
          ...prevData,
          {
            time: now,
            y: newStatus,
          },
        ];

        const filteredData = newData.filter(
          (d) => now - d.time < 30 * 60 * 1000
        );

        if (onDataUpdate) {
          onDataUpdate(filteredData);
        }

        return filteredData;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [externalData, onDataUpdate]);

  const getPossibleNextStatus = (currentStatus) => {
    switch (currentStatus) {
      case "low":
        return ["low", "medium"];
      case "medium":
        return ["low", "medium", "high"];
      case "high":
        return ["medium", "high"];
      default:
        return ["low", "medium", "high"];
    }
  };

  useEffect(() => {
    if (containerRef.current && data.length > 0 && isScrolledToEnd) {
      containerRef.current.scrollTo({
        left: containerRef.current.scrollWidth,
        behavior: "smooth",
      });
    }
  }, [data, isScrolledToEnd]);

  const formatTime = (date) => {
    return date.toLocaleTimeString("en-US", {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  const totalWidth = Math.max(width, data.length * TIME_WIDTH);

  const generatePath = () => {
    if (data.length < 2) return "";

    const points = data.map((d, i) => ({
      x: i * TIME_WIDTH,
      y: STATUS_LEVELS[d.y],
    }));

    const path = points.reduce((acc, point, i, arr) => {
      if (i === 0) {
        return `M ${point.x} ${point.y}`;
      }

      const prevPoint = arr[i - 1];
      const controlPoint1X = prevPoint.x + TIME_WIDTH / 3;
      const controlPoint2X = point.x - TIME_WIDTH / 3;

      return `${acc} C ${controlPoint1X} ${prevPoint.y}, ${controlPoint2X} ${point.y}, ${point.x} ${point.y}`;
    }, "");

    return path;
  };

  // Calculate the actual height needed for the SVG
  const svgHeight = height + TIME_LABEL_MARGIN + 20; // Added extra space for datetime labels

  return (
    <div style={styles.wrapper}>
      <div style={styles.fixedLabels}>
        <svg width={LABEL_WIDTH} height={svgHeight}>
          {Object.entries(STATUS_LEVELS).map(([status, y]) => (
            <text key={status} x="10" y={y} style={styles.statusText}>
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </text>
          ))}
        </svg>
      </div>

      <div
        ref={containerRef}
        style={styles.scrollContainer}
        onScroll={handleScroll}
      >
        <svg width={totalWidth} height={svgHeight}>
          {Object.entries(STATUS_LEVELS).map(([status, y]) => (
            <line
              key={status}
              x1="0"
              y1={y}
              x2={totalWidth}
              y2={y}
              style={styles.horizontalLine}
            />
          ))}

          {data.map((point, index) => (
            <text
              key={index}
              x={index * TIME_WIDTH + PADDING_LEFT}
              y={height + TIME_LABEL_MARGIN + 15} // Adjusted position with margin
              style={styles.timeText}
              textAnchor="middle"
            >
              {formatTime(point.time)}
            </text>
          ))}

          <path d={generatePath()} style={styles.dataLine} />
        </svg>
      </div>
    </div>
  );
};

export default RealtimeChart;
