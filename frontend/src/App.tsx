import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';

import Header from './components/pages/Header';
import Dashboard from './components/pages/Dashboard';
import SignIn from "./components/pages/SignIn";
import SignUp from "./components/pages/SignUp";
function App() {
  return (
    <Router>
      <Routes>
        <Route path='/' element={<Header />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/signin" element={<SignIn />} />
        <Route path="/signup" element={<SignUp />} />
      </Routes>
    </Router>
  );
}

export default App;