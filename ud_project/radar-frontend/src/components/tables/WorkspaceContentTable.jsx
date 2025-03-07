import React, { useState } from "react";
// import { prototype } from "apexcharts";
import Detail from "./Detail";
import PopupView from "./Dialog";
import Table from "./Table";

const WorkspaceContentTable = (props) => {
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
		if (e.data.video_id === selectedId) {
			setSelectId(null);
			return;
		}
		setSelectId(e.data.video_id);
	};

	const selectAllHandler = () => {
		selectedProducts
			? setSelectedProducts(null)
			: setSelectedProducts(props.values);
		setSelectId(null);
	};

	const selectText = selectedProducts ? "Deselect all" : "Select all";
	return (
		<div>
			<div className="table-body">
				<Table
				dataKey="video_id"
					values={props.values}
					onSelectionChange={(e) => setSelectedProducts(e.value)}
					onRowClick={handleRowClick}
					selection={selectedProducts}
					headers={props.headers}
					selectionMode={rowClick ? null : "checkbox"}
					withCheckbox
					{...props}
				/>

				{selectedId && <Detail setSelectId={setSelectId} handleOpenModal={handleOpenModal} id={selectedId} />}
				{
					<PopupView
						visible={isOpen}
						onHide={handleCloseModal}
						values={props.values}
						headers={props.headers}
					/>
				}
			</div>
		</div>
	);
}

// prototype.defaultProps = {
// 	values: [],
// 	headers: [],
// };

export default WorkspaceContentTable;