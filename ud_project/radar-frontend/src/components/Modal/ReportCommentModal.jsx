import React, { useState } from "react";
import "./DropContentModal.scss";
import Button from "../button/Button";
import { Modal, ModalBody, ModalFooter, ModalHeader } from "reactstrap";
import Checkbox from "../CheckBox/Checkbox";
import Select from "../Select/Select";
import { CloseIcon } from "../../assets/icons";
import justificationData from "../../pages/ContentDetails/contentDetails.json";
import useApiData from "../../hooks/useApiData";
import endpoints from "../../config/config.dev";
import LoaderAnimation from "../LoaderAnimation";
import { commentData } from '../OriginalContent/commentData';
import moment from "moment/moment";
import { go2OriginalContent } from "../../pages/CategoryDetails/CommentUi";




const options1 = [
	"Choose a subject for your email template",
	"Report of Violent Threats",
	"Report of Copyright Theft",
	"Request for Investigation",
];
const options2 = [
	"Choose list organization who will receive this email",
	"Communication & Industry Relation (example@email.com)",
	"Regulatory Policy (example@email.com)",
	"Consumer & Industry Affair (example@email.com)",
];


const ReportCommentModel = ({ isOpen, toggle, handleShowMessage, onCloseModal, id, comment_id }) => {
	const [selectedOptions1, setSelectedOptions1] = useState(options1[0]);
	const [selectedOptions2, setSelectedOptions2] = useState(options1[0]);
	const [activeTab, setActiveTab] = useState('comments')
	

	const handleTabButton = (e) => {
		const value = e.target.value;
		console.log(e.target.value)

		setActiveTab(value)
	}
	const { data: commentData, loadingData } = useApiData(`${endpoints.getCommentDetails}id=${id}&comment_id=${comment_id}`);

	const closeBtn = (
		<div className="close" onClick={toggle}>
			<CloseIcon fill="#fff" />
		</div>
	);

	const handleSelectChange1 = (option) => {
		setSelectedOptions1(option);
	};
	const handleSelectChange2 = (option) => {
		setSelectedOptions2(option);
	};

	const justification = {
		en: commentData?.content_justifications,
		my: commentData?.malay_justification
	}
	return (
		<Modal

			isOpen={isOpen}
			toggle={toggle}
			centered
			size="xl"
		>
			<ModalHeader toggle={toggle} close={closeBtn}>

				<span className="drop-content-header"> Report Comment</span>

			</ModalHeader>
			<ModalBody className="report-content-body comment-report-body">
				{loadingData ?
				<div className="loading">
					<LoaderAnimation />
					</div>
					:
					<>
						<div>
							<button className={`tab-button  ${activeTab === "comments" ? 'active' : null}`} onClick={handleTabButton} value="comments">Comments Detail</button>
							<button className={`tab-button  ${activeTab === "standardAndRegulation" ? 'active' : null}`} onClick={handleTabButton} value="standardAndRegulation">Standards & Regulations</button>
						</div>

						{activeTab === "comments" ?
							<div className="comment-body">
								<div className="right-section ">

									<p className="title-type-4 mb-2">Original Content</p>
									<div className="sample-photo position-relative">

										<img src={commentData?.contentPicture} alt="Video Thumbnail" />
										{/* <p className="url-container input-title">
											<span>Content URL: </span>
											<a href={commentData?.contentUrl} target="_blank" rel="noreferrer"> {commentData?.contentUrl}</a>
										</p> */}


										<div className="download-btn-wrapper position-absolute" style={{top: '10px', right: '10px'}}>
											<a href={commentData?.contentUrl} target="_blank" rel="noopener noreferrer">

												<i className="pi pi-cloud-download" style={{ fontSize: '1.75rem', color: '#00FFFF', marginRight: 8 }}></i>
											</a>
										</div>
									</div>
									<JustificationUi contents={justification} />
								</div>
								<div className="main-comment-details">
									<p className="title-type-4 mb-2">Main Comment</p>
									<MainComment comment={commentData} />

									<div>
										<div className="reply-header-wrapper">
											<p className="title-type-4 mt-2 mb-2">Main Comment’s Replies</p>
											<div className="last-update">Latest Update: {moment(commentData?.scrappedDate).format('MM/DD/YYYY')}</div>
										</div>
										<div key={commentData?.commentId} className="comment-card">


											{commentData?.replyOnComments?.length ? <div className="reply-comments-wrapper">
												{
													commentData?.replyOnComments?.map((replyComment, index) => {
														return (
															<div className="reply-comment-card" key={index}>
																<div className="avatar-wrapper">
																	<img src={replyComment?.replyCreatorPhoto} alt={replyComment?.replyCreatorName} />
																	<h4 className='ms-3'>{replyComment?.replyCreatorName}</h4>
																</div>
																<div className="comment">
																	{replyComment?.commentText}
																</div>
															</div>
														)
													})
												}

											</div> : <div className="no-reply">No replies yet</div>}
										</div>
									</div>

								</div>
							</div>
							:
							<div className="comment-body">
						<LawViolations commentData={commentData}/>
							</div>
						}



						<div>
							<div className="my-3">
								Send comment report to external organization (Optional)
							</div>
							<div className="creator-detail-input-wrapper w-100">
								<div className="input-title w-20">Report Subject</div>
								<Select
									options={options1}
									defaultValue={options1[0]}
									onChange={handleSelectChange1}
								/>
							</div>
							<div className="creator-detail-input-wrapper w-100">
								<div className="input-title w-20">Select Organization</div>
								<Select
									options={options2}
									defaultValue={options2[0]}
									onChange={handleSelectChange2}
								/>
							</div>
							<div className="creator-detail-input-wrapper w-100">
								<div className="input-title w-20">Send to custom email</div>
								<input
									type="email"
									placeholder="Type list of email who will receive this email  "
									style={{ width: "80%", margin: 0 }}
								/>
							</div>
						</div>
					</>
				}
			</ModalBody>
			<ModalFooter>
				<Button text="Cancel" variant="outline" onClick={toggle} />
				<Button text="Report Comment" variant="contain"
					onClick={toggle}
				/>
			</ModalFooter>
		</Modal>
	);
};

