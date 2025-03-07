import React, { useState, useMemo, useCallback } from 'react';
import ContentDetailsTopCard from '../../components/TopCards/ContentDetailsTopCard';
import WatchListProfile from '../../components/WatchListProfile';
import OriginalContent, { Category } from '../../components/OriginalContent';
import { useLocation } from 'react-router-dom';
import useBreadcrumb from '../../hooks/useBreadcrumb';
import Alert from '../../components/Alert';
import useApiData from '../../hooks/useApiData';
import endpoints from '../../config/config.dev';

const ParameterList = [
    'Inviting users to click a URL link',
    'High promising words',
    'Requests for personal information',
    'Unsolicited investment offers',
    'Guaranteed high returns',
    'Anonymous or untraceable transactions',
    'Phishing emails or messages',
    'Unrealistic investment schemes'
]

const AgentContentDetails = () => {
    const location = useLocation();
    const content = location.state;
    
    const [isOpenDropContent, setIsOpenDropContent] = useState(false);
    const [isOpenReportContent, setIsOpenReportContent] = useState(false);
    const [showMessage, setShowMessage] = useState(false);
    const [alertMessage, setAlertMessage] = useState("Content has been successfully reported");
  
    const { data, loadingData } = useApiData(`${endpoints.getContentDetail}?video_id=${content?.video_id}`, showMessage);
    const toggleDropContent = useCallback(() => {
      setIsOpenDropContent(prevState => !prevState);
    }, []);
  
    const toggleReportContent = useCallback(() => {
      setIsOpenReportContent(prevState => !prevState);
    }, []);
  
    const onCloseModal = () => {
      setTimeout(() => {
        window.location.reload();
      }, 2000); 
    };
  
    const handleReportContents = useCallback((data) => {
      setIsOpenReportContent(false);
      setShowMessage(true);
      setAlertMessage('Content has been successfully reported')
    }, []);
  
    const handleShowMessage = (message) => {
      setAlertMessage(message)
      setShowMessage(true);
    }
  
    useBreadcrumb({ title: '', hasBackButton: true, hasDateFilter: false });
  
    const alertComponent = useMemo(() => (
      <Alert
        message={alertMessage}
        info="success"
        duration={3000}
        visible={showMessage}
      />
    ), [showMessage]);
  
    return (
      <div className="content-details-wrapper agent-content-details-wrapper" >
        {alertComponent}
        <section className="top-filter card-wrap">
          <ContentDetailsTopCard data={data} loading={loadingData} />
        </section>
        <section className="original-content-wrapper">
          <div className="d-flex flex-column w-60 h-100">
            <Category subCategoryRoute={data?.sub_category} subCategoryTopic={data?.ai_topic} />
            <div className="original-content card-wrap">
              <OriginalContent data={data} loading={loadingData} showComments={false}/>
            </div>
          </div>
  
          <div className="do-wrapper h-100">
            <div className="profile-details card-wrap">
              <WatchListProfile data={data?.content_creator} loading={loadingData} />
            </div>
            <div className="data-observatory card-wrap">
              <h2 className="title-type-2 p-3">The parameters related to this content</h2>
              
              <div className='parameters-wrapper'>
                <ul className='p-list'>
                    {
                        ParameterList && ParameterList.map((parameterItem, index) => (
                            <li className='p-list__item'>{parameterItem}</li>
                        ))
                    }
                </ul>
              </div>
            </div>
          </div>
        </section>
      </div>
    );
  };

export default AgentContentDetails
