'use client';

import React from 'react';
import Link from 'next/link';
import { useAuth } from '../context/AuthContext';
import '../styles/Header.css';

const Header = () => {
  const { token, logout } = useAuth();

  return (
    <header className="header">
      <h1>Template</h1>
      <nav>
        <ul>
          {token ? (
            <>
              <li>
                <Link href="/upload">Загрузить изображения</Link>
              </li>
              <li>
                <button onClick={logout}>Выйти</button>
              </li>
            </>
          ) : (
            <>
              <li>
                <Link href="/login">Вход</Link>
              </li>
              <li>
                <Link href="/register">Регистрация</Link>
              </li>
            </>
          )}
        </ul>
      </nav>
    </header>
  );
};

export default Header;