export default ReportCommentModel;





const JustificationUi = ({ contents }) => {
	const [lang, setLang] = React.useState('en')
	const texts = contents[lang ?? 'en']
	const handleLangChange = (e) => {
		const value = e.target.value;
		setLang(value)
	}

	return <div className="justification-wrapper">
		<div className="justification-wrapper-header">
			<h4> Justification</h4>
			<div className="justification-wrapper-buttons">
				<button className={`justification-wrapper-button ${lang === 'en' ? "btn-active" : null} `} onClick={handleLangChange} value='en'> English</button>
				<button className={`justification-wrapper-button ${lang === 'my' ? "btn-active" : null} `} onClick={handleLangChange} value='my'>Malay</button>
			</div>
		</div>
		<div className="justification-wrapper-content">
			{texts?.map(item => (
				<li key={item.justification} className="justification-item">
					<span className="justification-number">{item.justification}.</span>
					<div className="justification-text">
						{item.justification_text}
					</div>
				</li>
			))}
		</div>
	</div>

}


function MainComment({ comment }) {
	if (!comment) return null;
	const isoString = moment(comment.contentDate).format('HH:mm DD [of] MMM YYYY');

	return (
		<div key={comment.commentId} className="comment-card">

			<div className="avatar-wrapper">
				<div className="avatar-wrapper_profile">
					<img src={comment?.creatorPhoto} alt={comment?.creatorName} />
					<h4 className='ms-3'>{comment?.creatorName}</h4>
				</div>
			</div>
			<div className="comment-details">
				<div className="comment-date">
					{isoString}


				</div>
				<div className='d-flex align-items-center justify-content-between me-2'>
					<div className="comment-id">
						ID: <span>{comment.commentId}</span>
					</div>
					<div className={`risk-level ${comment.risk.toLowerCase()} text-capitalize`}>
						{comment.risk}
					</div>
				</div>
				<p className="comment">{comment?.mainComment}</p>

				<div className="tags">
					<span className="tag-title">Sub-Category</span>
					<span className="tag">
						{comment.commentSubCategories}
					</span>
					<span className="external-link float-right" onClick={(e) => go2OriginalContent(e, comment.creatorName, comment?.video_id)}>
						<svg width="17" height="18" viewBox="0 0 17 18" fill="none" xmlns="http://www.w3.org/2000/svg">
						<path d="M8.89954 0.303759C9.84936 0.289062 10.7937 0.297771 11.737 0.289062C11.7942 1.39999 12.1937 2.5316 13.0069 3.31703C13.8184 4.12206 14.9664 4.49055 16.0833 4.6152V7.53757C15.0366 7.50328 13.985 7.28555 13.0352 6.83487C12.6215 6.64763 12.2361 6.4065 11.8589 6.15993C11.854 8.28054 11.8676 10.3984 11.8453 12.5103C11.7887 13.5249 11.454 14.5346 10.8639 15.3707C9.91467 16.7624 8.26706 17.6698 6.57482 17.6981C5.53683 17.7574 4.49993 17.4744 3.61543 16.9529C2.14962 16.0886 1.11817 14.5063 0.967937 12.8081C0.949014 12.4484 0.946108 12.0881 0.959228 11.7282C1.08986 10.3473 1.77296 9.02624 2.83327 8.12759C4.03509 7.0809 5.71863 6.58231 7.29493 6.87733C7.30963 7.95233 7.26663 9.02624 7.26663 10.1012C6.54651 9.86828 5.70502 9.9336 5.0758 10.3707C4.61545 10.6739 4.26757 11.1201 4.08571 11.6405C3.93549 12.0085 3.97849 12.4173 3.98719 12.8081C4.15974 13.999 5.30496 15 6.52746 14.8917C7.33793 14.883 8.11466 14.4127 8.53704 13.7241C8.67366 13.483 8.82661 13.2364 8.83477 12.9529C8.90608 11.6547 8.87777 10.362 8.88648 9.0638C8.89247 6.13816 8.87777 3.22069 8.90009 0.304303L8.89954 0.303759Z" fill="#5B7DF5"/>
						</svg>
					</span>
				</div>
				<div className="actions">


				</div>
			</div>
		</div>
	)
}


const LawViolations = ({ commentData }) => {

	return (
	  <div className="law-violations">
		<h4>Law Violations</h4>
		{commentData?.law_violations &&
		  Object.entries(commentData.law_violations).map(([law, details]) => {
			console.log(law)
			const header=law.replace(/_/g, ' ').toUpperCase()==='AKTA HASUTAN'? "SEDITION ACT":law.replace(/_/g, ' ').toUpperCase();
			return(
			<div key={law} className="law-violation-item">
			  <h4>{header}</h4>
			  <ul>
				<li>
				  <strong>Sections Violated: </strong>{details['Sections Violated']}
				</li>
				<li>
				  <strong>Violation Analysis: </strong>{details['Violation Analysis']}
				</li>
			  </ul>
			</div>
		  )})}
		{commentData?.law_violations === undefined && (
		  <p>No law violations found.</p>
		)}
		{commentData?.law_violations === null && (
		  <p>Error loading law violations.</p>
		)}
	  </div>
	);
  };
  
