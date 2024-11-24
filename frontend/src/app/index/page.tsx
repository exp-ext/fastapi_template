import { useEffect } from 'react';
import { useRouter } from 'next/router';

interface IndexPageProps {
  token: string | null;
}

const IndexPage: React.FC<IndexPageProps> = ({ token }) => {
  const router = useRouter();

  useEffect(() => {
    if (token) {
      router.replace('/upload');
    } else {
      router.replace('/login');
    }
  }, [token, router]);

  return null;
};

export default IndexPage;
