import React, { useState, useEffect, useRef } from "react";
import { DownArrowIcon, UpArrowIcon } from "../../assets/icons";

const CustomSelect = ({
    options: initialOptions,
    defaultValue,
    onChange,
    className,
    arrowSize,
    placeholder,
    addInputPlaceholder,
    disabled,
}) => {
    const [options, setOptions] = useState(initialOptions);
    const [selectedOption, setSelectedOption] = useState(defaultValue);
    const [isOpen, setIsOpen] = useState(false);
    const [customOption, setCustomOption] = useState("");
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

    const handleAddCustomOption = () => {
        if (customOption && !options.includes(customOption)) {
            setOptions((prevOptions) => [...prevOptions, customOption]);
            setSelectedOption(customOption);
            setCustomOption("");
            setIsOpen(false);

            if (onChange) {
                onChange(customOption);
            }
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
                {selectedOption ? selectedOption : placeholder}
                {isOpen ? (
                    <UpArrowIcon size={arrowSize} fill="#fff" />
                ) : (
                    <DownArrowIcon size={arrowSize} fill="#fff" />
                )}
            </div>
            {isOpen && (
                <div className="select-items">
                    <div className="custom-option-input">
                        <input
                            type="text"
                            value={customOption}
                            onChange={(e) => setCustomOption(e.target.value)}
                            placeholder={addInputPlaceholder}
                        />
                        <button onClick={handleAddCustomOption}>+</button>
                    </div>
                    {options.map((option, index) => (
                        <div
                            key={index}
                            className={
                                option === selectedOption ? "same-as-selected" : ""
                            }
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

export default CustomSelect;
