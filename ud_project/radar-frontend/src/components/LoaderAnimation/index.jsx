import React from 'react'
import './LoaderAnimation.scss'
import LoaderGIF from '../../assets/images/loader.gif'


const LoaderAnimation = () => {
    return (
        <div className="loader loader--style2">
            {/* <svg
                version="1.1"
                id="loader-1"
                xmlns="http://www.w3.org/2000/svg"
                xmlnsXlink="http://www.w3.org/1999/xlink"
                x="0px"
                y="0px"
                width="40px"
                height="40px"
                viewBox="0 0 50 50"
                style={{ enableBackground: 'new 0 0 50 50' }}
                xmlSpace="preserve"
            >
                <rect x="0" y="0" width="4" height="10" fill="#333">
                    <animateTransform attributeType="xml"
                        attributeName="transform" type="translate"
                        values="0 0; 0 20; 0 0"
                        begin="0" dur="0.6s" repeatCount="indefinite" />
                </rect>
                <rect x="10" y="0" width="4" height="10" fill="#333">
                    <animateTransform attributeType="xml"
                        attributeName="transform" type="translate"
                        values="0 0; 0 20; 0 0"
                        begin="0.2s" dur="0.6s" repeatCount="indefinite" />
                </rect>
                <rect x="20" y="0" width="4" height="10" fill="#333">
                    <animateTransform attributeType="xml"
                        attributeName="transform" type="translate"
                        values="0 0; 0 20; 0 0"
                        begin="0.4s" dur="0.6s" repeatCount="indefinite" />
                </rect>
            </svg> */}
            <img src={LoaderGIF} alt="Loading..." />
        </div>
    )
}

export default LoaderAnimation
