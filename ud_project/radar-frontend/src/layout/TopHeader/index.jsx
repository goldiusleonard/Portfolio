import React, { useState } from "react";
import { Button } from "reactstrap";
import { useNav } from "../../contexts/NavContext";
import { useNavigate } from "react-router-dom";
import Select from "../../components/Select/Select";
import { useGlobalData } from "../../App";
import { useAuth } from "../../contexts/AuthContext";
import Notification from "../../components/Notification";
import NotificationDetail from "../../components/Notification/NotificationDetail";

const TopHeader = () => {
  const navigate = useNavigate();
  const { userRole } = useAuth();
  const isOfficer = userRole === "officer";
  const { navData } = useNav();

  const [isShowNotificationLive, setIsShowNotificationLive] = useState(false);

  const handleGoBack = () => {
    navigate(-1);
  };

  const handleModalNotificationLive = () => {
    setIsShowNotificationLive(!isShowNotificationLive);
  };

  const dateOptions = [
    "Today",
    "Last 7 Days",
    "Last 15 Days",
    "Last 30 Days",
    "Last 3 Months",
  ];

  const options1 = isOfficer ? dateOptions : dateOptions.slice(1);

  const options2 = ["Scam", "3R", "ATIPSOM", "Family and Sexual"];

  return (
    <div className="top-header">
      <div className="top-header-wrapper">
        <div className="top-header-title-section">
          {navData.hasBackButton && (
            <Button onClick={handleGoBack}>
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="20"
                height="20"
                viewBox="0 0 20 20"
                fill="white"
              >
                <g filter="url(#filter0_b_1612_17452)">
                  <path
                    opacity="1"
                    fillRule="evenodd"
                    clipRule="evenodd"
                    d="M8.0532 10.0009L12.551 5.46527C12.8839 5.12914 12.8839 4.58702 12.551 4.25089C12.3924 4.09032 12.176 4 11.9503 4C11.7247 4 11.5083 4.09032 11.3497 4.25089L6.2512 9.39281C5.91724 9.72857 5.91724 10.2714 6.2512 10.6072L11.3495 15.7491C11.5083 15.9097 11.7247 16 11.9503 16C12.176 16 12.3924 15.9097 12.5512 15.7491C12.8839 15.4129 12.8839 14.8708 12.5508 14.5347L8.0532 10.0009Z"
                    fill="white"
                    fillOpacity="0.6"
                  />
                </g>
                <defs>
                  <filter
                    id="filter0_b_1612_17452"
                    x="-182"
                    y="-182"
                    width="384"
                    height="384"
                    filterUnits="userSpaceOnUse"
                    colorInterpolationFilters="sRGB"
                  >
                    <feFlood floodOpacity="0" result="BackgroundImageFix" />
                    <feGaussianBlur in="BackgroundImageFix" stdDeviation="90" />
                    <feComposite
                      in2="SourceAlpha"
                      operator="in"
                      result="effect1_backgroundBlur_1612_17452"
                    />
                    <feBlend
                      mode="normal"
                      in="SourceGraphic"
                      in2="effect1_backgroundBlur_1612_17452"
                      result="shape"
                    />
                  </filter>
                </defs>
              </svg>
              Back
            </Button>
          )}

          {navData.navItems.length > 0 && !navData.title && (
            <nav aria-label="breadcrumb">
              <ol className="breadcrumb">
                {navData.navItems.map((item, index) => {
                  // Check if item.name contains "Watch" and remove spaces between characters if true
                  const displayName = item.name.includes("Watch")
                    ? item.name.replace(/\s+/g, "")
                    : item.name;

                  return (
                    <li
                      key={item.url + index}
                      className={`breadcrumb-item ${
                        item.active ? "active" : ""
                      }`}
                      aria-current={item.active ? "page" : undefined}
                    >
                      {item.active ? (
                        <span>{displayName}</span>
                      ) : (
                        <a href={item.url}>{displayName}</a>
                      )}
                    </li>
                  );
                })}
              </ol>
            </nav>
          )}

          {navData.title ? (
            navData.title === "Dashboard" ? (
              <div>
                <div className="dashboard-title-wrapper">
                  <div className="dashboard-title">Dashboard</div>
                </div>
                <div className="dashboard-sub-title">
                  AI-flagged scam content overview: total scans, sub-categories,
                  resolved cases, platform distribution, keywords, and
                  engagement.
                </div>
              </div>
            ) : (
              <div className="top-header-title">{navData.title}</div>
            )
          ) : null}
        </div>

        <div className="d-flex top-header-filter">
          {navData.hasCategoryFilter && (
            <Select
              options={options2}
              defaultValue={options2[0]}
              className="scamDropdown"
              arrowSize={"15"}
            />
          )}

          {navData.hasDateFilter && (
            <Select
              options={options1}
              defaultValue={options1[0]}
              className="DaysDropdown"
              arrowSize={"15"}
            />
          )}

          <Notification
            handleOpenNotificationDetail={handleModalNotificationLive}
          />

          <NotificationDetail
            isShowModal={isShowNotificationLive}
            handleModal={handleModalNotificationLive}
          />
        </div>
      </div>
    </div>
  );
};

export default TopHeader;
