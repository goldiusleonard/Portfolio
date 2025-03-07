import React, { useState } from "react";
import Table from "../tables/Table";
import { getUserFromLocalStorage } from "../../Util/index";
import lawReferencesDataTable from "../../data/sampleJson/lawReferencesDataTable.json";

const LawReferences = ({
    data,
    filters,
    loading = false,
    onRowClick = (data) => { },
    onAddNewLaw = () => { },
}) => {
    const user = getUserFromLocalStorage();

    const listHeader = [
        { field: "name", header: "Law Name" },
        { field: "category", header: "Category" },
        { field: "effective_date", header: "Effective Date" },
        { field: "upload_date", header: "Upload Date" },
        { field: "publisher", header: "Publisher" },
        { field: "summary", header: "Summary" },
    ];

    function EmptyScreen() {
        return (
            <div className="law-references-empty-state">
                <p>
                    There is no Law available,
                    <br />
                    <br /> upload a new Law to start.
                </p>
                <BtnAddNewLaw />
            </div>
        );
    }

    const BtnAddNewLaw = () => {
        return (
            <button className="btn-add-law" onClick={onAddNewLaw}>
                <span>+</span>Add New Law
            </button>
        );
    };

    return (
        <div className="law-references-table">
            <Table
                values={data}
                filters={filters}
                dataKey="law-references"
                headers={listHeader}
                onRowClick={({ data }) => onRowClick(data)}
                loading={loading}
                role={user.role}
                emptyMessage={EmptyScreen}
                useExactHeader
                disabledCheckForIsPublished
            />
        </div>
    );
};

export default LawReferences;
