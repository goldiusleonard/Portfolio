import React from 'react'
import Table from './Table';
import Searchbar from '../ui/inputs/Searchbar';


import LoaderAnimation from '../LoaderAnimation';


function TableWithSearchbar(props) {
  const [filters, setFilters] = React.useState({
    global: { value: null, matchMode: 'contains'},
  });
  const searchChange = (e) => {
    const value = e.target.value;
    let _filters = { ...filters };

    _filters['global'].value = value;

    setFilters(_filters);
    
  };
  return (
    <>
      <div>
        <Searchbar placeholder='Search Creator' {...props.searchProps}  onChange={searchChange}/>
      </div>
      {!props.loadingData ? <Table  {...props.tableProps} value={props.data} onRowClick={props.onRowClick}  filters={filters}/> : <LoaderAnimation />}
    </>
  )
}

export default TableWithSearchbar
