import React from "react";

const ReloadIcon = ({ fill }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="24"
    height="24"
    viewBox="0 0 24 24"
    fill="none"
  >
    <path
      d="M4 10C4 5.6 7.6 2 12 2C16.4 2 20 5.6 20 10C20 14.4 16.4 18 12 18H4"
      stroke={fill}
      stroke-linecap="round"
      stroke-linejoin="round"
    />
    <path
      d="M8 22L4 18L8 14"
      stroke={fill}
      stroke-linecap="round"
      stroke-linejoin="round"
    />
  </svg>
);

export default ReloadIcon;
