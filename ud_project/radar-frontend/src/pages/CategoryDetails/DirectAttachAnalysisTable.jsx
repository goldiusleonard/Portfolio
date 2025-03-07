import { ArrowRight } from "../../assets/icons"
import { useState } from "react";
import { useNavigate } from "react-router-dom";

const DirectAttachAnalysisTable = ({isSelectable = false, isUpload = false, isEmpty = false, columns, data, openDialog}) => {

    console.log('data', data);
    

    // State for managing checkboxes
    const [selectAll, setSelectAll] = useState(false);
    const [checkedItems, setCheckedItems] = useState(Array.isArray(data) ? data.map(() => false) : []);

    const navigate = useNavigate();

    // Handle header checkbox click
    const handleSelectAll = () => {
        const newSelectAll = !selectAll;
        setSelectAll(newSelectAll);
        setCheckedItems(data?.map(() => newSelectAll));
    };

    // Handle individual checkbox click
    const handleCheckboxChange = (index) => {
        const updatedCheckedItems = [...checkedItems];
        updatedCheckedItems[index] = !updatedCheckedItems[index];
        setCheckedItems(updatedCheckedItems);

        // Update the "Select All" state
        setSelectAll(updatedCheckedItems.every((checked) => checked));
    };


    return (
        <div className="direct-attach-analysis-table">
            <table>
    <thead>
        <tr>
            {isSelectable && (
                <th>
                    <input
                        type="checkbox"
                        checked={selectAll}
                        onChange={handleSelectAll}
                    />
                </th>
            )}
            {columns.map(column => (
                <th key={column}>{column}</th>
            ))}
        </tr>
    </thead>
    <tbody style={{display: isEmpty ? 'none' : 'table-row-group'}}>
        {data?.length ? (
            data?.map((item, index) => {
                if (isUpload) {
                    return (
                        <tr onClick={() => navigate('/category-details/content-details')} key={item.id || index}>
                            <td className="table-img-content">
                                <>
                                    <img src={item.content.thumbnail} alt="img" />
                                    <div>
                                        <p>{item.id}</p>
                                        <a
                                            href={item.content.link}
                                            target="_blank"
                                            rel="noreferrer"
                                            className="social-link"
                                        >
                                            {item.content.link}
                                        </a>
                                    </div>
                                </>
                            </td>
                            <td>{item.date}</td>
                            <td>{item.social_media}</td>
                            <td><p className={`risk ${item.risk.toLowerCase()}`}>{item.risk}</p></td>
                        </tr>
                    );
                }
                return (
                    <tr onClick={openDialog} key={item.id || index}>
                        {isSelectable && (
                            <td>
                                <input
                                    type="checkbox"
                                    checked={checkedItems[index]}
                                    onChange={() => handleCheckboxChange(index)}
                                />
                            </td>
                        )}
                        <td>
                            <p className="highlighted">{item.id}</p>
                        </td>
                        <td>
                            <p>{item.date}</p>
                        </td>
                        <td>
                            <p>{item.socialMedia}</p>
                        </td>
                        <td>
                            <p className="highlighted">{item.topic}</p>
                        </td>
                        <td>
                            <p className="highlighted">{item.status}</p>
                        </td>
                        <td>
                            <div className="d-flex align-items-center">
                                <p className={`risk ${item.risk}`}>{item.risk}</p>
                            </div>
                        </td>
                    </tr>
                );
            })
        ) : (
            <tr>
                <td colSpan={columns.length + (isSelectable ? 1 : 0)}>No data available</td>
            </tr>
        )}
    </tbody>
</table>

        </div>
    )
}

export default DirectAttachAnalysisTable;