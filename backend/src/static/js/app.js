new Vue({
  el: '#app',
  data() {
    return {
      username: '',
      password: '',
      token: localStorage.getItem('token') || null,
      inputImages: [],
      objectApp: 'users-account',
    };
  },
  computed: {
    isAuthenticated() {
      return !!this.token;
    },
  },
  methods: {
    async login() {
      const params = new URLSearchParams();
      params.append('username', this.username);
      params.append('password', this.password);

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
          this.token = data.access_token;
          localStorage.setItem('token', this.token);
        } else {
          console.error('Login failed:', response.statusText);
        }
      } catch (error) {
        console.error('Error during login:', error);
      }
    },
    onFileChange(event) {
      const files = event.target.files;

      for (const file of files) {
        if (file && file.type.startsWith('image/')) {
          const reader = new FileReader();
          reader.onload = (e) => {
            this.inputImages.push({
              front_key: this.generateUniqueId(),
              file_name: file.name,
              file: file,
              preview: e.target.result,
              uploaded: false,
              image_id: null,
              is_main: false,
            });
          };
          reader.readAsDataURL(file);
        }
      }
    },
    setAsMainImage(index) {
      this.inputImages.forEach((image, i) => {
        image.is_main = (i === index);
      });
    },
    async createProcess() {
      if (!this.token) {
        console.error('No token found. Please login first.');
        return;
      }

      for (let i = 0; i < this.inputImages.length; i++) {
        const image = this.inputImages[i];
        if (!image.uploaded) {
          const formData = new FormData();
          formData.append('file_name', image.file_name);
          formData.append('is_main', image.is_main);
          formData.append('front_key', image.front_key);

          const uploadUrl = `/${this.objectApp}/upload-url-image`;

          try {
            const response = await fetch(uploadUrl, {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${this.token}`,
              },
              body: formData,
            });

            if (response.ok) {
              const data = await response.json();
              image.image_id = data.image.image.id;
              const presignedUrl = data.image.url;

              const uploadResult = await this.uploadFile(image.file, presignedUrl);

              if (uploadResult) {
                this.changeFileStatus(image.front_key, image.image_id);
              }
            } else if (response.status === 401) {
              this.token = null;
              localStorage.removeItem('token');
              alert('Your session has expired. Please log in again.');
              window.location.reload();
            } else {
              console.error('Error uploading image:', response.statusText);
            }
          } catch (error) {
            console.error('Error in createProcess:', error);
          }
        }
      }
    },
    async uploadFile(file, presignedUrl) {
      try {
        const uploadResponse = await fetch(presignedUrl, {
          method: 'PUT',
          body: file,
        });

        return uploadResponse.ok;
      } catch (error) {
        console.error('Error in uploadFile:', error);
        return false;
      }
    },
    async changeFileStatus(front_key, image_id) {
      const image = this.inputImages.find(image => image.front_key === front_key);
      if (image) {
        image.uploaded = true;

        try {
          const response = await fetch('/media/images/treatment/', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${this.token}`,
              'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
              image_id: image_id.toString(),
            }),
          });

          if (response.ok) {
            console.log('Image treatment initiated successfully.');
          } else if (response.status === 401) {
            this.token = null;
            localStorage.removeItem('token');
            alert('Your session has expired. Please log in again.');
            window.location.reload();
          } else {
            console.error('Image treatment failed:', response.statusText);
          }
        } catch (error) {
          console.error('Error in changeFileStatus:', error);
        }
      }
    },
    generateUniqueId() {
      return Math.random().toString(36).substring(2, 11);
    },
  },
});