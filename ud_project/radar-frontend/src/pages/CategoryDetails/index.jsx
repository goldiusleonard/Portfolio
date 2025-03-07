import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { scammersRankingHeaders } from '../../data/scammerRank';
import Table from '../../components/tables/BootstrapTable';
import avatarIcon from '../../assets/icons/user.svg';
import arrowUp from '../../assets/icons/comment_arrow_up.svg';
// import Table from '../../components/tables/BootstrapTable';
// import Bar from '../../components/RiskIndicator/Bar';
// import SubCategoryCard from '../../components/SubCategoryCard';
// import PieChart from '../../components/charts/PieChart';
// import Searchbar from '../../components/ui/inputs/Searchbar';
// import Button from '../../components/ui/buttons/Button';
import { Treemap, TableWithSearchbar } from '../../components';
import useBreadcrumb from '../../hooks/useBreadcrumb';
import { useLocation, useNavigate } from 'react-router-dom';
import useApiData from '../../hooks/useApiData';
import endpoints from '../../config/config.dev';
// import LoaderAnimation from '../../components/LoaderAnimation';
// import { FilterMatchMode, FilterOperator } from 'primereact/api';

// import Select from '../../components/Select/Select';
import HashTag from '../../components/HashTag';
import CategoryFunnel from '../../components/CategoryFunnel';
import TaskTracker from './TaskTracker';
import ContentList from './ContentList';
import { getUserFromLocalStorage } from '../../Util';
import Alert from '../../components/Alert';
import comments from './CategoryDetails.json'
import ReportCommentModal from '../../components/Modal/ReportCommentModal';
import CommentUi from './CommentUi';


