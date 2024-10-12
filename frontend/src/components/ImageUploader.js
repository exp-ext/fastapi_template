import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import './ImageUploader.css';

const ImageUploader = ({ token }) => {
  const [inputImages, setInputImages] = useState([]);

  const { getRootProps, getInputProps } = useDropzone({
    accept: 'image/*',
    onDrop: (acceptedFiles) => {
      const newImages = acceptedFiles.map((file) => ({
        front_key: generateUniqueId(),
        file_name: file.name,
        file: file,
        preview: URL.createObjectURL(file),
        uploaded: false,
        image_id: null,
        is_main: false,
      }));
      setInputImages((prevImages) => [...prevImages, ...newImages]);
    },
  });

  const generateUniqueId = () => {
    return Math.random().toString(36).substring(2, 11);
  };

  const setAsMainImage = (index) => {
    setInputImages((prevImages) =>
      prevImages.map((image, i) => ({
        ...image,
        is_main: i === index,
      }))
    );
  };

  const uploadImages = async () => {
    if (!token) {
      console.error('No token found. Please login first.');
      return;
    }

    for (let i = 0; i < inputImages.length; i++) {
      const image = inputImages[i];
      if (!image.uploaded) {
        const formData = new FormData();
        formData.append('file_name', image.file_name);
        formData.append('is_main', image.is_main);
        formData.append('front_key', image.front_key);

        const uploadUrl = `/api/users-account/upload-url-image`;

        try {
          const response = await fetch(uploadUrl, {
            method: 'POST',
            headers: {
              Authorization: `Bearer ${token}`,
            },
            body: formData,
          });

          if (response.ok) {
            const data = await response.json();
            const presignedUrl = data.image.url;
            const uploadResult = await uploadFile(image.file, presignedUrl);

            if (uploadResult) {
              changeFileStatus(image.front_key, data.image.image.id);
            }
          } else {
            console.error('Error uploading image:', response.statusText);
          }
        } catch (error) {
          console.error('Error in uploadImages:', error);
        }
      }
    }
  };

  const uploadFile = async (file, presignedUrl) => {
    try {
      const response = await fetch(presignedUrl, {
        method: 'PUT',
        body: file,
      });
      return response.ok;
    } catch (error) {
      console.error('Error uploading file:', error);
      return false;
    }
  };

  const changeFileStatus = async (front_key, image_id) => {
    const image = inputImages.find((img) => img.front_key === front_key);
    if (image) {
      image.uploaded = true;
      try {
        const response = await fetch('/api/assets/images/treatment/', {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/x-www-form-urlencoded',
          },
          body: new URLSearchParams({ image_id: image_id.toString() }),
        });

        if (response.ok) {
          console.log('Image treatment initiated successfully.');
        } else {
          console.error('Image treatment failed:', response.statusText);
        }
      } catch (error) {
        console.error('Error changing file status:', error);
      }
    }
  };

  return (
    <div className="uploader-container">
      <div className="dropzone" {...getRootProps()}>
        <input {...getInputProps()} />
        <p>Перетащите сюда изображения или нажмите, чтобы выбрать файлы</p>
      </div>
      <div className="preview-container">
        {inputImages.map((image, index) => (
          <div key={image.front_key} className="image-preview">
            <img src={image.preview} alt={image.file_name} />
            <button
              className={`main-button ${image.is_main ? 'main-selected' : ''}`}
              onClick={() => setAsMainImage(index)}
            >
              {image.is_main ? 'Основное' : 'Сделать основным'}
            </button>
          </div>
        ))}
      </div>
      <button className="upload-button" onClick={uploadImages}>
        Загрузить изображения
      </button>
    </div>
  );
};

export default ImageUploader;
