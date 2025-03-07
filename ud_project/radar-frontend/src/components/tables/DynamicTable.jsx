import React, { useState } from "react";
import { DataTable } from "primereact/datatable";
import { Column } from "primereact/column";
import { prototype } from "apexcharts";

export default function Table(props) {
	const [selectedProducts, setSelectedProducts] = useState(null);
	const [rowClick] = useState(true);
	const [selectedId, setSelectId] = useState(null);

	const [isOpen, setIsOpen] = useState(false);

	const handleOpenModal = () => {
		setIsOpen(true);
	};

	const handleCloseModal = () => {
		setIsOpen(false);
	};
	const handleRowClick = (e) => {
		if (e.data.id === selectedId) {
			setSelectId(null);
			return;
		}
		setSelectId(e.data.id);
	};

	const selectAllHandler = () => {
		selectedProducts
			? setSelectedProducts(null)
			: setSelectedProducts(props.values);
		setSelectId(null);
	};
	return (
		<div className="table-card card">
			<div className="table-body">
				<DataTable
					value={props.values}
					selectionMode={rowClick ? null : "checkbox"}
					selection={selectedProducts}
					onSelectionChange={(e) => setSelectedProducts(e.value)}
					dataKey="id"
					onRowClick={handleRowClick}
				>
					<Column
						selectionMode="multiple"
						// headerStyle={{ position: "fixed", marginLeft: 16 }}
					></Column>
					{props.headers.map((header) => {
						return <Column key={header.field} {...header} />;
					})}
				</DataTable>
			</div>
		</div>
	);
}

prototype.defaultProps = {
	values: [],
	headers: [],
};
