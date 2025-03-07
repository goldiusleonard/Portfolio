import React from 'react';
import { Modal, ModalHeader, ModalBody, ModalFooter, Button } from 'reactstrap';

import { useNavigate } from 'react-router-dom';
import markIcon from '../../assets/icons/rounded_mark.svg'
// import './ActivateAgentModal.scss';


const ActivateAgentModal = ({ isOpen, toggle }) => {

const handleClose = () => {
  toggle();
}
  
  return (
    <Modal isOpen={isOpen} toggle={toggle} size="md" centered className='activation-modal'>
      <ModalHeader className="modal-header-custom" toggle={toggle}>
        AI Agent Status: Active
      </ModalHeader>
      <ModalBody className="modal-body-custom text-center">
        <div className="success-icon">
            <img src={markIcon} alt="mark icon" />
        </div>
        <p className="status-text">AI agent successfully activated</p>
      </ModalBody>
      <ModalFooter className="modal-footer-custom">
        <Button color="light" onClick={handleClose} className="close-button">
          Close
        </Button>
      </ModalFooter>
    </Modal>
  );
};

export default ActivateAgentModal;
