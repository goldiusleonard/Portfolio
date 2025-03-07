import React from "react";
import { DataTable } from "primereact/datatable";
import { Column } from "primereact/column";
import LoaderAnimation from "../LoaderAnimation";
import { useStatus } from "../../contexts/StatusContext";
export default function Table(props) {
  const { isAgentActive } = useStatus();
  const role = props?.role;

  const filteredValues =
    role === "Officer"
      ? props.disabledCheckForIsPublished ? props?.values : props?.values.filter((item) => item.isPublished)
      : props?.values;

  const statusBodyTemplate = (rowData) => {
    if (rowData.status === "Ready" && !isAgentActive) {
      return "Ready (Inactive)";
    }
    return rowData.status; // Default status
  };

  const totalContentBodyTemplate = (rowData) => {
    return `${rowData.totalContent} Scanned`;
  };
  return (
    <>
      {props.loading ? (
        <LoaderAnimation />
      ) : (
        <DataTable
          value={filteredValues.length > 0 && filteredValues.map((item, index) => ({
            ...item,
            _uniqueId: index,
          }))}
          dataKey="_uniqueId"
          selectionMode={"checkbox"}
          // selection={props.selectedProducts}
          // onSelectionChange={handOnSelectionChange}
          // dataKey={props.dataKey ?? 'id'}
          scrollable
          scrollHeight={props.scrollHeight ?? "100%"}
          {...props}
          rowClassName={props.rowClassName ?? "table-row"}
        >
          {props.withCheckbox && (
            <Column
              selectionMode="multiple"
              className="checkboxheader"
            ></Column>
          )}
          {props.headers.map((header, index) => {
            const isRank = header.header === "Rank";
            const style = isRank ? { minWidth: "30px" } : { minWidth: "130px" };
            if (index === props.headers.length - 1 && role === "Officer" && !props.useExactHeader) {
              return (
                <Column
                  key={`column-totalContent-${index}`}
                  field="totalContent"
                  header="Total Content"
                  body={totalContentBodyTemplate}
                  style={style}
                />
              );
            }
            if (index === props.headers.length - 1 && role !== "Officer" && !props.useExactHeader) {
              return (
                <Column
                  key={`column-status-${index}`}
                  field="status"
                  header="Status"
                  body={statusBodyTemplate}
                  style={style}
                />
              );
            }
            return (
              <Column
                key={`column-${header.field}-${index}`}
                // key={header.field}
                {...header}
                style={style}
              />
            );
          })}
        </DataTable>
      )}
    </>
  );
}

Table.defaultProps = {
  values: [],
  headers: [],
  loading: false,
};
