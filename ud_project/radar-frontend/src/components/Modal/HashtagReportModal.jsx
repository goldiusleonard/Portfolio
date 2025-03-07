import React, { useState } from "react";
import axios from "axios";
import "./ReportContentModal.scss";
import Button from "../button/Button";
import { Modal, ModalBody, ModalFooter, ModalHeader } from "reactstrap";
import Table from "../tables/Table";
import useApiData from "../../hooks/useApiData";
import endpoints from '../../config/config.dev';
import {
	contentsListHeaders,
	similarContentsListHeaders,
} from "../../data/workspaceTableData";
import { CloseIcon } from "../../assets/icons";
import Select from "../Select/Select";
import { Tooltip } from '..';
import EditorTemplate from '../../assets/images/emailTemplate.png'
import { capitalizeFirstLetter } from "../../Util";
import HashTagRow from "../ui/hashtag/HashTagRow";


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
const options3 = [
	"Type list of email who will receive this email  ",
	"Communication & Industry Relation (example@email.com)",
	"Regulatory Policy (example@email.com)",
	"Consumer & Industry Affair(example@email.com)",
];

const HashtagReportModal = ({ isOpen, toggle, chosenContent, handleReportContents, onCloseModal }) => {

	const { data, loadingData } = useApiData(endpoints.getSimilarContents + `?video_id=${chosenContent?.content_id}`);
	const [sendLoading, setSendLoading] = useState()
	const {

		identification_id,
		ai_topic,
		sub_category,
		user_handle,
		content_id,
		content_date,
		risk_level,
		social_media_type,
		report_status,
		content_report_id

	} = chosenContent || {}

	const extractedFromContent = {
		video_id: content_id,
		identification_id,
		video_posted_timestamp: content_date,
		video_source: social_media_type,
		ai_topic,
		status: report_status,
		risk_status: risk_level,
		sub_category,
		video_api_id: content_report_id,
		user_handle
	}
	const [selectedContents, setSelectedContents] = useState([extractedFromContent]);

	const [selectedOptions1, setSelectedOptions1] = useState(options1[0]);
	const [selectedOptions2, setSelectedOptions2] = useState(options1[0]);
	const [selectedOptions3, setSelectedOptions3] = useState(options1[0]);

	const handleSelectChange1 = (option) => {
		setSelectedOptions1(option);
	};
	const handleSelectChange2 = (option) => {
		setSelectedOptions2(option);
	};
	const handleSelectChange3 = (option) => {
		setSelectedOptions3(option);
	};
	const closeBtn = (
		<div className="close" onClick={toggle}>
			<CloseIcon fill="#fff" />
		</div>
	);
	const handleselection = (e) => {
		setSelectedContents(e.value);
	};

	const reportContents = () => {
		handleReportContents(selectedContents);

		sendReport()
	};
	const sendReport = async () => {
		setSendLoading(true);
		try {
			const response = await axios({
				method: 'post',
				url: endpoints.postVideoContentReport,
				data: selectedContents,
			});
			console.log(JSON.stringify(response.data));
		} catch (error) {
			console.error(error);
		} finally {
			setSendLoading(false);
			onCloseModal()
		}
	}

	const handleEditTemplate = () => {
		setIsTemplate(!isTemplate)
	}

	const onCancel = () => {
		setIsTemplate(false)
		toggle()
	}

	const handleNext = () => setCurrentStep((prevStep) => prevStep + 1);
	const handleBack = () => setCurrentStep((prevStep) => prevStep - 1);

	const go2OriginalContent = (event) => {
		const { user_handle, content_id, video_id
		} = event.data;
		if (user_handle && (content_id || video_id
		)) {
			window.open(`https://www.tiktok.com/@${user_handle}/video/${content_id ?? video_id
				}`, '_blank', 'noopener,noreferrer');
		}
	}


	const [tooltipVisible, setTooltipVisible] = React.useState(false);
	const [tooltipPosition, setTooltipPosition] = React.useState({ x: 0, y: 0 });
	const [tooltipContent, setTooltipContent] = React.useState("");
	const [isTemplate, setIsTemplate] = useState(false);
	const [currentStep, setCurrentStep] = useState(1);
	//   const sentences = text.match(/[^\.!\?]+[\.!\?]+/g);

	const handleTooltip = (e) => {
		if (!e.data.justification_split) return;

		setTooltipContent(e.data.justification_split);
		setTooltipPosition({
			x: e.originalEvent
				.clientX, y: e.originalEvent
					.clientY
		});

		setTooltipVisible(true);
	}

	if (!chosenContent) return null;
	return (
		<Modal
			style={{ width: "60%" }}
			isOpen={isOpen}
			toggle={toggle}
			centered
			size="xl"

		>
			<div onMouseEnter={() => setTooltipVisible(false)}
				onMouseDown={() => setTooltipVisible(false)}
				onMouseLeave={() => setTooltipVisible(false)}>
				<ModalHeader toggle={toggle} close={closeBtn}

				>
					<div className="drop-content-header">
						<h2>Report Content</h2>
						<p>Category: Hate Speech| Sub-Category: {capitalizeFirstLetter(sub_category)}</p>
					</div>
				</ModalHeader>
				<ModalBody className="report-content-body">
					{currentStep === 1 &&
						<>
							
								<HashTagRow level={chosenContent.risk_level} item={{
                                    name: '#Bitcoin',
                                    level: 'High'
                                }} onClick={handleEditTemplate} />
						
							<div className="report-optional-table-container" >
								<p>Do you also want to report Similar Contents? (Optional)</p>
								<div className="report-optional-sub-container">
									<div className="report-optional-table">
										<Table
											dataKey="video_id"
											values={data}
											headers={similarContentsListHeaders}
											withCheckbox
											selection={selectedContents}
											onSelectionChange={handleselection}
											loading={loadingData}
											// onRowClick={handleSelectChange}
											onRowDoubleClick={go2OriginalContent}
											onRowMouseEnter={handleTooltip}
										// onMouseLeave={() => setTooltipVisible(false)}
										/>
									</div>
								</div>
							</div>
						</>}
					<div>
						<div className="my-4">
							Send content report to External Organization (Optional)
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
					{currentStep === 2 &&
						<div className="report-editor">
							<Button text="Edit" variant="contain" />
							<img src={EditorTemplate} alt="EditorTemplate" />
						</div>
					}
				</ModalBody>

				<ModalFooter>
					{currentStep === 1 && <Button text="Cancel" variant="outline" onClick={toggle} />}
					{currentStep === 1 && <Button text="Next" variant="contain" onClick={handleNext} />}
					{currentStep === 2 && <Button text="Back" variant="outline" onClick={handleBack} />}
					{currentStep === 2 && <Button text="Report Content" variant="contain" onClick={reportContents} />}
				</ModalFooter>
				<Tooltip visible={tooltipVisible} onClose={() => setTooltipVisible(false)} tooltipPosition={tooltipPosition.y} content={tooltipContent} />
			</div>
		</Modal>
	);
};

export default HashtagReportModal;
