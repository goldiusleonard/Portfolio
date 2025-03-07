import React from 'react'

function UploadedDocuments({legalDocument}) {
  return (
    <div className='agent-category-container h-100'>
    <div className=" category-breadcrumb-title ">Supported Legal Documents</div>
    <ul className='overflow-auto h-75 mt-2'>
      {legalDocument && legalDocument.length > 0 && legalDocument.map((document, index) => (
        <li className='category-breadcrumb mb-1' key={index}>{document}</li>
      ))}
    </ul>
    </div>
  )
}

export default UploadedDocuments