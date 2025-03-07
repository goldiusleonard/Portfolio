import React from 'react';
// import './filterCard.scss'


const FilterByRisk = () => {
  return (
    <div className="container p-0 filter-risk"> 
      <div className="row"> 
        <div className="col"> 
          <div className="box high-box">
            High
          </div>
        </div>
      </div>

      <div className="row"> 
        <div className="col"> 
          <div className="box medium-box">
            Medium
          </div>
        </div>
      </div>

      <div className="row">
        <div className="col"> 
          <div className="box low-box">
            Low
          </div>
        </div>
      </div>
    </div>
  );
};

export default FilterByRisk;
