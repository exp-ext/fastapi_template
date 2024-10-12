import React from 'react';
import { Link } from 'react-router-dom';
import './Header.css';

const Header = ({ token, handleLogout }) => {
  return (
    <header className="header">
      <h1>Image Upload App</h1>
      <nav>
        <ul>
          {token ? (
            <>
              <li>
                <Link to="/upload">Загрузить изображения</Link>
              </li>
              <li>
                <button onClick={handleLogout}>Выйти</button>
              </li>
            </>
          ) : (
            <>
              <li>
                <Link to="/login">Вход</Link>
              </li>
              <li>
                <Link to="/register">Регистрация</Link>
              </li>
            </>
          )}
        </ul>
      </nav>
    </header>
  );
};

export default Header;
