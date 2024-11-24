'use client';

import '../styles/globals.css';
import { AuthProvider } from '../context/AuthContext';
import Header from '../components/Header';
import Footer from '../components/Footer';
import ChatPopup from '../components/ChatPopup';

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <Header />
          {children}
          <ChatPopup />
          <Footer />
        </AuthProvider>
      </body>
    </html>
  );
}
