import React from 'react';
import { useStatus } from '../../contexts/StatusContext';
import { Modal, ModalHeader, ModalBody, ModalFooter, Button } from 'reactstrap';
import warningIcon from '../../assets/icons/warning.svg'
import checkCircleIcon from '../../assets/icons/Check-circle.svg'
import CloseIcon from '../../assets/icons/CloseIcon'

const ModalLawReferencesConfirmation = ({
  type = 'delete' | 'created' | 'updated',
  isOpen,
  onClose = () => { },
  onAction = () => { }
}) => {
  const content = {
    delete: {
      title: 'Confirm Deletion',
      icon: warningIcon,
      message: 'Are you sure you want to delete this law reference? This action cannot be undone.',
      buttonOk: 'Delete Law'
    },
    created: {
      title: 'Law Uploaded Successfully!',
      icon: checkCircleIcon,
      message: 'The new legal reference has been added to the system and is now available for access.',
      buttonOk: undefined
    },
    updated: {
      title: 'Law Updated Successfully!',
      icon: checkCircleIcon,
      message: 'The law reference has been updated and changes are now reflected in the system.',
      buttonOk: undefined
    }
  }

  const headerButtonClose = (
    <button className="modal-law-references-confirmation-header-close-button">
      <CloseIcon
        fill="#80EED3"
        onClick={onClose}
      />
    </button>
  )

  return (
    <Modal
      className={`deactivate-modal ${type !== 'delete' ? 'modal-law-references-confirmation--success' : ''}`}
      isOpen={isOpen}
      toggle={undefined}
      size="md"
      centered
    >
      <ModalHeader
        className="modal-header-custom"
        toggle={onClose}
        close={headerButtonClose}
      >
        {content[type].title}
      </ModalHeader>
      <ModalBody className="modal-body-custom text-center">
        <div className="warning-icon">
          <img src={content[type].icon} alt="warning icon" />
        </div>
        <p className="confirmation-text">
          {content[type].message}
        </p>
      </ModalBody>
      <ModalFooter className="modal-footer-custom">
        {type === 'delete' ?
          <>
            <Button color="secondary" onClick={onClose}>
              Cancel
            </Button>
            <Button
              color="danger"
              onClick={onAction}
            >
              {content[type].buttonOk}
            </Button>
          </>
          :
          <Button
            className="btn-cancel"
            onClick={onClose}
          >
            {type !== 'delte' ? 'Close' : 'Cancel'}
          </Button>
        }
      </ModalFooter>
    </Modal>
  );
};

export default ModalLawReferencesConfirmation;
