import React from "react";
import fb_black_icon from "../../assets/icons/fb-icon-black.svg";

const PDFAccountDetailThread = ({ listThread }) => {
    return (
        <div className="pdf-account-detail-thread-creator-wrapper">
            {listThread.map((data, index) => (
                <div className="pdf-account-detail-threads" key={index}>
                    <div className="thread-creator-date">{data.threadDate}</div>
                    {data.threadDatas.map((threadData, index) => (
                        <div className="thread-creator-item" key={index}>
                            <div className="thread-creator-item-socmed">
                                <img src={fb_black_icon} alt="socmed-icon" />
                                <div className="vertical-line" />
                            </div>
                            <div className="thread-creator-item-category">
                                {threadData.category}
                            </div>
                            <div className="thread-creator-item-content">
                                <span>{threadData.content}</span>
                                <div className="thread-creator-item-source">
                                    <a
                                        href={threadData.urlLink}
                                        target="_blank"
                                        rel="noreferrer"
                                    >
                                        {threadData.urlLink}
                                    </a>
                                    <div
                                        className={`thread-creator-status ${threadData.categoryType.toLowerCase()}`}
                                    >
                                        {threadData.categoryType}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            ))}
        </div>
    );
};

export default PDFAccountDetailThread;
