import React, { useEffect, useRef, useState } from "react";
import sample_profile_image from "../../assets/images/avatar.png";
import Button from "../button/Button";

const dummyDataNotification = [
  {
    id: 1,
    name: "Jane Copper",
    status: "end",
    dateTime: "1 Feb, 2024 . 6:45 am",
  },
  {
    id: 2,
    name: "Jane Copper",
    status: "live",
    dateTime: "1 Feb, 2024 . 6:45 am",
  },
  {
    id: 3,
    name: "Jane Copper",
    status: "end",
    dateTime: "1 Feb, 2024 . 6:45 am",
  },
];

const EmptyNotification = () => {
  return (
    <div className="notification-empty">There’s no notification available.</div>
  );
};

const NotificationItem = ({ data, handleGoToLive }) => {
  const { id, name, status, dateTime } = data;
  return (
    <div className="notification-item" key={id}>
      <div className="notification-item-image">
        <img src={sample_profile_image} alt="notification-profile" />
        {status === "live" && (
          <div className="notification-item-live">LIVE</div>
        )}
      </div>
      <div className="notification-item-content">
        <div className="notification-item-title">
          <b>{name}</b>{" "}
          {status === "live"
            ? "is doing Live Video right now."
            : "Live Video has ended."}
        </div>
        <div className="notification-item-time">{dateTime}</div>
        {status === "live" && (
          <div className="notification-item-action">
            <button
              className="notification-item-action-button"
              onClick={handleGoToLive}
            >
              Watch Live Video
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

const Notification = ({ handleOpenNotificationDetail }) => {
  const [dataNotification, setDataNotification] = useState(
    dummyDataNotification
  );
  const [isShowNotification, setIsShowNotification] = useState(false);
  const notificationRef = useRef(null);

  const handleClickNotification = () => {
    setIsShowNotification(!isShowNotification);
  };

  const handleGoToLive = () => {
    handleClickNotification();
    handleOpenNotificationDetail();
  };

  const closeNotification = (event) => {
    if (
      notificationRef.current &&
      !notificationRef.current.contains(event.target)
    ) {
      setIsShowNotification(false);
    }
  };

  const handleClearNotification = () => {
    setDataNotification([]);
  };

  useEffect(() => {
    document.addEventListener("mousedown", closeNotification);

    return () => {
      document.removeEventListener("mousedown", closeNotification);
    };
  }, []);

  return (
    <div className="header-notification-wrapper" ref={notificationRef}>
      <div
        className="top-header-filter-notification-icon"
        onClick={handleClickNotification}
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="19"
          viewBox="0 0 16 19"
          fill="none"
        >
          <path
            d="M8 19C9.1 19 10 18.1231 10 17.0513H6C6 18.1231 6.9 19 8 19ZM14 13.1538V8.28205C14 5.29077 12.37 2.78667 9.5 2.1241V1.46154C9.5 0.652821 8.83 0 8 0C7.17 0 6.5 0.652821 6.5 1.46154V2.1241C3.64 2.78667 2 5.28103 2 8.28205V13.1538L0 15.1026V16.0769H16V15.1026L14 13.1538ZM12 14.1282H4V8.28205C4 5.86564 5.51 3.89744 8 3.89744C10.49 3.89744 12 5.86564 12 8.28205V14.1282Z"
            fill="white"
          />
        </svg>
        {dataNotification?.length > 0 && <div className="dot-notification" />}
      </div>
      {isShowNotification && (
        <div className="top-header-notification-wrapper">
          <div className="notification-header">
            <h1 className="notification-title">Notification</h1>
            <Button
              onClick={handleClearNotification}
              disabled={dataNotification?.length === 0}
              className="notification-button-clear text-white bg-transparent justify-content-center align-items-center border"
              text={"Clear Notification"}
            />
          </div>
          <div className="notification-body">
            {dataNotification?.length === 0 && <EmptyNotification />}
            {dataNotification?.map((data) => (
              <NotificationItem
                key={data.id}
                data={data}
                handleGoToLive={handleGoToLive}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Notification;
