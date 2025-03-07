import React from 'react';
import { useStatus } from '../../contexts/StatusContext';
import { Modal, ModalHeader, ModalBody, ModalFooter, Button } from 'reactstrap';
import warningIcon from '../../assets/icons/warning.svg'
// import './DeactivateModal.scss'; 

const DeactivateModal = ({ isOpen, toggle, isDeleteModal }) => {
  const {setIsAgentActive} = useStatus();

const handleDeactivate = () => {
  setIsAgentActive(false)
  toggle();

}
  
  return (
    <Modal isOpen={isOpen} toggle={toggle} size="md" centered className='deactivate-modal'>
      <ModalHeader className="modal-header-custom" toggle={toggle}>
              {isDeleteModal ? 'Delete Video Source' : 'Deactivate AI Agent'}
      </ModalHeader>
      <ModalBody className="modal-body-custom text-center">
        <div className="warning-icon">
          <img src={warningIcon} alt="warning icon" />
        </div>
              <p className="confirmation-text">
                  {isDeleteModal ?
                      'Are you sure you want to delete the video source? All parameters related to this video will be deleted.' :
          'Are you sure you want to deactivate AI Agent? All processes that depend on this AI agent will be stopped.'}
        </p>
      </ModalBody>
      <ModalFooter className="modal-footer-custom">
        <Button color="secondary" onClick={toggle}>
          Cancel
        </Button>
        <Button color="danger" onClick={handleDeactivate}>
                  {isDeleteModal ? 'Delete' : 'Deactivate'}
        </Button>
      </ModalFooter>
    </Modal>
  );
};

export default DeactivateModal;
