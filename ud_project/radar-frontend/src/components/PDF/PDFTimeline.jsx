import React from 'react';

const PDFTimeline = () => {
  const timelineData = [
    { time: '17:03 - Oct 11, 2024', label: 'Content Scanned' },
    { time: '18:23 - Oct 11, 2024', label: 'Content Reported' },
    { time: '18:23 - Oct 11, 2024', label: 'External Reporting - Email to THE ROYAL MALAYSIA POLICE has been sent' },
    { time: '14:00 - Oct 14, 2024', label: 'Content Resolved' },
  ];

  return (
    <div>
        <div className="history-items">
            {timelineData?.length > 0 ? (
              timelineData?.map((item, index) => (
                <div key={index} className="history-item">
                     <div className="timeline">
                    <div className="timeline-dot"></div>
                    {index !== timelineData?.length - 1 && (
                      <div className="timeline-line"></div>
                    )}
                  </div>
                  <div className='d-flex align-items-center gap-3 history-wrapper'>
                    <div className="history-time">
                      <p>{item.time}</p>
                      {/* <p>{item.label}</p> */}
                    </div>
                    <div className='history-line'></div>
                    <div>
                      <p>{item.label}</p>
                    </div>
                  </div>
                 
                  {/* <div className="history-description">
                    <p>
                      <span className="ada-mr-1">From</span>
                      {item.oldValue || "N/A"}
                      <span className="ada-mx-1">to</span>
                      {item.newValue}
                    </p>
                  </div> */}
                </div>
              ))
            ) : (
              <p className="no-data">No History Available.</p>
            )}
          </div>
    </div>
  );
};

export default PDFTimeline;
