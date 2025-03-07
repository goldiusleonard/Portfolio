
import React, { useState } from "react";
import { Dialog } from 'primereact/dialog';
import { DataTable } from 'primereact/datatable';
import { Column } from 'primereact/column';

export default function PopupView(props) {

    const [rowClick] = useState(true);
    const [selectedProducts, setSelectedProducts] = useState(null);

    return (

        <Dialog

            visible={props?.visible}
            modal

            onHide={props?.onHide}
            position='center'
            // style={{ width: '80vw' }}
            showHeader={false}
            breakpoints={{ '960px': '80vw' }}
            className="dialog"
            maskClassName='dialog-mask'
        >

            <div className="dialog-header">
                <p>Similar Contents</p>
                <button className='table-button table-button-report' >Report</button>


            </div>



            {props.values && <DataTable

                value={props.values}
                selectionMode={rowClick ? null : 'checkbox'}
                selection={selectedProducts}
                onSelectionChange={(e) => setSelectedProducts(e.value)}
                dataKey="id"

                // onRowClick={handleRowClick}
                tableStyle={{ width: '100%', color: '#00FFFF', fontSize: '20px', fontWeight: '400' }}
                showHeaders={false}

            >

                <Column selectionMode='multiple' headerStyle={{ visibility: 'hidden', marginLeft: 16 }}></Column>
                {props?.headers?.map((header) => {

                    return <Column key={header.field} {...header} />;
                })}

            </DataTable>}

            <div className="dialog-footer">


                <button className='table-button table-button-selectAll' onClick={props.onHide}>Cancel</button>
                <button className='table-button table-button-report' >Continue</button>


            </div>
        </Dialog>

    )
}
