import React, { useState } from 'react';
import uploadIcon from '../../assets/icons/upload.svg'
import { CloseIcon } from '../../assets/icons';

const UploadVideos = () => {
    const [videos, setVideos] = useState([]);

    // const handleFileChange = (event) => {
    //     const files = Array.from(event.target.files);
    //     setVideos((prevVideos) => [...prevVideos, ...files]);
    // };

    const handleFileChange = (event) => {
        const files = Array.from(event.target.files);
        setVideos((prevVideos) => {
          const newVideos = [];
          files.forEach((file) => {
            if (!prevVideos.some((video) => video.name === file.name)) {
              newVideos.push(file);
            }
          });
          return [...prevVideos, ...newVideos];
        });
      };

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

    return (
        <div className='upload-wrapper p-3'>
            <h2 className='title-type-3 mb-2'>Generate by Video Upload</h2>
            <div className="upload-area">
                <label className="custom-file-upload" htmlFor='multi_upload_input'>
                    <input type="file" multiple onChange={handleFileChange} id='multi_upload_input' />
                    <img src={uploadIcon} alt='Upload Icon' className='mb-1'/>
                    Upload
                    <span className='mb-1'>Upload videos or docs (MP4, AVI, PDF, etc.) up to 50 MB</span>
                </label>
                {videos.length > 0 ?
                    <div className="video-previews ps-4">
                        {videos.map((video, index) => (
                            <div key={index} className="video-preview d-flex">
                                <div className='video-tag'> 
                                    V{index+1}
                                </div>
                                <div className='d-flex select-video-item'>
                                    <span>{video.name}</span>
                                    <div onClick={() => removeVideo(index)}>
                                        <CloseIcon fill="#fff" />
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                    :
                    <div className='text-center no-video'>
                        <span>Upload to Generate the Parameter</span>
                    </div>
                }
                {/* <button className='btn-handle-upload' onClick={uploadVideos}>Upload Videos</button> */}
            </div>

        </div>
    );
};

export default UploadVideos;
