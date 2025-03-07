import React, { useState } from "react";
import "./DropContentModal.scss";
import Button from "../button/Button";
import { Modal, ModalBody, ModalFooter, ModalHeader } from "reactstrap";
import Checkbox from "../CheckBox/Checkbox";
import { CloseIcon } from "../../assets/icons";

const DropContentModal = ({ isOpen, toggle, handleShowMessage }) => {
	const closeBtn = (
		<div className="close" onClick={toggle}>
			<CloseIcon fill="#fff" />
		</div>
	);
	const [checkboxes, setCheckboxes] = useState({
		checkbox1: true,
		checkbox2: false,
		checkbox3: false,
		checkbox4: false,
		checkbox5: false,
	});

	const handleCheckboxChange = (e) => {
		const { name, checked } = e.target;
		setCheckboxes({ ...checkboxes, [name]: checked });
	};
	return (
		<Modal
			style={{ width: "850px" }}
			isOpen={isOpen}
			toggle={toggle}
			centered
			size="xl"
		>
			<ModalHeader toggle={toggle} close={closeBtn}>
				<div className="drop-content-header">
					<h2>Drop Content</h2>
					<p>The content will be moved to the archive menu</p>
				</div>
			</ModalHeader>
			<ModalBody>
				<div className="drop-content-modal-content">
					<div className="drop-content-radio-group">
						<Checkbox
							id="checkbox1"
							checked={checkboxes.checkbox1}
							name="checkbox1"
							value="value1"
							onChange={handleCheckboxChange}
							label="No issues found with the content"
						/>
						<Checkbox
							id="checkbox2"
							checked={checkboxes.checkbox2}
							name="checkbox2"
							value="value2"
							onChange={handleCheckboxChange}
							label="Content is unrelated to the designated category."
						/>
						<Checkbox
							id="checkbox3"
							checked={checkboxes.checkbox3}
							name="checkbox3"
							value="value3"
							onChange={handleCheckboxChange}
							label="Content marked with the AI Flag is deemed inappropriate"
						/>
						<Checkbox
							id="checkbox4"
							checked={checkboxes.checkbox4}
							name="checkbox4"
							value="value4"
							onChange={handleCheckboxChange}
							label="The content is either unavailable or has been removed"
						/>
						<Checkbox
							id="checkbox5"
							checked={checkboxes.checkbox5}
							name="checkbox5"
							value="value5"
							onChange={handleCheckboxChange}
							label="Others"
						/>
					</div>
					<div className="drop-content-justification">
						<p>Justification (Optional)</p>
						<textarea
							placeholder="Write your justification here..."
							className="custom-textarea"
						/>
					</div>
				</div>
			</ModalBody>
			<ModalFooter>
				<Button text="Cancel" variant="outline" onClick={toggle} />
				<Button text="Mark as Resolved" variant="contain"
					onClick={() => {
						toggle();
						handleShowMessage('This feature will be available soon.');
					}} 
				/>
			</ModalFooter>
		</Modal>
	);
};

export default DropContentModal;
