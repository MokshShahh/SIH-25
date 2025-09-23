import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';

import './App.css'

import Header from './components/pages/Header'
import Dashboard from './components/pages/Dashboard';

function AppContent(){
  const loaction = useLocation();
  return (
    <>
      <Routes>
        <Route path='/' element={<Header />}/> 
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </>
  )  
}

function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  )
}

export default App
