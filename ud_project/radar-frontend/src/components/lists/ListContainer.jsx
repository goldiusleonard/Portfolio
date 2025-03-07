import React from 'react'

const ListContainer = ({ header,children}) => {
    return (
        <div className='list-container h-100 card-wrap '>
            <div className="seondary-title">{header}</div>
            <div className="h-100 w-100  overflow-auto  gap16   ">
            {children}
            </div>
        </div>
    )
}

export default ListContainer