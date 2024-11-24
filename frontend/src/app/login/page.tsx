'use client';

import Login from '../../components/Login';
import { useAuth } from '../../context/AuthContext';
import { useRouter } from 'next/navigation';

const LoginPage: React.FC = () => {
  const { setToken } = useAuth();
  const router = useRouter();

  const handleLoginSuccess = (token: string) => {
    setToken(token);
    localStorage.setItem('token', token);
    router.push('/upload');
  };

  return <Login onLoginSuccess={handleLoginSuccess} />;
};

export default LoginPage;
