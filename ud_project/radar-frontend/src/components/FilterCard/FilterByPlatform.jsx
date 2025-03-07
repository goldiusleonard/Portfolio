import React from 'react';
// import './filterCard.scss'

const FilterByPlatform = () => {
  return (
    <div className="container p-0"> 
      <div className="row"> 
        <div className="col"> 
          <div className="platform-box">
            Facebook
          </div>
        </div>
      </div>

      <div className="row"> 
        <div className="col"> 
          <div className="platform-box">
            Instagram
          </div>
        </div>
      </div>

      <div className="row">
        <div className="col"> 
          <div className="platform-box">
            TikTok
          </div>
        </div>
      </div>

      <div className="row">
        <div className="col"> 
          <div className="platform-box">
            X
          </div>
        </div>
      </div>
    </div>
  );
};

export default FilterByPlatform;
