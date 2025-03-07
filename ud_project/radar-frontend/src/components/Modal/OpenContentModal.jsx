import React, { useState } from "react";
import axios from "axios";
import "./ReportContentModal.scss";
import Button from "../button/Button";
import { Modal, ModalBody, ModalFooter, ModalHeader } from "reactstrap";
import Table from "../tables/Table";
import useApiData from "../../hooks/useApiData";
import endpoints from '../../config/config.dev';
import { CloseIcon } from "../../assets/icons";



const OpenContentModal = ({ isOpen, toggle, data }) => {

	const closeBtn = (
		<div className="close" onClick={toggle}>
			<CloseIcon fill="$white" />
		</div>
	);


	return (
		<Modal
			style={{ width: "60%" }}
			isOpen={isOpen}
			toggle={toggle}
			centered
			size="xl"
			className="content-preview-modal"
		>
			<ModalHeader toggle={toggle} close={closeBtn}>
				<div className="drop-content-header">
					<h2>Content Preview</h2>
				</div>
			</ModalHeader>
			<ModalBody className="preview-content-body">
				<div className="iframe-wrapper">
					{/* <iframe width="375" height="667" src={`https://www.tiktok.com/embed/v2/${content_url}`}></iframe> */}
					<video autoPlay loop controls className="w-100 h-100">
						<source
							src={data?.content_url}
							type="video/mp4"
						/>
						Your browser does not support the video tag.
					</video>
				</div>
				<div className="transcription-wrapper">
					<div className="transcription-title">Audio Transcription</div>
					{data?.original_transcription ?
						<div className="t-text">
							{data?.original_transcription}
						</div>
						:
						<div className="d-flex align-items-center no-transcription justify-content-center">No audio or voice-over is available in this video.</div>
					}
				</div>

			</ModalBody>
			<ModalFooter>
				{/* <Button text="Cancel" variant="outline" onClick={toggle} /> */}
			</ModalFooter>
		</Modal>
	);
};

export default OpenContentModal;