const CategoryDetails = () => {
  const navigate = useNavigate();
  const user=getUserFromLocalStorage()
  const [filterStatus, setFilterStatus] = useState(()=>{
    const savedName = sessionStorage.getItem('categoryDetails');
    return savedName ? JSON.parse(savedName) :{
      subCategory: null,
      topic: null
    };
    
  });
  const [hashtag, setHashtag] = useState(()=>{
    const savedHashtag = sessionStorage.getItem('hashTag');
    return savedHashtag  ? JSON.parse(savedHashtag ):null
  })
  const [commentIds, setCommentIds] =useState(null)
  const contentListUrl = `${endpoints.getContentList}?category=hate%20speech${filterStatus?.subCategory ? `&subCategory=${filterStatus?.subCategory}` : ''}${filterStatus?.topic ? `&topic=${filterStatus?.topic}` : ''}${hashtag ? `&hashtag=${hashtag}` : ''}`;
  const [activeTab, setActiveTab] = useState("Creators");
  const { data: rankData, loadingData: rankLoading } = useApiData(
    `${endpoints.getRankingWithFilter}?category=hate%20speech${
      filterStatus?.subCategory
        ? `&subCategory=${filterStatus?.subCategory}`
        : ""
    }${filterStatus?.topic ? `&topic=${filterStatus?.topic}` : ""}`
  );
  const { data: hashTagData, loadingData: hashLoading } = useApiData(
    `${endpoints.getHashTags}?category=hate%20speech${
      filterStatus?.subCategory
        ? `&subCategory=${filterStatus?.subCategory}`
        : ""
    }${filterStatus?.topic ? `&topic=${filterStatus?.topic}` : ""}`
  );
  const [showMessage, setShowMessage] = useState(false);
  const [alertMessage, setAlertMessage] = useState(
    "Content has been successfully reported"
  );
  const [isOpenReportComment, setIsOpenReportComment] = useState(false);

  let userName = user?.user_name;

  userName = userName
    ?.replace(".userdata", "")
    .replace(/^\w/, (c) => c.toUpperCase());

  const title = `Hello, ${userName}`;
  const hasBackButton = false;
  const hasDateFilter = true;
  const hasCategoryFilter = true;

  useBreadcrumb({ title, hasBackButton, hasDateFilter, hasCategoryFilter });

  const ref = useRef(null);
  const treeRef = useRef(null);
  const scrollHeight = ref.current?.offsetHeight - 84;

  const handleStatusCardClick = (e, backButton = false, filterClick = null) => {
    if (backButton) {
      if (filterStatus?.topic) {
        setFilterStatus({ subCategory: e, topic: "" });
      } else {
        // setSubCat(filterData?.subCategory);
        setFilterStatus({ subCategory: "", topic: "" });
      }
    } else if (filterClick !== null) {
      if (filterClick === "sub") {
        setFilterStatus({ subCategory: e, topic: "" });
      } else {
        // setSubCat(filterData?.subCategory);
        setFilterStatus({ subCategory: "", topic: e });
      }
    } else {
      setHashtag(null);
      if (filterStatus?.subCategory) {
        setFilterStatus((prev) => ({ ...prev, topic: e }));
      } else {
        setFilterStatus((prev) => ({ ...prev, subCategory: e }));
      }
    }
  };
  const saveStatehandler = () => {
    sessionStorage.setItem(
      "categoryDetails",
      JSON.stringify({
        subCategory: filterStatus.subCategory,
        topic: filterStatus.topic,
      })
    );
    sessionStorage.setItem("hashTag", JSON.stringify(hashtag));
  };
  const clearSessionStorage = () => {
    sessionStorage.removeItem("categoryDetails");
    sessionStorage.removeItem("hashTag");
  };

  const onClickRankListRow = (row) => {
    saveStatehandler();
    navigate("/watch-list/creator", { state: row.data });
  };

  const tableProps = {
    tableProps: {
      headers: scammersRankingHeaders,
      scrollHeight: scrollHeight,
      emptyMessage: "No creators found",
    },
    searchProps: {
      placeholder: "Search Creator",
    },
    sortable: true,
    data: rankData,
    loadingData: rankLoading,
    onRowClick: onClickRankListRow,
  };

  const handleReportContents = useCallback((message) => {
    setShowMessage(true);
    setAlertMessage(message);
  }, []);

  const handleHashTagChange = (value) => {
    if ("#" + hashtag === value) {
      setHashtag(null);
    } else {
      setHashtag(value.substring(1));
    }
  };

  useEffect(() => {
    if (showMessage) {
      setTimeout(() => {
        setShowMessage(false);
      }, 3000);
    }
  }, [showMessage]);

  const alertComponent = useMemo(
    () => (
      <Alert
        message={alertMessage}
        info={alertMessage.includes("Failed") ? "fail" : "success"}
        duration={3000}
        visible={showMessage}
      />
    ),
    [alertMessage, showMessage]
  );

  const handleReportComment = useCallback((data) => {
    setCommentIds(data);
    setIsOpenReportComment((prevState) => !prevState);
  }, []);

  const toggleReportComment = useCallback(() => {
    setIsOpenReportComment((prevState) => !prevState);
  }, []);

  return (
    <div className="category-details-wrapper">
      {/* <AiAgentPublished /> */}
      {alertComponent}
      <section className="charts-section">
        <div className="charts-wrapper">
          <div className="pie-chart-wrapper card-wrap">
            <CategoryFunnel />
          </div>
          <div className="risk-indicator-wrapper">
            <TaskTracker />
          </div>
        </div>
        <div className="categories-card card-wrap">
          <div ref={treeRef} className="treemap-wrapper">
            <Treemap
              treeRef={treeRef}
              setTopic={handleStatusCardClick}
              setSubCategory={setFilterStatus}
              handleStatusCardClick={handleStatusCardClick}
              activeTopic={filterStatus?.topic}
              subCategory={filterStatus}
            />
          </div>
          <div className="hashtag-wrapper">
            <HashTag
              hashTags={hashTagData}
              handleHashTagChange={handleHashTagChange}
              hashtag={hashtag}
            />
          </div>
        </div>
      </section>
      <section className="table-section">
        <div className="rank-list-wrapper card-wrap" ref={ref}>
          <div></div>
          {/* <div className="tabs">
            <button
              className={activeTab === 'Comments' ? 'active' : ''}
              onClick={() => setActiveTab('Comments')}
            >
              Comments
            </button>
            <button
              className={activeTab === 'Creators' ? 'active' : ''}
              onClick={() => setActiveTab('Creators')}
            >
              Creators
            </button>
          </div> */}
          {activeTab === "Creators" && <TableWithSearchbar {...tableProps} />}
          {activeTab === "Comments" && (
            <CommentUi
              handleReportComment={handleReportComment}
              filterStatus={filterStatus}
            />
          )}
        </div>
        <div className="content-list-wrapper card-wrap">
          <ContentList
            contentListUrl={contentListUrl}
            scrollHeight={scrollHeight}
            Table={Table}
            handleReportContents={handleReportContents}
            saveStatehandler={saveStatehandler}
          />
        </div>

        <ReportCommentModal
          isOpen={isOpenReportComment}
          // chosenContent={data}
          // handleReportContents={handleReportContents}
          toggle={toggleReportComment}
          {...commentIds}
        />
      </section>
    </div>
  );
};

export default CategoryDetails;


