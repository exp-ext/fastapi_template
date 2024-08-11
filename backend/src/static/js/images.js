$(document).ready(function () {
  const loginButton = $('#login-button');
  const uploadButton = $('#upload-button');
  const fileInput = $('#file-input');
  const imageGrid = $('#image-grid');

  let token = null;
  let inputImages = [];

  // События
  loginButton.on('click', login);
  fileInput.on('change', onFileChange);
  uploadButton.on('click', createProcess);

  async function login() {
    const username = $('#username').val();
    const password = $('#password').val();

    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);

    try {
      const response = await fetch('/auth/jwt/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Accept': 'application/json',
        },
        body: params.toString(),
      });

      if (response.ok) {
        const data = await response.json();
        token = data.access_token;
        $('#auth-section').hide();
        $('#add-image').show();
      } else {
        console.error('Login failed:', response.statusText);
      }
    } catch (error) {
      console.error('Error during login:', error);
    }
  }

  async function createProcess() {
    if (!token) {
      console.error('No token found. Please login first.');
      return;
    }

    const objectApp = uploadButton.data('app');
    const uploadUrl = `/${objectApp}/upload-url-image`;

    for (const image of inputImages) {
      if (!image.uploaded) {
        const formData = new FormData();
        formData.append('file_name', image.file_name);
        formData.append('is_main', image.is_main);
        formData.append('front_key', image.front_key);

        try {
          const response = await fetch(uploadUrl, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`, // Добавляем токен в заголовок
            },
            body: formData,
          });

          if (response.ok) {
            const data = await response.json();
            const presignedUrl = data.image.url;

            const uploadResult = await uploadFile(image.file, presignedUrl);

            if (uploadResult) {
              changeFileStatus(image.front_key);
            }
          } else {
            console.error('Error uploading image:', response.statusText);
          }
        } catch (error) {
          console.error('Error in createProcess:', error);
        }
      }
    }
  }

  async function uploadFile(file, presignedUrl) {
    try {
      const uploadResponse = await fetch(presignedUrl, {
        method: 'PUT',
        body: file,
      });

      if (uploadResponse.ok) {
        return true;
      }
    } catch (error) {
      console.error('Error in uploadFile:', error);
    }
    return false;
  }

  function onFileChange(e) {
    const files = e.target.files;

    for (const file of files) {
      if (file && file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (event) => {
          const img = $('<img>').attr('src', event.target.result).addClass('preview grid-item');
          imageGrid.append(img);
        };
        reader.readAsDataURL(file);

        inputImages.push({
          front_key: generateUniqueId(),
          file_name: file.name,
          file: file,
          is_main: false, // Установите это значение, если нужно
          uploaded: false,
        });
      }
    }
  }

  function changeFileStatus(front_key) {
    const image = inputImages.find(image => image.front_key === front_key);
    if (image) {
      image.uploaded = true;
    }
  }

  function generateUniqueId() {
    return Math.random().toString(36).substring(2, 11);
  }
});