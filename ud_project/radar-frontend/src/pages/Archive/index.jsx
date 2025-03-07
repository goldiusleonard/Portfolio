import React, { useRef, useState, useMemo, useCallback } from 'react';
import { FilterMatchMode } from 'primereact/api';
import useBreadcrumb from '../../hooks/useBreadcrumb';
import useApiData from '../../hooks/useApiData';
import endpoints from '../../config/config.dev';
import Table from '../../components/tables/Table';
import { archiveListHeaders } from '../../data/scammerRank';
import Searchbar from '../../components/ui/inputs/Searchbar';
import Select from '../../components/Select/Select';
import comments from '../CategoryDetails/CategoryDetails.json';
import { useNavigate } from 'react-router-dom';

const Archive = () => {
  const title = 'Archive';
  const hasBackButton = false;
  const hasDateFilter = true;
  const hasCategoryFilter=true;
  useBreadcrumb({ title, hasBackButton, hasDateFilter,hasCategoryFilter });

  const [filters, setFilters] = useState({ global: { value: null, matchMode: FilterMatchMode.CONTAINS } });
  const [activeTab, setActiveTab] = useState('Contents');
  const containerRef = useRef();
  const { data, loadingData } = useApiData(`${endpoints.getReportedData}`);


  const scrollHeight = useMemo(() => containerRef.current?.offsetHeight - 100, [containerRef.current?.offsetHeight]);



  const tabList = [
    'Creators',
    'Contents',
    // 'Comments',
  ];






  const handleFilterChange = (value, filterKey) => {
    const updatedValue = value.includes('Select') ? null : value;
    setFilters(prevFilters => ({
      ...prevFilters,
      [filterKey]: { ...prevFilters[filterKey], value: updatedValue },
    }));
  };

  const handleTabChange = (e) => {
    setActiveTab(e.target.value);
  };

  return (
    <div className='w-100'>
      <div className="tab-btn-container">
        {tabList.map((item, index) => (
          <button
            key={index}
            className={` ${activeTab === item ? 'active' : ''}`}
            onClick={handleTabChange}
            value={item}
          >
            {item}
          </button>
        ))}
      </div>
      <div className='p-3 w-100 card-wrap archive-page' ref={containerRef}>
        <TabContent
          activeTab={activeTab}
          data={data}
          filters={filters}
          scrollHeight={scrollHeight}
          loadingData={loadingData}
          onGlobalFilterChange={(e) => handleFilterChange(e.target.value, 'global')}
          handleFilterChange={handleFilterChange}
        />
      </div>
    </div>
  );
};

export default Archive;



