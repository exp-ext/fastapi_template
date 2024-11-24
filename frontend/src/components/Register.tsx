'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import '../styles/Register.css';
import config from '../config';

const Register: React.FC = () => {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const router = useRouter();

  const register = async () => {
    if (password !== confirmPassword) {
      alert('Пароли не совпадают');
      return;
    }
    try {
      const response = await fetch(`${config.API_BASE_URL}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          first_name: firstName,
          last_name: lastName,
          email: email,
          password: password,
        }),
      });

      if (response.ok) {
        router.push('/login');
      } else {
        const errorData = await response.json();
        console.error(
          'Registration failed:',
          errorData.message || response.statusText
        );
        alert(
          `Ошибка регистрации: ${errorData.message || 'Неизвестная ошибка'}`
        );
      }
    } catch (error) {
      console.error('Error during registration:', error);
      alert('Произошла ошибка во время регистрации. Попробуйте позже.');
    }
  };

  return (
    <div className="register-container">
      <h2 className="register-title">Register</h2>
      <input
        className="register-input"
        type="text"
        placeholder="First Name"
        value={firstName}
        onChange={(e) => setFirstName(e.target.value)}
      />
      <input
        className="register-input"
        type="text"
        placeholder="Last Name"
        value={lastName}
        onChange={(e) => setLastName(e.target.value)}
      />
      <input
        className="register-input"
        type="email"
        placeholder="Email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
      />
      <input
        className="register-input"
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <input
        className="register-input"
        type="password"
        placeholder="Confirm Password"
        value={confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
      />
      <button className="register-button" onClick={register}>
        Register
      </button>
    </div>
  );
};

export default Register;
