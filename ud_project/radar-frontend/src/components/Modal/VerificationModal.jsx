import React from "react";
import { Modal, ModalHeader, ModalBody } from "reactstrap";
import { Carousel } from "react-bootstrap";
import { upin } from '../../assets/images';
import "bootstrap/dist/css/bootstrap.min.css";
import "./VerificationModal.scss";

const VerificationModal = ({ isOpen, toggle }) => {
  const slides = [
    { src: upin, altText: "Slide 1" },
    { src: upin, altText: "Slide 2" },
    { src: upin, altText: "Slide 3" },
    // Add more slides as needed
  ];

  return (
    <Modal isOpen={isOpen} toggle={toggle} size="xl" centered className="scanned-result-modal">
      <ModalHeader toggle={toggle}>Sample of Scanned AI Agent Results</ModalHeader>
      <ModalBody>
        <div className="modal-content-wrapper">
          <div className="carousel-section">
            <Carousel className="custom-carousel" interval={null}>
              {slides.map((slide, index) => (
                <Carousel.Item key={index} className="carousel-item-wrapper">
                  <img src={slide.src} alt={slide.altText} className="carousel-image" />
                </Carousel.Item>
              ))}
            </Carousel>
          </div>
          <div className="content-section">
            <h5>Content URL</h5>
            <a href="https://www.tiktok.com/video/7176305936829517061?is_copy">
              https://www.tiktok.com/video/7176305936829517061?is_copy
            </a>
            <p className="justification-text">
              According to the video, there are strong indications that the content might be high likely a scam...
            </p>
            <div className="parameters">
              <ul>
                <li>Poor grammar and spelling errors: <strong>High</strong></li>
                <li>Untraceable transactions: <strong>High</strong></li>
                <li>Inconsistent Tone: <strong>High</strong></li>
                <li>Incomplete Information: <strong>High</strong></li>
                <li>Misleading Information: <strong>High</strong></li>
                <li>Inviting users to click a URL link: <strong>Medium</strong></li>
              </ul>
            </div>
          </div>
        </div>
      </ModalBody>
    </Modal>
  );
};

export default VerificationModal;
