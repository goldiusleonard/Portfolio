import React, { useState } from 'react';
import arrowUp from '../../assets/icons/comment_arrow_up.svg';
// import comments from './CategoryDetails.json'
import Searchbar from '../../components/ui/inputs/Searchbar';
import useApiData from '../../hooks/useApiData';
import endpoints from '../../config/config.dev';
import LoaderAnimation from '../../components/LoaderAnimation';




const CommentUi = ({ handleReportComment, filterStatus }) => {
  const [commitSearch, setCommitSearch] = useState('')
  const { data: comments, loadingData } = useApiData(`${endpoints.getComments}?category=hate%20speech${filterStatus?.subCategory ? `&sub_category=${filterStatus?.subCategory}` : ''}${filterStatus?.topic ? `&topic=${filterStatus?.topic}` : ''}`);

  const commitsAfterFiltered = comments?.comments?.filter(el => {
    if (commitSearch === '') {
      return el
    } else {
      const lowerCaseSearch = commitSearch.toLowerCase();
    return (
      el['comment_id']?.toLowerCase().includes(lowerCaseSearch) ||
      el['user']?.toLowerCase().includes(lowerCaseSearch) ||
      el['comment']?.toLowerCase().includes(lowerCaseSearch) ||
      el['risk']?.toLowerCase().includes(lowerCaseSearch) ||
      el['details']?.subCategory?.toLowerCase().includes(lowerCaseSearch)
    )}
  })

  const handleCommitSearchChange = (e) => {
    const lowerCase = e.target.value.toLowerCase();
    setCommitSearch(lowerCase)
  }


  return (
    loadingData ?
      <LoaderAnimation />
      :
      <div className='overflow-auto'>
        <Searchbar placeholder='Search Keyword' onChange={handleCommitSearchChange} />
        {commitsAfterFiltered?.map((comment) => <Comment comment={comment} handleReportComment={handleReportComment} key={comment.id} />)}
      </div>
  )
}

export default CommentUi;

export const go2OriginalContent = (event, userHandle, contentId) => {
  event.preventDefault();
  event.stopPropagation();
  window.open(`https://www.tiktok.com/@${userHandle}/video/${contentId}`, '_blank', 'noopener,noreferrer');
}


function Comment({ comment, handleReportComment }) {
const  clickHandler= (e)=>{
  e.preventDefault();
  handleReportComment({
    id:comment.id,
    comment_id:comment.comment_id
  })
}
  return (
    <div key={comment.id} className="comment-card">
      <div className="avatar-wrapper">
        <img src={comment.avatar} alt={comment.user} />
        <h4>{comment.user}</h4>
      </div>
      <div className="comment-details">
        <div className="comment-date">
          {comment?.comment_date}
        </div>
        <div className='d-flex align-items-center justify-content-between me-2'>
          <div className="comment-id">
            ID: <span>{comment.comment_id}</span>
          </div>
          <div className={`risk-level ${comment.risk.toLowerCase()} text-capitalize`}>
              {comment.risk}
          </div>
        </div>
        <p>{comment?.comment}</p>

        <div className="tags">
          <span className="tag-title">Sub-Category</span>
          {/* {comment?.tags?.slice(0, 3).map((tag, index) => (
            <span key={index} className="tag">
              {tag}
            </span>
          ))} */}
          {/* {comment.tags.length > 3 &&
              <span className="tag plus">
                +{comment.tags.length - 3}
              </span>
            } */}
           <span className="tag">
              {comment.details.subCategory}
            </span>
          <span className="external-link float-right" onClick={(e) => go2OriginalContent(e, comment.user, comment?.video_id)}>
            <svg width="17" height="18" viewBox="0 0 17 18" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M8.89954 0.303759C9.84936 0.289062 10.7937 0.297771 11.737 0.289062C11.7942 1.39999 12.1937 2.5316 13.0069 3.31703C13.8184 4.12206 14.9664 4.49055 16.0833 4.6152V7.53757C15.0366 7.50328 13.985 7.28555 13.0352 6.83487C12.6215 6.64763 12.2361 6.4065 11.8589 6.15993C11.854 8.28054 11.8676 10.3984 11.8453 12.5103C11.7887 13.5249 11.454 14.5346 10.8639 15.3707C9.91467 16.7624 8.26706 17.6698 6.57482 17.6981C5.53683 17.7574 4.49993 17.4744 3.61543 16.9529C2.14962 16.0886 1.11817 14.5063 0.967937 12.8081C0.949014 12.4484 0.946108 12.0881 0.959228 11.7282C1.08986 10.3473 1.77296 9.02624 2.83327 8.12759C4.03509 7.0809 5.71863 6.58231 7.29493 6.87733C7.30963 7.95233 7.26663 9.02624 7.26663 10.1012C6.54651 9.86828 5.70502 9.9336 5.0758 10.3707C4.61545 10.6739 4.26757 11.1201 4.08571 11.6405C3.93549 12.0085 3.97849 12.4173 3.98719 12.8081C4.15974 13.999 5.30496 15 6.52746 14.8917C7.33793 14.883 8.11466 14.4127 8.53704 13.7241C8.67366 13.483 8.82661 13.2364 8.83477 12.9529C8.90608 11.6547 8.87777 10.362 8.88648 9.0638C8.89247 6.13816 8.87777 3.22069 8.90009 0.304303L8.89954 0.303759Z" fill="#5B7DF5"/>
            </svg>
          </span>
        </div>
        <div className="actions">
          {/* <button className="report-button">Report Account</button> */}
          <button className="report-button" onClick={clickHandler}>Report Comment</button>

        </div>
      </div>
    </div>
  )
}