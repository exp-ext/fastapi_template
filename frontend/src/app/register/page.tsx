'use client';

import Register from '../../components/Register';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

interface RegisterPageProps {
  token: string | null;
}

const RegisterPage: React.FC<RegisterPageProps> = ({ token }) => {
  const router = useRouter();

  useEffect(() => {
    if (token) {
      router.replace('/upload');
    }
  }, [token, router]);

  return <Register />;
};

export default RegisterPage;
