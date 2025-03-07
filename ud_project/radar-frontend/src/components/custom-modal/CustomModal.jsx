import React from "react";
import { Modal, ModalBody, ModalFooter, ModalHeader } from "reactstrap";
import "bootstrap/dist/css/bootstrap.min.css";
// import './CustomModal.scss';

const CustomModal= ({ isOpen, toggle,title, subTitle, content,footer, className, size = 'xl'}) => {
    return (
        <Modal isOpen={isOpen} toggle={toggle} centered size={size} className={`global-cutom-modal ${className}`}>
            <ModalHeader toggle={toggle}>
                {title}
                {subTitle && <p className='pop-up-sub-title'>{subTitle}</p>}
            </ModalHeader>
            <ModalBody className="text-center">
              {content}
            </ModalBody>
            <ModalFooter className="justify-content-center">
               {footer}
            </ModalFooter>
        </Modal>
    );
};

export default CustomModal;
