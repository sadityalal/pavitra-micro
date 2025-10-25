import { createContext, useState, useContext } from 'react';

const AuthContext = createContext();

// This is likely what you have - a default export
const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);

  // Your auth logic here...

  return (
    <AuthContext.Provider value={{ user, setUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthProvider; // Default export