import React from "react";
import './subCategoryCard.scss';
import LoaderAnimation from "./../LoaderAnimation/index";
import { Button } from "reactstrap";

const SubCategoryCard = ({setSubCategory, subCategory, handleStatusCardClick, activeTopic, data, loading }) => {

  const isLength = data?.length === 3
  const handleGoBack = () => {
    handleStatusCardClick(subCategory, true)
  };

  return (
    loading ? (
      <LoaderAnimation />
    ) : (
        <>
          {subCategory &&
            <div className="filter-nav">
              <Button onClick={handleGoBack} className="btn">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20" fill="white">
                  <g filter="url(#filter0_b_1612_17452)">
                    <path opacity="1" fillRule="evenodd" clipRule="evenodd" d="M8.0532 10.0009L12.551 5.46527C12.8839 5.12914 12.8839 4.58702 12.551 4.25089C12.3924 4.09032 12.176 4 11.9503 4C11.7247 4 11.5083 4.09032 11.3497 4.25089L6.2512 9.39281C5.91724 9.72857 5.91724 10.2714 6.2512 10.6072L11.3495 15.7491C11.5083 15.9097 11.7247 16 11.9503 16C12.176 16 12.3924 15.9097 12.5512 15.7491C12.8839 15.4129 12.8839 14.8708 12.5508 14.5347L8.0532 10.0009Z" fill="white" fillOpacity="0.6" />
                  </g>
                  <defs>
                    <filter id="filter0_b_1612_17452" x="-182" y="-182" width="384" height="384" filterUnits="userSpaceOnUse" colorInterpolationFilters="sRGB">
                      <feFlood floodOpacity="0" result="BackgroundImageFix" />
                      <feGaussianBlur in="BackgroundImageFix" stdDeviation="90" />
                      <feComposite in2="SourceAlpha" operator="in" result="effect1_backgroundBlur_1612_17452" />
                      <feBlend mode="normal" in="SourceGraphic" in2="effect1_backgroundBlur_1612_17452" result="shape" />
                    </filter>
                  </defs>
                </svg>
                Back
              </Button>
              <nav aria-label="breadcrumb">
                <ol className="breadcrumb">
                <li
                    className='breadcrumb-item'
                    onClick={() => handleStatusCardClick(null, false, 'scam')}
                  >
                   <span> Scam </span> 
                    
                  </li>
                  <li
                    className={`breadcrumb-item ${!activeTopic && 'active'}`}
                    onClick={() => handleStatusCardClick(subCategory, false, 'sub')}
                  >
                    <span>{subCategory}</span>
                    
                  </li>
                  {activeTopic &&
                    <li
                      className={`breadcrumb-item ${activeTopic && 'active' }`}
                    >
                      <span>{activeTopic}</span>
                    </li>
                  }
                </ol>
              </nav>
            </div>
          }
        <div className={`subcategory-wrapper ${isLength ? 'main-3-items' : ''} ${subCategory ? 'h-85' : ''}`}>
          
        {data?.map((item, index) => (
          <div 
            key={index} 
            className={`subcategory-card ${activeTopic === item.name ? 'active' : ''}`}
            onClick={() => handleStatusCardClick(item.name)}
          >
            <div className="text-capitalize">{item.name}</div>
            <div>{item.percentage.toFixed(1)}%</div>
            
          </div>
        ))}
      </div></>
    )
  );
}

export default SubCategoryCard;
