import React from 'react'
import useBreadcrumb from '../../hooks/useBreadcrumb';


const LandingPage = () => {
  const title = 'Settings'; 
	const hasBackButton = false;
	const hasDateFilter = false; 
  
  useBreadcrumb({ title, hasBackButton, hasDateFilter });

  return (
    <div className='setting-container'>
      <h4 className='p-3'>Under Development</h4>
      <p>This screen is currently under development and will be available soon. We’re working hard to make it great!</p>
    </div>
  )
}

export default LandingPage