const TabContent = ({ activeTab, data, filters, scrollHeight, loadingData, onGlobalFilterChange, handleFilterChange }) => {
  const navigate = useNavigate();
  const [commitSearch, setCommitSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('')
  // if (loadingData) return <div>Loading...</div>;
  // if (!data?.length) return <div>No data available</div>;
  const riskLevels = [
    'Select Risk Level',
    'High',
    'Medium',
    'Low',
  ];
  const categoryList = [
    'Select Category',
    ...comments?.category_list
  ];
  const contentStatuses = [
    'Select Status',
    'Reported',
    'AI Flagged',
  ];

  const filtered = comments.comments.filter(e => {
    if (selectedCategory === '') {
      return e
    } else {
      return e['details']['category']?.toLowerCase() === selectedCategory
    }
  })



  const commitsAfterFiltered = filtered.filter(el => {
    if (commitSearch === '') {
      return el
    } else {

      return el['comment_id']?.toLowerCase().includes(commitSearch)
    }

  })

  const handleCommitSearchChange = (e) => {
    const lowerCase = e.target.value.toLowerCase();
    setCommitSearch(lowerCase)
  }

  const onRowClick = useCallback((row) => {
    navigate('/category-details/content-details', { state: row.data });
  }, [navigate]);

  const handleCategoryChange = (e) => {

    if (e === 'Select Category' || !e) {
      setSelectedCategory('')
    } else {
      setSelectedCategory(e.toLowerCase())
    }
  }

  if (activeTab === 'Contents') {
    return (
      <>
        <div className='mb-3 d-flex'>
          <div className='me-3'>
            <p className='label'>Reported</p>
            <span>{data?.length} Content</span>
          </div>
          <Searchbar
            placeholder='Search Keyword'
            onChange={onGlobalFilterChange}
          />
          <Select
            options={riskLevels}
            defaultValue={'Select Risk Level'}
            placeholder={'Select Risk Level'}
            className="StatusDropdown ms-3"
            arrowSize={"15"}
            onChange={(value) => handleFilterChange(value, 'global')}
          />
        </div>
        <Table
          values={data}
          filters={filters}
          dataKey='identification_id'
          headers={archiveListHeaders}
          scrollHeight={scrollHeight}
          loading={loadingData}
          onRowClick={onRowClick}
        />
      </>
    );
  } else if (activeTab === 'Creators') {
    return (
      <div className='d-flex h-100 w-100 align-items-center justify-content-center'>
        Creators Report: Under Development
      </div>
    )
  } else if (activeTab === 'Comments') {
    return (
      <div className='reported-comment-wrapper h-100 w-100'>

        <div className="under-dev-mg d-flex h-100 w-100 align-items-center justify-content-center">
          Comments Report: Under Development
        </div>

        {/*  TEMPORARY COMMENTED FOR UNDER DEV. ===> UNTIL BE IS READY */}
        
        {/* <div className='mb-3 d-flex'>
          <div className='me-3'>
            <p className='label'>Reported</p>
            <span>{data?.length} Content</span>
          </div>
          <Searchbar
            placeholder='Search Keyword'
            onChange={handleCommitSearchChange}
          />
          <Select
            options={categoryList}
            defaultValue={'Select Category'}
            placeholder={'Select Category'}
            className="StatusDropdown ms-3"
            arrowSize={"15"}
            onChange={handleCategoryChange}
          />
        </div>
        {commitsAfterFiltered.map((comment) => (
          <div key={comment.comment_id} className="comment-card">


            <div className="avatar-wrapper">
              <div className="avatar-wrapper_profile">
                <img src={comment.avatar} alt={comment.user} />
                <h4 className='ms-3'>{comment.user}</h4>
              </div>
              <div className="comment-id">
                ID: {comment.comment_id}
              </div>
            </div>
            <div className="comment-details">
              <p>{comment.comment}</p>
              <ul className='details-list'>
                <li><p>Comment Time & Date: <span className='fw-bold'>{comment.details.report_date}</span></p></li>
                <li><p>Reported Time & Date: <span className='fw-bold'>{comment.comment_date}</span></p></li>
                <li><p>Social Media: <span className='fw-bold'>{comment.details.platform}</span></p></li>
                <li><p>Category: <span className='fw-bold'>{comment.details.category}</span></p></li>
                <li><p>Sub-Category: <span className='fw-bold'>{comment.details.subCategory}</span></p></li>
                <li style={{marginRight: '20px', listStyle: 'none', cursor: 'pointer'}}><svg width="17" height="18" viewBox="0 0 17 18" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M8.89954 0.303759C9.84936 0.289062 10.7937 0.297771 11.737 0.289062C11.7942 1.39999 12.1937 2.5316 13.0069 3.31703C13.8184 4.12206 14.9664 4.49055 16.0833 4.6152V7.53757C15.0366 7.50328 13.985 7.28555 13.0352 6.83487C12.6215 6.64763 12.2361 6.4065 11.8589 6.15993C11.854 8.28054 11.8676 10.3984 11.8453 12.5103C11.7887 13.5249 11.454 14.5346 10.8639 15.3707C9.91467 16.7624 8.26706 17.6698 6.57482 17.6981C5.53683 17.7574 4.49993 17.4744 3.61543 16.9529C2.14962 16.0886 1.11817 14.5063 0.967937 12.8081C0.949014 12.4484 0.946108 12.0881 0.959228 11.7282C1.08986 10.3473 1.77296 9.02624 2.83327 8.12759C4.03509 7.0809 5.71863 6.58231 7.29493 6.87733C7.30963 7.95233 7.26663 9.02624 7.26663 10.1012C6.54651 9.86828 5.70502 9.9336 5.0758 10.3707C4.61545 10.6739 4.26757 11.1201 4.08571 11.6405C3.93549 12.0085 3.97849 12.4173 3.98719 12.8081C4.15974 13.999 5.30496 15 6.52746 14.8917C7.33793 14.883 8.11466 14.4127 8.53704 13.7241C8.67366 13.483 8.82661 13.2364 8.83477 12.9529C8.90608 11.6547 8.87777 10.362 8.88648 9.0638C8.89247 6.13816 8.87777 3.22069 8.90009 0.304303L8.89954 0.303759Z" fill="#5B7DF5" />
                </svg></li>
              </ul>
            </div>
          </div>

        ))} */}
      </div>
    )
  }

  return <div>{activeTab}</div>;
};
