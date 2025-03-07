import React, { useEffect, useMemo, useRef, useState } from "react";
import CustomModal from "../custom-modal/CustomModal";
import { CloseIcon, UploadIcon } from "../../assets/icons";
import DragAndDropUpload from "../DragDropUploadFile";
import Select from "../Select/Select";
import Button from "../button/Button";
import SingleDatePicker from "../DatePicker/SingleDatePicker";

const optionsCategory = [
    "Criminal Law",
    "Data Protection Law",
    "Corporate Law",
    "Labor Law",
    "Financial Law",
    "Environmental Law",
];

const LawViolationUploadModal = ({
    isShowModal,
    handleCloseModal,
    categories,
    isEdit,
    editData,
    isLoading,
    onSubmit = (payload) => { },
    onDelete = () => { },
}) => {
    const [file, setFile] = useState(null);
    const [statusSubmit, setStatusStatusSubmit] = useState(0);
    const [formLawViolation, setFormLawViolation] = useState({
        lawName: "",
        lawCategory: "",
        lawEffectiveDate: new Date(),
        lawUploadDate: new Date(),
        lawPublisher: "",
        lawSummary: "",
    });

    const fileInputRef = useRef(null);

    useEffect(() => {
        if (isShowModal) {
            handleClearFile()
        }
    }, [isShowModal])

    const handleChange = (event, fieldId) => {
        const fieldValue =
            fieldId === "lawCategory" ||
                fieldId === "lawEffectiveDate" ||
                fieldId === "lawUploadDate"
                ? event
                : event.target.value;

        // Create a new object with the updated field value
        const newValues = {
            ...formLawViolation,
            [fieldId]: fieldValue,
        };

        // Update the state with the new object
        setFormLawViolation(newValues);
    };

    const handleSelectFile = (event) => {
        const file = event.target.files[0];
        setFile(file);
    };

    const handleClick = () => {
        fileInputRef.current.click();
    };

    const handleClearFile = () => {
        if (fileInputRef.current?.value) {
            fileInputRef.current.value = null;
        }
        setFile(null);
        setStatusStatusSubmit(0);
    };

    const isValidForm = useMemo(() => {
        if (
            formLawViolation.lawName === "" &&
            formLawViolation.lawCategory === "" &&
            formLawViolation.lawCategory === "" &&
            formLawViolation.lawPublisher === ""
        ) {
            return false;
        }
        return true;
    }, [formLawViolation]);

    const handleButtonSubmit = (event) => {
        if (file?.name && statusSubmit === 0) {
            setStatusStatusSubmit(1);
            // Send the file to the server
        } else if (file?.name && statusSubmit === 1) {
            if (isValidForm) {
                // Send form data to the server
                onSubmit({
                    file,
                    ...formLawViolation
                });
            }
        }
    };

    const handleCloseModalUpload = () => {
        handleCloseModal();
        handleClearFile();
    };

    const titleContent = (
        <div className="title-law-violation-modal d-flex align-items-center justify-content-between w-100">
            {isEdit ? "Law Reference" : "Upload New Law Reference"}
            <CloseIcon onClick={handleCloseModalUpload} fill="#80EED3" />
        </div>
    );

    useEffect(() => {
        if (isEdit) {
            const mappingEditData = {
                lawName: editData.name,
                lawCategory: editData.category,
                lawEffectiveDate: new Date(editData.effective_date),
                lawUploadDate: new Date(editData.upload_date),
                lawPublisher: editData.publisher,
                lawSummary: editData.summary,
            };
            setFormLawViolation(mappingEditData);
        }
    }, [isEdit, editData]);

    const FormLawViolation = () => {
        return (
            <div className="form-law-violation d-flex gap-3 flex-column">
                <div className="form-law-violation-item d-flex flex-row gap-3 align-items-center">
                    <label
                        className="form-law-violation-item-label col-3 text-start"
                        htmlFor="label-law-name"
                    >
                        Law Name
                    </label>
                    <div className="d-flex flex-column w-100 align-items-start gap-2">
                        <input
                            onChange={(event) => {
                                handleChange(event, "lawName");
                            }}
                            className={`field-input-text ${formLawViolation.lawName === "" &&
                                "invalid-field"
                                }`}
                            type="text"
                            value={formLawViolation.lawName}
                            placeholder="Type the official name or title of the law"
                        />
                        {formLawViolation.lawName === "" && (
                            <span className="error-text">
                                Law Name cannot be empty
                            </span>
                        )}
                    </div>
                </div>
                <div className="form-law-violation-item d-flex flex-row gap-3 align-items-center">
                    <label
                        className="form-law-violation-item-label col-3 text-start"
                        htmlFor="label-category"
                    >
                        Category
                    </label>
                    <div className="d-flex flex-column w-100 align-items-start gap-2">
                        <Select
                            className={
                                formLawViolation.lawCategory === "" ?
                                    "invalid-field" : "law-violation-select-text"
                            }
                            options={categories}
                            onChange={(value) =>
                                handleChange(value, "lawCategory")
                            }
                            placeholder={"Choose list of category law"}
                            defaultValue={
                                isEdit
                                    ? categories.find(
                                        (v) => v === editData.category
                                    )
                                    : ""
                            }
                        />
                        {formLawViolation.lawCategory === "" && (
                            <span className="error-text">
                                Category cannot be empty
                            </span>
                        )}
                    </div>
                </div>
                <div className="form-law-violation-item d-flex flex-row gap-3 align-items-center">
                    <label
                        className="form-law-violation-item-label col-3 text-start"
                        htmlFor="label-category"
                    >
                        Effective Date
                    </label>
                    <div className="d-flex flex-column w-100 align-items-start gap-2">
                        <SingleDatePicker
                            classname={`field-input-text ${formLawViolation.lawEffectiveDate === "" &&
                                "invalid-field"
                                } `}
                            handleChangeValue={(event) =>
                                handleChange(event, "lawEffectiveDate")
                            }
                            valueDate={formLawViolation.lawEffectiveDate}
                        />
                        {formLawViolation.lawEffectiveDate === "" && (
                            <span className="error-text">
                                Effective Date cannot be empty
                            </span>
                        )}
                    </div>
                </div>
                {isEdit && (
                    <div className="form-law-violation-item d-flex flex-row gap-3 align-items-center">
                        <label
                            className="form-law-violation-item-label col-3 text-start"
                            htmlFor="label-category"
                        >
                            Uploaded Date
                        </label>
                        <SingleDatePicker
                            classname={`field-input-text ${!isEdit && formLawViolation.lawUploadDate === "" &&
                                "invalid-field"
                                } `}
                            handleChangeValue={(event) =>
                                handleChange(event, "lawUploadDate")
                            }
                            valueDate={isEdit ? editData.upload_date : formLawViolation.lawUploadDate}
                        />
                    </div>
                )}
                <div className="form-law-violation-item d-flex flex-row gap-3 align-items-center">
                    <label
                        className="form-law-violation-item-label col-3 text-start"
                        htmlFor="label-category"
                    >
                        Publisher
                    </label>
                    <div className="d-flex flex-column w-100 align-items-start gap-2">
                        <input
                            className={`field-input-text ${formLawViolation.lawPublisher === "" &&
                                "invalid-field"
                                }`}
                            type="text"
                            placeholder="Type the official source or publisher of the law"
                            onChange={(value) =>
                                handleChange(value, "lawPublisher")
                            }
                            value={formLawViolation.lawPublisher}
                        />
                        {formLawViolation.lawPublisher === "" && (
                            <span className="error-text">
                                Publisher cannot be empty
                            </span>
                        )}
                    </div>
                </div>
                <div className="form-law-violation-item d-flex flex-row gap-3">
                    <label
                        className="form-law-violation-item-label col-3 text-start"
                        htmlFor="label-category"
                    >
                        Summary (Optional)
                    </label>
                    <textarea
                        className="field-textarea"
                        type="text"
                        rows={4}
                        placeholder="Type a short summary of the law's content or purpose"
                        value={formLawViolation.lawSummary}
                        onChange={(value) =>
                            handleChange(value, "lawSummary")
                        }
                    />
                </div>
            </div>
        );
    };

    const contentModal = (
        <div className="law-violation-modal-wrapper d-flex gap-3 flex-column">
            <div className="d-flex gap-3 align-items-center">
                <label className="label-upload-file col-3">Upload Law</label>
                <div className="field-input-text">
                    {isEdit ? editData.file_name : file ? file?.name : "Please upload your law document here"}
                    {file?.name && (
                        <div className="btn-remove-file">
                            <CloseIcon onClick={handleClearFile} fill="#fff" />
                        </div>
                    )}
                </div>
                <input
                    ref={fileInputRef}
                    type="file"
                    className="file-upload-file"
                    onChange={handleSelectFile}
                />
                {!file?.name && !isEdit && (
                    <Button
                        onClick={handleClick}
                        className="outline col-3"
                        text={
                            <div className="d-flex align-items-center gap-3">
                                <UploadIcon fill="#fff" />
                                Upload New
                            </div>
                        }
                    />
                )}
            </div>
            {(file?.name && statusSubmit === 1) || isEdit ? (
                FormLawViolation()
            ) : (
                <DragAndDropUpload file={file} setFile={setFile} />
            )}
            <div className="wrapper-footer-modal d-flex justify-content-between mt-3">
                <Button
                    onClick={handleCloseModalUpload}
                    className="btn-cancel-modal-upload-law text-white bg-transparent justify-content-center align-items-center px-5"
                    text={"Cancel"}
                    disable={isLoading}
                />
                {isEdit ? (
                    <div className="btn-edit-modal-law-violoation-wrapper ">
                        <Button
                            className="btn-submit-modal-upload-law bg-white justify-content-center align-items-center px-5 btn-delete"
                            text={"Delete Law"}
                            onClick={onDelete}
                            disable={isLoading}
                        />

                        <Button
                            className="btn-submit-modal-upload-law bg-white justify-content-center align-items-center px-5"
                            text={"Save Changes"}
                            onClick={(_) => onSubmit(formLawViolation)}
                            disable={isLoading}
                        />
                    </div>
                ) : (
                    <Button
                        className="btn-submit-modal-upload-law bg-white justify-content-center align-items-center px-5"
                        text={"Submit"}
                        onClick={handleButtonSubmit}
                        disable={isLoading}
                    />
                )}
            </div>
        </div>
    );

    return (
        <CustomModal
            isOpen={isShowModal}
            className="law-violation-modal"
            size={"xl"}
            title={titleContent}
            subTitle={
                "Provide the details of the law to make it accessible as a reference."
            }
            content={contentModal}
        />
    );
};

export default LawViolationUploadModal;
