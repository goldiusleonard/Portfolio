import React from 'react';
import { Button } from 'reactstrap';
import { useNavigate } from 'react-router-dom';
import './topCard.scss';

const TopCards = ({ handleClick, filterValue, data }) => {
  const navigate = useNavigate();

  const handleViewWorkspace = () => {
    navigate('/workspace');
  };

  return (
    <div className="categories-filter-wrapper">
      <div className='left-action'>
        <div className={`categories-filter`} >
            Total Scanned Content
            <span style={{ fontWeight: 'normal' }}>
              {data?.scanned_content.toLocaleString()}
            </span>
        </div>
      </div>
      <div className='right-actions'>
        <div className="categories-filters">
          <div
            className={`categories-filter ${filterValue === 'AI Flagged Content' ? 'active' : ''}`}
            onClick={() => handleClick('AI Flagged Content')}
          >
            Ai Flagged Content
          </div>
          <div
            className={`categories-filter ${filterValue === 'Reported' ? 'active' : ''}`}
            onClick={() => handleClick('Reported')}
          >
            Reported Content
          </div>
          <div
            className={`categories-filter ${filterValue === 'Resolved' ? 'active' : ''}`}
            onClick={() => handleClick('Resolved')}
          >
            Resolved Content
          </div>
        </div>
        <Button className="btn" onClick={handleViewWorkspace}>
          Your Workspace
          <div>
            <svg width="13" height="22" viewBox="0 0 13 22" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M8.08108 11L0 2.95L2.45946 0.5L13 11L2.45946 21.5L0 19.05L8.08108 11Z" fill="white" />
            </svg>
          </div>
        </Button>
      </div>
    </div>
  );
};

export default TopCards;
