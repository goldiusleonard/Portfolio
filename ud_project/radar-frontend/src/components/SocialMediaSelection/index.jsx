import React, { useState } from "react";
import "./SocialMediaSelection.scss";

function SocialMediaSelection() {
  const [selectedPlatforms, setSelectedPlatforms] = useState({
    tiktok: false,
  });

  const handleCheckboxChange = (e) => {
    const { name, checked } = e.target;
    setSelectedPlatforms((prev) => ({
      ...prev,
      [name]: checked,
    }));
  };

  return (
    <div className="p-3 w-100">
      <div className="title-type-3 mb-2">Social Media Selection</div>
      <p className="social-media-description mb-2">
        You can only include content according to the social media you choose,
        otherwise the data will fail to crawl.
      </p>
      <div className="w-100">
        <form className="d-flex w-100">
          <div className="w-50">
            <div>
              <label className="d-flex align-items-center">
                <input
                  type="checkbox"
                //   className="ms-3"
                  name="tiktok"
                  checked={selectedPlatforms.tiktok}
                  onChange={handleCheckboxChange}
                />
                TikTok
              </label>
            </div>
            <div>
              <label className="d-flex align-items-center">
                <input
                  type="checkbox"
                  name="x"
                  disabled
                  checked={false}
                  onChange={() => {}}
                />
                X
              </label>
            </div>
          </div>
          <div className="w-50">
            <div>
              <label className="d-flex align-items-center">
                <input
                  type="checkbox"
                  name="facebook"
                  disabled
                  checked={false}
                  onChange={() => {}}
                />
                Facebook
              </label>
            </div>
            <div>
              <label className="d-flex align-items-center">
                <input
                  type="checkbox"
                  name="instagram"
                  disabled
                  checked={false}
                  onChange={() => {}}
                />
                Instagram
              </label>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}

export default SocialMediaSelection;
