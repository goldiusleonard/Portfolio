import React, { useState, useEffect } from "react";
import { Table as BootstrapTable } from "react-bootstrap";
import LoaderAnimation from "../LoaderAnimation";
import "bootstrap/dist/css/bootstrap.min.css";

export default function Table(props) {
  const [selectedRows, setSelectedRows] = useState([]);

  useEffect(() => {
    if (props.selection && props.selection.length === 0) {
      setSelectedRows([]);
    }
  }, [props.selection]);

  const filterValues = (values, filters) => {
    if (!filters || !filters.global) return values;

    const { value, status } = filters.global;
    const trimmedValue = value?.trim();

    return values.filter((item) => {
      const regex = new RegExp(`${trimmedValue}`, "i");
      const matchesValue =
        !trimmedValue ||
        (item.identification_id && regex.test(item.identification_id.trim())) ||
        (item.video_source && regex.test(item.video_source.trim())) ||
        (item.ai_topic && regex.test(item.ai_topic.trim()));

      const matchesStatus =
        !status ||
        (item.risk_status &&
          item.risk_status.toLowerCase() === status.toLowerCase());

      return matchesValue && matchesStatus;
    });
  };

  const filteredValues = filterValues(props.values, props.filters);

  const handleDoubleClick = (row) => {
    if (props.onRowDoubleClick) {
      props.onRowDoubleClick(row);
    }
  };

  const handleRowClick = (row) => {
    if (props.onRowDoubleClick) {
      props.onRowDoubleClick(row);
    }
  };

  const handleCheckboxClick = (row, event) => {
    event.stopPropagation(); // Prevent row click from triggering
    const isSelected = selectedRows.some((selectedRow) => selectedRow === row);
    let updatedSelection = [];

    if (isSelected) {
      updatedSelection = selectedRows.filter(
        (selectedRow) => selectedRow !== row
      );
    } else {
      updatedSelection = [...selectedRows, row];
    }

    setSelectedRows(updatedSelection);

    if (props.onRowClick) {
      props.onRowClick(row, !isSelected);
    }
  };

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedRows(filteredValues);
      if (props.onSelectAll) {
        props.onSelectAll(filteredValues);
      }
    } else {
      setSelectedRows([]);
      if (props.onSelectAll) {
        props.onSelectAll([]);
      }
    }
  };

  return (
    <>
      {props.loading ? (
        <LoaderAnimation />
      ) : (
        <div className="table-spacing">
          <BootstrapTable bordered hover>
            <thead className="table-fixed-header">
              <tr>
                {props.withCheckbox && (
                  <th style={{ width: "50px", paddingLeft: "8px" }}>
                    <input
                      type="checkbox"
                      className="table-checkbox"
                      onChange={handleSelectAll}
                      checked={
                        selectedRows.length === filteredValues.length &&
                        filteredValues.length > 0
                      }
                    />
                  </th>
                )}
                {/* {props.headers.map((header) => (
                                    <th key={header.field}>{header.header}</th>
                                ))} */}
                {props.headers.map((header, index) => (
                  <th key={`${header.field}-${index}`}>{header.header}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filteredValues.length === 0 ? (
                <tr>
                  <td
                    colSpan={
                      props.headers.length + (props.withCheckbox ? 1 : 0)
                    }
                    className="no-data-message"
                  >
                    No data available
                  </td>
                </tr>
              ) : (
                filteredValues.map((item, index) => (
                  <tr
                    key={index}
                    className="table-row"
                    onDoubleClick={() => handleDoubleClick(item)}
                    onClick={() => handleRowClick(item)}
                  >
                    {props.withCheckbox && (
                      <td
                        style={{
                          width: "50px",
                          paddingLeft: "10px !important",
                        }}
                        onClick={(event) => handleCheckboxClick(item, event)}
                      >
                        <input
                          type="checkbox"
                          className="table-checkbox"
                          checked={selectedRows.includes(item)}
                          onClick={(event) => handleCheckboxClick(item, event)}
                          readOnly
                        />
                      </td>
                    )}
                    {/* {props.headers.map((header) => (
                      <td key={header.field}>
                        {header.body ? header.body(item) : item[header.field]}
                      </td>
                    ))} */}
                    {props.headers.map((header, index) => (
  <td key={`${header.field}-${index}`}>
    {header.body ? header.body(item) : item[header.field]}
  </td>
))}

                  </tr>
                ))
              )}
            </tbody>
          </BootstrapTable>
        </div>
      )}
    </>
  );
}

Table.defaultProps = {
  values: [],
  headers: [],
  loading: false,
  withCheckbox: false,
  filters: null,
  onSelectAll: null,
};
