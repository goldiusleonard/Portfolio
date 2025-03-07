import React from 'react';
import moment from 'moment';
import formatNumber from '../../Util/NumberFormat';
import { Button } from 'reactstrap';


const CustomBox = (data) => {
    const colors = {
      low: {
        color: '#FFE700',
        borderColor: '#FFE700',
        backgroundColor: 'rgba(255, 231, 0, 0.20)',
      },
      medium: {
        color: '#FF8C00',
        borderColor: '#FF8C00',
        backgroundColor: 'rgba(255, 140, 0, 0.20)',
      },
      high: {
        color: '#F12D2D',
        borderColor: '#F12D2D',
        backgroundColor: 'rgba(241, 45, 45, 0.20)',
      },
    };
  
    return colors[data] || {};
  };

function PDFCommentTopCard() {
  return (

    <>
    <div className='content-details-cards'>
    <div className='platform-container'>
        <div style={{ cursor: 'pointer' }} >
          {/* {data?.social_media_type === 'TikTok' ? */}
            <svg xmlns="http://www.w3.org/2000/svg" width="34" height="39" viewBox="0 0 34 39" fill="none">
              <path d="M17.3525 0.848185C19.4261 0.816101 21.4878 0.835114 23.5471 0.816101C23.6719 3.24142 24.5441 5.7119 26.3194 7.42661C28.0912 9.18411 30.5973 9.98859 33.0357 10.2607V16.6407C30.7506 16.5658 28.4548 16.0905 26.3812 15.1066C25.4781 14.6978 24.6368 14.1714 23.8133 13.6331C23.8026 18.2627 23.8323 22.8864 23.7836 27.497C23.66 29.712 22.9292 31.9163 21.6411 33.7415C19.5687 36.78 15.9717 38.7609 12.2773 38.8227C10.0112 38.9522 7.74748 38.3343 5.81649 37.1959C2.6164 35.3089 0.364572 31.8545 0.0366008 28.147C-0.00471062 27.3618 -0.0110545 26.5752 0.017588 25.7894C0.30278 22.7747 1.7941 19.8907 4.1089 17.9288C6.73267 15.6437 10.4081 14.5552 13.8494 15.1993C13.8815 17.5462 13.7876 19.8907 13.7876 22.2376C12.2155 21.729 10.3784 21.8716 9.0047 22.8258C7.99969 23.4879 7.24019 24.462 6.84318 25.5981C6.51521 26.4014 6.60909 27.2938 6.6281 28.147C7.00479 30.747 9.50497 32.9323 12.1739 32.6958C13.9433 32.6768 15.639 31.6501 16.5611 30.1469C16.8594 29.6205 17.1933 29.0822 17.2111 28.4631C17.3668 25.629 17.305 22.8068 17.324 19.9727C17.3371 13.5856 17.305 7.21628 17.3537 0.849373L17.3525 0.848185Z" fill="#5B7DF5" />
            </svg>
            {/* :
            <svg width="22" height="40" viewBox="0 0 22 40" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M20.3075 22.5L21.4188 15.2612H14.4725V10.5637C14.4725 8.58372 15.4425 6.65247 18.5538 6.65247H21.7113V0.489971C21.7113 0.489971 18.8463 0.0012207 16.1063 0.0012207C10.3863 0.0012207 6.64751 3.46872 6.64751 9.74497V15.2625H0.288757V22.5012H6.64751V40.0012H14.4725V22.5012L20.3075 22.5Z" fill="#5B7DF5" />
            </svg>
          } */}
        </div>
        <div className='content-id-container'>
          {/* <div className='content-report-id'>
            <small className={`${isHovered ? 'fill-text' : ''}`} ref={content_id_copy}>{data?.identification_id}</small>
            <button
              className='btn-copy'
              onClick={copyToClipboard}
              onMouseEnter={() => setIsHovered(true)}
              onMouseLeave={() => setIsHovered(false)}
            >
              <img src={copyIcon} alt="Icon to copy" />
            </button>
          </div> */}

          <div className='content-date-time'>
            <div>
            HH:mm
                {/* {moment(data?.content_date).format('HH:mm')} */}
                </div>
            <div>
            DD MMM YYYY
                {/* {moment(data?.content_date).format('DD MMM YYYY')} */}
                </div>
          </div>
        </div>
      </div>
    </div>
     
     
      <div className='content-details-cards'>
        <div className='content-details-cards-title'>Status</div>
        <div className='content-details-cards-content'>
            new
            {/* {data?.report_status?.toLowerCase() === 'new' || data?.report_status?.toLowerCase() === 'ai flaged' ? 'AI Flagged' : data?.report_status} */}
            </div>
      </div>
      <div className='content-details-cards'>
        <div className='content-details-cards-title'>Likes</div>
        <div className='content-details-cards-content'>
            100
            {/* {formatNumber(data?.likes)} */}
            </div>
      </div>
      <div className='content-details-cards'>
        <div className='content-details-cards-title'>Replied</div>
        <div className='content-details-cards-content'>100</div>
      </div>
      
     
      <div className='content-details-cards'>
        <div className='content-details-cards-content '>
          <Button className='content-details-card-btn text-capitalize'
            // style={{ ...CustomBox(data?.risk_level) }}
            size='sm'
          >
            height
            {/* {data?.risk_level} */}
          </Button>
        </div>
      </div>
     
        
    </>
     

  )
}

export default PDFCommentTopCard