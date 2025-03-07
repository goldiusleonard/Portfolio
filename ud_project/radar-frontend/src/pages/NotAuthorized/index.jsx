// NotAuthorized.js
import React from 'react';
import './NotAuthorized.scss'; // Optional, if you want to add styling
import useBreadcrumb from '../../hooks/useBreadcrumb';

function NotAuthorized() {
  const title = 'Not Authorized'; 
	const hasBackButton = false;
	const hasDateFilter = false; 
  
  useBreadcrumb({ title, hasBackButton, hasDateFilter });
  return (
    <div className="setting-container">
      <h1>403 - Not Authorized</h1>
      <p>You do not have permission to view this page.</p>
    </div>
  );
}

export default NotAuthorized;