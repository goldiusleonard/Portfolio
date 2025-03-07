import React, { useState, useMemo, useCallback } from 'react';
import ContentDetailsTopCard from '../../components/TopCards/ContentDetailsTopCard';
import WatchListProfile from '../../components/WatchListProfile';
import OriginalContent, { Category, CategoryDisplay } from '../../components/OriginalContent';
import CategoryDO from '../../components/CategoryDO';
import Button from '../../components/button/Button';
import DropContentModal from '../../components/Modal/DropContentModal';
import ReportContentModal from '../../components/Modal/ReportContentModal';
import { useLocation } from 'react-router-dom';
import useBreadcrumb from '../../hooks/useBreadcrumb';
import Alert from '../../components/Alert';
import useApiData from '../../hooks/useApiData';
import endpoints from '../../config/config.dev';
import ListContainer from '../../components/lists/ListContainer';
import HashTagRow from '../../components/ui/hashtag/HashTagRow';
import HashtagReportModal from '../../components/Modal/HashtagReportModal';


const justText = 'According to the video, there are strong indications that the content might be high likely a scam. This is suggested by the involvement of a person associated with OctaFX, a company already listed by Bank Negara Malaysia and Securities Commission Malaysia as an unauthorised entity. Additionally, the video promises high returns on investment for joining their group, a claim that appears suspiciously unrealistic. '


const Keywords = [
  'Ethereum',
  'Tether',
  'Binance Coin',
  'USD Coin',
  'XRP',
  'Cardano',
  'Dogecoin',
  'Solana',
  'Polkadot',
  'Binance Smart Chain',
  'Ripple'

]
const hashTags = [
  {
    id: 1,
    name: 'Ethereum',
    risk_level: 'Low'
  },
  {
    id: 2,
    name: 'Tether',
    risk_level: 'high'
  },
  {
    id: 3,
    name: 'Binance Coin',
    risk_level: 'medium'
  },
  {
    id: 4,
    name: 'USD Coin',
    risk_level: 'Low'
  },
  {
    id: 5,
    name: 'XRP',
    risk_level: 'Low'
  },
  {
    id: 6,
    name: 'Cardano',
    risk_level: 'Low'
  },
  {
    id: 7,
    name: 'Dogecoin',
    risk_level: 'Low'
  },
  {
    id: 8,
    name: 'Solana',
    risk_level: 'Low'
  },
  {
    id: 9,
    name: 'Polkadot',
    risk_level: 'Low'
  },
]

const ContentDetails = () => {
  const location = useLocation();
  const content = location.state;

  const [isOpenDropContent, setIsOpenDropContent] = useState(false);
  const [isOpenReportContent, setIsOpenReportContent] = useState(false);
  const [isOpenHashtagReport, setIsOpenHashtagReport] = useState(false);
  const [showMessage, setShowMessage] = useState(false);
  const [alertMessage, setAlertMessage] = useState("Content has been successfully reported");
  const [chosenContent, setChosenContent] = useState(null);

  const { data, loadingData } = useApiData(`${endpoints.getContentDetail}?video_id=${content?.video_id}`, showMessage);
  const toggleDropContent = useCallback(() => {
    setIsOpenDropContent(prevState => !prevState);
  }, []);

  const toggleReportContent = useCallback(() => {
    setIsOpenReportContent(prevState => !prevState);
  }, []);


  const toggleHashtagReport = useCallback((data) => {
    setChosenContent(data);
    setIsOpenHashtagReport(prevState => !prevState);
  }, []);


  const onCloseModal = () => {
    setTimeout(() => {
      window.location.reload();
    }, 2000);
  };

  const handleReportContents = useCallback((data) => {
    // get selected content list and send to backend
    setIsOpenReportContent(false);
    setShowMessage(true);
    setAlertMessage('Content has been successfully reported')
  }, []);

  const handleShowMessage = (message) => {
    setAlertMessage(message)
    setShowMessage(true);
  }

  useBreadcrumb({
    title: "",
    hasBackButton: true,
    hasDateFilter: true,
    hasCategoryFilter: true,
  });

  const alertComponent = useMemo(() => (
    <Alert
      message={alertMessage}
      info="success"
      duration={3000}
      visible={showMessage}
    />
  ), [alertMessage, showMessage]);

  return (
    <div className="content-details-wrapper" >
      {alertComponent}
      <section className="top-filter card-wrap">
        <ContentDetailsTopCard data={data} loading={loadingData} />
      </section>
      <section className="original-content-wrapper">
        <div className="d-flex flex-column w-60 h-100">
          <div className='justification-conatiner card-wrap' >
            {/* <Category subCategoryRoute={data?.sub_category} subCategoryTopic={data?.ai_topic} /> */}
            <div>
              <p>Justification</p>
              <div className='description-wrapper'>
                {justText}
              </div>
            </div>

          </div>
          <div className="original-content card-wrap">
            <OriginalContent data={data} loading={loadingData} showComments={true} />
          </div>
        </div>

        <div className="do-wrapper h-100">
          <div className="profile-details card-wrap">
            <WatchListProfile data={data?.content_creator} loading={loadingData} />
          </div>
          <div className="data-observatory ">
            {/* <h2 className="title-type-2 p-3">Similar Keywords</h2>
            <CategoryDO /> */}
            <ListContainer header="Similar Keywords">
              {Keywords.map((item, index) => (
                <div className='keyword-containers'>
                  <p className='keyword-label' key={index}>{item}</p>
                </div>

              ))}
            </ListContainer>
            <ListContainer header="Hashtags" >
              {hashTags.map((item, index) => <HashTagRow level={item.risk_level} onClick={toggleHashtagReport} key={index} item={item} />)
              }
            </ListContainer>
          </div>
          <div className="btn-wrapper">
            <Button
              text="Mark as Resolved"
              variant="outline"
              onClick={toggleDropContent}
            // disable={data?.report_status !== 'AI Flagged'}
            />
            <Button
              text="Report Content"
              variant="contain"
              onClick={toggleReportContent}
              disable={data?.report_status !== 'AI Flagged'}
            />

            <DropContentModal
              isOpen={isOpenDropContent}
              toggle={toggleDropContent}
              handleShowMessage={handleShowMessage}
            />
            {data &&
              <ReportContentModal
                isOpen={isOpenReportContent}
                chosenContent={data}
                handleReportContents={handleReportContents}
                toggle={toggleReportContent}
                onCloseModal={onCloseModal}
              />

            }
            {data &&
              <HashtagReportModal
                isOpen={isOpenHashtagReport}
                chosenContent={chosenContent}
                handleReportContents={handleReportContents}
                toggle={toggleHashtagReport}
                onCloseModal={onCloseModal}

              />

            }
          </div>
        </div>
      </section>
    </div>
  );
};

export default ContentDetails;
