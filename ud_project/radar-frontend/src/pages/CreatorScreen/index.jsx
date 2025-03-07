import React, { useState, useEffect } from 'react';
import { Button, Modal, ModalHeader, ModalBody, ModalFooter } from 'reactstrap';
import axios from 'axios';
import ScrollableList from '../../components/lists/ScrollableList';
import HeatMap from '../../components/HeatMap';
import HeatMapTopCard from "../../components/TopCards/HeatMapTopCard";
import CreatorDO from '../../components/CreatorDO';
import { useLocation, useNavigate } from 'react-router-dom';
import creatorData from './CreatorScreen.json';
import useBreadcrumb from '../../hooks/useBreadcrumb';
import useApiData from '../../hooks/useApiData';
import endpoints from '../../config/config.dev';
import Select from '../../components/Select/Select';
import { SingleLinechart } from '../../components';
import { avatar } from '../../assets/images';
import { CloseIcon } from '../../assets/icons';
import Alert from '../../components/Alert';
import formatNumber from '../../Util/NumberFormat';
import CategoryPostStatus from "./CategoryPostStatus";

const CreatorScreen = () => {
  const location = useLocation();
  const navigate = useNavigate()
  const [sendLoading, setSendLoading] = useState()
  const years = ['2024', '2023', '2022', '2021', '2020']
  const { profile_id: id, user_handle: name, engagementDate } = location.state ? location.state : [];
  const apiEndpoint = `${endpoints.getCreatorProfile}?userName=${name}`
  const { data: creatorProfileData } = useApiData(apiEndpoint)
  const getCreatorPostsApi = `${endpoints.getCreatorPosts}?userName=${name}`
  const { data: posts, loadingData: postsLoading } = useApiData(getCreatorPostsApi);
  const [year, setYear] = useState('2024')
  const [date, setDate] = useState(null)
  const [modal, setModal] = useState(false);
  const [highlightedContent, setHighlightedContent] = useState([]);
  const [isHeatmap, setIsHeatmap] = useState(true)
  const toggle = () => setModal(!modal);
  const [showMessage, setShowMessage] = useState(false);
  const title = '';
  const hasBackButton = true;
  const hasDateFilter = true;
  const hasCategoryFilter = true;
  const lineChartRef = React.useRef();


  useBreadcrumb({ title, hasBackButton, hasDateFilter, hasCategoryFilter });

  const goToWatchList = () => {
    navigate('/watch-list')
  }

  const options1 = [
    "Choose a subject for your email template",
    "Report of Violent Threats",
    "Report of Copyright Theft",
    "Request of Investigation",
  ];
  const options2 = [
    "Choose list organization who will receive this email",
    "Communication & Industry Relation (example@email.com)",
    "Regulatory Policy (example@email.com)",
    "Consumer & Industry Affair(example@email.com)",
  ];
  const handleYearSelect = (e) => {
    setYear(e)
  }

  const handleDateSelect = React.useCallback((e) => {
    setDate(e);
  }, []);

  const handleHighlightedContent = (content) => {
    setHighlightedContent(content);
  };

  const handleCreatorReport = (creatorProfile) => {
    toggle()
    sendReport(creatorProfile)
    // console.log("Consumer", creatorProfile)
  }

  const sendReport = async (creatorProfile) => {

    setSendLoading(true)
    try {
      const response = axios({
        method: 'post',
        url: endpoints.postProfileReport,
        data: creatorProfile
      }).then((response) => {
        console.log(JSON.stringify('repor', response.data));

        setShowMessage(true)
      });
    } catch (error) {
      console.error(error);
    } finally {
      setSendLoading(false);
    }
  }
  const widthLineChart = lineChartRef.current?.offsetWidth;


  const handleToggle = (e) => {
    setIsHeatmap(e.currentTarget.name === 'heatmap')
  }

  const closeBtn = (
    <div className="close" onClick={toggle}>
      <CloseIcon fill="#fff" />
    </div>
  );

  const alertComponent = React.useMemo(() => (
    <Alert
      message="This feature will be available soon."
      info="success"
      duration={3000}
      visible={showMessage}
    />
  ), [showMessage]);
  return (
    <div className='creator-screen-wrapper'>
      {alertComponent}
      <section className='top-filter card-wrap'>
        {creatorProfileData && <HeatMapTopCard data={creatorProfileData} toggle={toggle} />}
      </section>
      <section className="category-heatmap-section">
        <div className="card-wrap category-post-status-wrapper">
          <CategoryPostStatus
            data={[
              { title: 'Scam', value: 10000 },
              { title: 'Hate Speech', value: 7200 },
              { title: '3R', value: 5900 },
              { title: 'Category #1', value: 712 },
              { title: 'Category #2', value: 712 },
              { title: 'Category #3', value: 712 },
              { title: 'Category #4', value: 712 }
            ]}
            maxProgress={10000}
            minHigh={8000}
            minMedium={5000}
            progressLabelFormatter={(v) => {
              console.log(v)
              if (v >= 1000) return `${v / 1000}k`
              return v
            }}
          />
        </div>
        <div className='heatmap-wrapper card-wrap' ref={lineChartRef}>
          {isHeatmap ?
            <HeatMap
              data={creatorData.profiles[0].threats} setHighlightedContent={handleHighlightedContent}
              engagementDate={engagementDate} profileName={name} year={year} setDate={handleDateSelect} handleToggle={handleToggle}
            />
            : <SingleLinechart width={widthLineChart} setDate={handleDateSelect} handleToggle={handleToggle} creatorName={name}
              handleHighlightedContent={handleHighlightedContent} />}
        </div>
      </section>
      <section className='content-list-wrapper'>
        <div className="content-list">
          <ScrollableList name={creatorProfileData && creatorProfileData[0]?.user_handle} setDate={setDate} date={date} currentYear={handleYearSelect} creatorScamsData={posts ?? {}} years={years} loading={postsLoading} highlightedContent={highlightedContent} />
        </div>
        <div className="data-observatory card-wrap">
          <div className='go-to-link'>
            <h2 className='title-type-1 p-3'>Similar Creators</h2>
            {/* <a className='view-all' onClick={goToWatchList}>View All</a> */}
          </div>
          {creatorProfileData && <CreatorDO creatorName={creatorProfileData[0]?.user_handle} />}
        </div>
      </section>

      {creatorProfileData && (
        <Modal isOpen={modal} toggle={toggle} centered={true} size='xl'>
          <ModalHeader toggle={toggle} style={{ color: '#A9A9A9' }} close={closeBtn}>Report Creator</ModalHeader>
          <ModalBody>
            <div>
              <div className="mb-3" style={{ color: '#7B7B7B' }}>Creator Detail</div>
              <div className="creator-detail flex-column h-100 align-items-start">
                <div className='creator-detail-profile' style={{ cursor: 'pointer', zIndex: '99999' }} onClick={(event) => {
                  event.preventDefault();
                  event.stopPropagation();
                  window.open(`https://www.tiktok.com/@${name}`, '_blank', 'noopener,noreferrer');
                }}>
                  <img src={!creatorProfileData[0]?.creator_photo_link || creatorProfileData[0]?.creator_photo_link.includes("https://p16-sign") ? avatar : creatorProfileData[0]?.creator_photo_link} alt='profile' />
                  <div className='creator-id-container'>
                    <p className='creator-id'>{name || 'Unknown'}</p>
                  </div>
                </div>
                <div className="d-flex justify-content-between w-100">
                  <div className='creator-details-cards'>
                    <div className='creator-details-cards-title'>Following</div>
                    <div className='creator-details-cards-content'>{creatorProfileData[0] !== null ? formatNumber(creatorProfileData[0]?.user_following_count) : 'N/A'}</div>
                  </div>
                  <div className='creator-details-cards'>
                    <div className='creator-details-cards-title'>Followers</div>
                    <div className='creator-details-cards-content'>{creatorProfileData[0] !== null ? formatNumber(creatorProfileData[0]?.user_followers_count) : 'N/A'}</div>
                  </div>
                  <div className='creator-details-cards'>
                    <div className='creator-details-cards-title'>Posts</div>
                    <div className='creator-details-cards-content'>{creatorProfileData[0] !== null ? creatorProfileData[0]?.user_total_videos : 'N/A'}</div>
                  </div>
                  <div className='creator-details-cards'>
                    <div className='creator-details-cards-title'>Engagement</div>
                    <div className='creator-details-cards-content'>{creatorProfileData[0] !== null ? creatorProfileData[0]?.ProfileEngagement_score?.toFixed(1) : 'N/A'}%</div>
                  </div>
                </div>
              </div>
              <div>
                <div className="my-4" style={{ color: '#A9A9A9' }}>Send content report to External Organization (Optional)</div>
                <div className="creator-detail-input-wrapper">
                  <div className="input-title">Report Subject</div>
                  <Select
                    options={options1}
                    defaultValue={options1[0]}
                    className="ReportDropdown"
                    arrowSize={"15"}
                  />
                </div>
                <div className="creator-detail-input-wrapper">
                  <div className="input-title">Select Organization</div>
                  <Select
                    options={options2}
                    defaultValue={options2[0]}
                    className="OrganizationDropdown"
                    arrowSize={"15"}
                  />
                </div>
                <div className="creator-detail-input-wrapper">
                  <div className="input-title">Send to custom email</div>
                  <input type="email" placeholder="Type list of email who will receive this email" />
                </div>
              </div>
            </div>
          </ModalBody>
          <ModalFooter>
            <Button className="btn btn-outline-light no-bg" variant="outline" onClick={toggle}>
              Cancel
            </Button>
            <Button className="btn btn-light" onClick={() => handleCreatorReport(creatorProfileData[0] !== null ? creatorProfileData[0] : {})}>
              Report Creator
            </Button>
          </ModalFooter>
        </Modal>
      )}
    </div>
  );
};

export default CreatorScreen;
