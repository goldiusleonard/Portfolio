import React, { forwardRef, useEffect, useState } from "react";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { DownArrowIcon } from "../../assets/icons";
import moment from "moment";

const SingleDatePicker = ({ classname, valueDate, handleChangeValue }) => {
    const [selectedDate, setselectedDate] = useState();

    const handleStartDateChange = (date) => {
        handleChangeValue(date);
        setselectedDate(date);
    };

    const CustomInput = forwardRef(({ value, onClick, className }, ref) => (
        <div
            className={`d-flex justify-content-beetwen ${className}`}
            onClick={onClick}
            ref={ref}
        >
            <span>{moment(value).format("D-MMM-YYYY")}</span>
            <DownArrowIcon size={10} fill="#fff" />
        </div>
    ));

    useEffect(() => {
        setselectedDate(valueDate);
    }, [valueDate]);

    return (
        <DatePicker
            selected={selectedDate}
            selectsStart
            onChange={handleStartDateChange}
            customInput={<CustomInput className={classname} />}
        />
    );
};

export default SingleDatePicker;
