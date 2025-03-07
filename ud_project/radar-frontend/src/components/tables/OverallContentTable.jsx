
import React, { useState } from 'react';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';
// import { prototype } from 'apexcharts';
import Detail from './Detail';
import PopupView from './Dialog';
import Table from './Table';
// import { ProductService } from './service/ProductService';



export default function OverallContentTable(props) {
    // const [products, setProducts] = useState(values);
    const [selectedProducts, setSelectedProducts] = useState(null);
    const [rowClick,] = useState(true);
    const [selectedId, setSelectId] = useState(null);

    const [isOpen, setIsOpen] = useState(false);

    const handleOpenModal = () => {
        setIsOpen(true);
    }

    const handleCloseModal = () => {
        setIsOpen(false);
    }
    const handleRowClick = (e) => {
        if (e.data.id === selectedId) {
            setSelectId(null);
            return;
        }
        setSelectId(e.data.id);
    }

    const selectAllHandler = () => {
        selectedProducts ? setSelectedProducts(null) :
            setSelectedProducts(props.values)
        setSelectId(null);
    }


    const selectText = selectedProducts ? 'Deselect all' : 'Select all'
    return (
        <div className="card">
            <div className='table-top-header'>
                <div className='header-button-container'>
                    <button className='table-button table-button-report' >Report</button>
                    <button className='table-button table-button-selectAll' onClick={selectAllHandler}>{selectText}</button>
                </div>
                <div className='header-button-container'>
                    <button className='table-button table-button-report'>Remove Filters</button>
                    <button className='table-button table-button-content'>Content Quantity
                        <span> 65</span></button>
                    <button className='table-button table-button-content'>Latest Update
                        <span> 8/05/2024</span></button>
                </div>

            </div>
            <div className='table-body'>

                {/* <DataTable

                    value={props.values} selectionMode={rowClick ? null : 'checkbox'}
                    selection={selectedProducts}
                    onSelectionChange={(e) => setSelectedProducts(e.value)}
                    dataKey="id"

                    onRowClick={handleRowClick}

                >

                    {props.Checkbox&&<Column selectionMode='multiple' headerStyle={{ visibility: 'hidden', marginLeft: 16 }}></Column>}
                    {props.headers.map((header) => {
                        return <Column key={header.field} {...header} />;
                    })}

                </DataTable> */}
                <Table
                    values={props.values}
                    onSelectionChange={(e) => setSelectedProducts(e.value)}
                    onRowClick={handleRowClick}
                    selection={selectedProducts}
                    headers={props.headers}
                    selectionMode={rowClick ? null : 'checkbox'}
                    withCheckbox
                />

                {selectedId && <Detail handleOpenModal={handleOpenModal} />}
                {<PopupView visible={isOpen} onHide={handleCloseModal} values={props.values} headers={props.headers} />}
            </div>
        </div>
    );
}

// prototype.defaultProps = {
//     values: [],
//     headers: [],
// };