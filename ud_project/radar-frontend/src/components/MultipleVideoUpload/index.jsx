import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';

const MultipleVideoUpload = () => {
  const [videos, setVideos] = useState([]);

  const onDrop = useCallback((acceptedFiles) => {
    setVideos((prevVideos) => [...prevVideos, ...acceptedFiles]);
  }, []);

  const removeVideo = (index) => {
    setVideos((prevVideos) => prevVideos.filter((_, i) => i !== index));
  };

  const uploadVideos = async () => {
    const formData = new FormData();
    videos.forEach((video, index) => {
      formData.append(`video_${index}`, video);
    });
    console.log('Videos uploaded successfully', videos);
    // try {
    //   const response = await fetch('/upload', {
    //     method: 'POST',
    //     body: formData,
    //   });
    //   if (response.ok) {
    //     console.log('Videos uploaded successfully');
    //   } else {
    //     console.error('Failed to upload videos');
    //   }
    // } catch (error) {
    //   console.error('Error uploading videos:', error);
    // }
  };

  const { getRootProps, getInputProps } = useDropzone({
    accept: 'video/*',
    onDrop,
  });

  return (
    <div>
      <div {...getRootProps({ className: 'dropzone' })}>
        <input {...getInputProps()} />
        <p>Drag & drop some videos here, or click to select videos</p>
      </div>
      <div className="video-previews">
        {videos.map((video, index) => (
          <div key={index} className="video-preview">
            <video width="200" controls>
              <source src={URL.createObjectURL(video)} type={video.type} />
              Your browser does not support the video tag.
            </video>
            <button onClick={() => removeVideo(index)}>Remove</button>
          </div>
        ))}
      </div>
      <button onClick={uploadVideos}>Upload Videos</button>
    </div>
  );
};

export default MultipleVideoUpload;
