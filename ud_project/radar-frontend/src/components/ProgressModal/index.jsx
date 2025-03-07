import React, { useState, useEffect } from 'react';
import { Modal, ModalBody, ModalFooter, Progress, Button, ModalHeader } from 'reactstrap';
import 'bootstrap/dist/css/bootstrap.min.css';
// import './ProgressModal.scss';

const ProgressModal = ({ isOpen, toggle, targetProgress }) => {
    // const [progress, setProgress] = useState(0);

    // useEffect(() => {
    //     setProgress(0);
    //     if (isOpen) {
    //         const interval = setInterval(() => {
    //             setProgress((prevProgress) => {
    //                 const newProgress = prevProgress + 1;
    //                 if (newProgress >= targetProgress) {
    //                     clearInterval(interval);
    //                     return targetProgress;
    //                 }
    //                 return newProgress;
    //             });
    //         }, 150);

    //         return () => clearInterval(interval);
    //     }
    // }, [isOpen, targetProgress]);

    return (
        <Modal isOpen={isOpen} toggle={toggle} centered size={'xl'} className='progress-container'>
            <ModalHeader toggle={toggle}>AI Agent Status: Process</ModalHeader>
            <ModalBody className="text-center">
                <div className='progress-wrapper'>
                    <h5>Processing: {targetProgress}%</h5>
                    <p>Please wait until the AI agent creation process is complete</p>
                    <div className="my-3">
                        <Progress value={targetProgress}>{`${targetProgress}%`}</Progress>
                    </div>
                </div>
            </ModalBody>
            <ModalFooter className="justify-content-center">
                <Button onClick={toggle} size='sm'>Back to AI Agent Dashboard</Button>
            </ModalFooter>
        </Modal>
    );
};

export default ProgressModal;
