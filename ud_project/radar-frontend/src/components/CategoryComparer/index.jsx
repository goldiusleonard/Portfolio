import React, { useEffect, useState } from "react";
import {
  CloseIcon,
  PlusIcon,
  ReloadIcon,
  SwitchCatIcon,
} from "../../assets/icons";

const CategoryComparer = ({
  currentCategory,
  toggleModal,
  handleUpdateCategories,
}) => {
  const [animatedCategories, setAnimatedCategories] = useState([
    ...currentCategory,
  ]);
  const [isRotating, setIsRotating] = useState(null);

  useEffect(() => {
    setAnimatedCategories([...currentCategory]);
  }, [currentCategory]);
  const handleRemoveCategories = (category) => {
    const updatedCategories = animatedCategories.filter(
      (item) => item !== category
    );
    setAnimatedCategories(updatedCategories);
    handleUpdateCategories(updatedCategories);
  };

  const handleResetCategories = (category) => {
    const resetCategories = animatedCategories.filter(
      (item) => item === category
    );
    setAnimatedCategories(resetCategories);
    handleUpdateCategories(resetCategories);
  };

  const handleSwitchCategories = (index) => {
    setIsRotating(index);
    if (index < animatedCategories.length - 1) {
      const newCategories = [...animatedCategories];
      // Swap the positions
      [newCategories[index], newCategories[index + 1]] = [
        newCategories[index + 1],
        newCategories[index],
      ];
      setAnimatedCategories(newCategories);
      handleUpdateCategories(newCategories);
    }
    setTimeout(() => setIsRotating(null), 500);
  };

  return (
    <div className="ui-container">
      <button
        className="icon-button"
        onClick={() => {
          handleResetCategories(animatedCategories[0]);
        }}
      >
        <ReloadIcon fill="#FFFFFF" />
      </button>
      {animatedCategories &&
        animatedCategories.map((category, index) => (
          <React.Fragment key={category}>
            <div className="chip text-truncate category-animation">
              <span className="chip-text text-truncate">{category}</span>
              <button
                className="close-button"
                onClick={() => {
                  handleRemoveCategories(category);
                }}
              >
                <CloseIcon fill="#FFFFFF" />
              </button>
            </div>
            {index !== animatedCategories.length - 1 && (
              <div
                className={`switch icon-button ${
                  isRotating === index ? "rotate" : ""
                }`}
                onClick={() => handleSwitchCategories(index)}
                style={{ cursor: "pointer" }}
              >
                <SwitchCatIcon fill="#FFFFFF" />
              </div>
            )}
          </React.Fragment>
        ))}

      {animatedCategories && animatedCategories.length < 4 && (
        <button className="icon-button" onClick={toggleModal}>
          <PlusIcon fill="#FFFFFF" />
        </button>
      )}
    </div>
  );
};

export default CategoryComparer;
