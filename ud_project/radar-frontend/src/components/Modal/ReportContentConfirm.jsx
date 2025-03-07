import React from 'react';
import { Modal, ModalHeader, ModalBody, ModalFooter, Button } from 'reactstrap';


const ReportContentConfirm = ({ isOpen, toggle, totalSelected, sendReport }) => {
  return (
    <Modal isOpen={isOpen} toggle={toggle} size="md" centered className='activation-modal report-content-confirm'>
      <ModalHeader className="modal-header-custom" toggle={toggle}>
        Report Selected
      </ModalHeader>
      <ModalBody className="modal-body-custom text-center">
        <p className="status-text">Are you sure you want to report {totalSelected} contents?</p>
      </ModalBody>
          <ModalFooter className="modal-footer-custom">
              <Button onClick={toggle} className='close-button'>
                Cancel
              </Button>
              <Button className="confirm-button" onClick={sendReport}>
                Report
              </Button>
          </ModalFooter>
    </Modal>
  );
};

export default ReportContentConfirm;
