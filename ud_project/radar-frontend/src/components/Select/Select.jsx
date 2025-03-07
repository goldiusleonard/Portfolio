import React, { useState, useEffect, useRef } from "react";
import "./Select.scss";
import { DownArrowIcon, UpArrowIcon } from "../../assets/icons";

const Select = ({ options, defaultValue, onChange, className, arrowSize, placeholder, disabled }) => {
    const [selectedOption, setSelectedOption] = useState(defaultValue);
    const [isOpen, setIsOpen] = useState(false);
    const selectRef = useRef(null);

    const handleOptionClick = (option) => {
      setSelectedOption(option);
      setIsOpen(false);

      if (onChange) {
        onChange(option);
      }
    };


    const handleSelectClick = () => {
        if (!disabled) {
            setIsOpen(!isOpen);
        }
    };

    const closeAllSelects = (event) => {
        if (selectRef.current && !selectRef.current.contains(event.target)) {
            setIsOpen(false);
        }
    };

    useEffect(() => {
        document.addEventListener("mousedown", closeAllSelects);

        return () => {
            document.removeEventListener("mousedown", closeAllSelects);
        };
    }, []);

    return (
      <div
        className={`custom-select ${className} ${disabled ? "disabled" : ""}`}
        ref={selectRef}
      >
        <div
          className={
            selectedOption ? "select-selected" : "select-selected as-selected"
          }
          onClick={handleSelectClick}
          style={{ opacity: disabled ? 0.5 : 1 }}
        >
          <span className="text-truncate">
            {" "}
            {selectedOption ? selectedOption : placeholder}{" "}
          </span>
          {isOpen ? (
            <UpArrowIcon size={arrowSize} fill="#fff" />
          ) : (
            <DownArrowIcon size={arrowSize} fill="#fff" />
          )}
        </div>
        {isOpen && (
          <div className="select-items">
            {options.map((option, index) => (
              <div
                key={index}
                className={option === selectedOption ? "same-as-selected" : ""}
                onClick={() => handleOptionClick(option)}
              >
                {option}
              </div>
            ))}
          </div>
        )}
      </div>
    );
};

export default Select;
