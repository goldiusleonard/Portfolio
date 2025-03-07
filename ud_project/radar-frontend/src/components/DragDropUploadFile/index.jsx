// src/DragAndDropUpload.js
import React, { useState, useRef } from "react";
import { UploadIcon } from "../../assets/icons";

const DragAndDropUpload = ({ file, setFile }) => {
  const [dragging, setDragging] = useState(false);
  const dropRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragging(true);
  };

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragging(false);
    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      setFile(files[0]);
    }
  };

  const handleFileSelect = (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      setFile(files[0]);
    }
  };

  return (
    <div
      ref={dropRef}
      className={`drop-zone ${
        dragging ? "dragging" : ""
      } wrapper-upload-drag-drop d-flex flex-row justify-content-center align-items-center gap-3`}
      onDragOver={handleDragOver}
      onDragEnter={handleDragEnter}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <input type="file" className="file-input" onChange={handleFileSelect} />
      {file ? (
        <p>File: {file.name}</p>
      ) : (
        <>
          <UploadIcon fill={"#666666"} />
          Click or Drag & drop your law document here.
        </>
      )}
    </div>
  );
};

export default DragAndDropUpload;
