import React from 'react';
import { useAuth } from '../context/AuthContext';

const Account = () => {
  const { user } = useAuth();

  return (
    <div className="container py-5">
      <h1>My Account</h1>
      <p>Welcome, {user?.name || user?.email}!</p>
      <p>Account management features will be here.</p>
    </div>
  );
};

export default Account;