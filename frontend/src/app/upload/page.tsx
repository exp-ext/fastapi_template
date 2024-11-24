'use client';

import ImageUploader from '../../components/ImageUploader';
import { useAuth } from '../../context/AuthContext';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

const UploadPage: React.FC = () => {
  const { token } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!token) {
      router.push('/login');
    }
  }, [token, router]);

  if (!token) {
    return <div>Загрузка...</div>;
  }

  return <ImageUploader token={token} />;
};

export default UploadPage;
