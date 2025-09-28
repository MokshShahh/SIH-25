import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';

import Header from './components/pages/Header';
import Dashboard from './components/pages/Dashboard';
import SignIn from "./components/pages/SignIn";
import SignUp from "./components/pages/SignUp";
import MumbaiLocal from "./components/pages/MumbaiLocal";

function App() {
  return (
    <Router>
      <Routes>
        <Route path='/' element={<Header />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/signin" element={<SignIn />} />
        <Route path="/signup" element={<SignUp />} />
        <Route path="/mumbai-local" element={<MumbaiLocal />} />
      </Routes>
    </Router>
  );
}

export default App;