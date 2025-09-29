import React, { useState, useEffect } from 'react';
import { NavLink, Link } from 'react-router-dom';
import { Moon, Sun } from 'lucide-react';
import AnimatedText from "./HoverAnimation";

function Navbar() {
  const [isModalOpen, setModalOpen] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);

  // Check for saved dark mode preference on mount
  useEffect(() => {
    const savedMode = localStorage.getItem('darkMode') === 'true';
    setIsDarkMode(savedMode);
    if (savedMode) {
      document.documentElement.classList.add('dark');
    }
  }, []);

  // Toggle dark mode
  const toggleDarkMode = () => {
    const newMode = !isDarkMode;
    setIsDarkMode(newMode);
    localStorage.setItem('darkMode', String(newMode));
    
    if (newMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  return (
    <>
      <div className="flex justify-between items-center h-14 px-6 shadow-lg bg-gray-100 dark:bg-gray-800 dark:text-gray-200 transition-colors duration-300">
        <div className="font-bold text-lg tracking-wide cursor-pointer hover:scale-105 transition-transform">
          <Link to="/">LOGO</Link>
        </div>

        <div>
          <ul className="flex gap-8 font-medium">
            <li className="cursor-pointer transition-colors">
              <NavLink 
                to="/" 
                className={({ isActive }) => 
                  isActive ? "bg-green-500 text-white p-1.5 rounded-lg" : ""
                }
              >
                <AnimatedText>Home</AnimatedText>
              </NavLink>
            </li>
            <li className="cursor-pointer transition-colors">
              <NavLink 
                to="/about" 
                className={({ isActive }) => 
                  isActive ? "bg-green-500 text-white p-1.5 rounded-lg" : ""
                }
              >
                <AnimatedText>About Us</AnimatedText>
              </NavLink>
            </li>
            <li className="cursor-pointer transition-colors">
              <NavLink 
                to="/dashboard" 
                className={({ isActive }) => 
                  isActive ? "bg-green-500 text-white p-1.5 rounded-lg" : ""
                }
              >
                <AnimatedText>Dashboard</AnimatedText>
              </NavLink>
            </li>
            <li className="cursor-pointer transition-colors">
              <NavLink 
                to="/mumbai-local" 
                className={({ isActive }) => 
                  isActive ? "bg-green-500 text-white p-1.5 rounded-lg" : ""
                }
              >
                <AnimatedText>Mumbai Local</AnimatedText>
              </NavLink>
            </li>
          </ul>
        </div>

        <div className="flex items-center gap-4">
          <Link 
            to="/signin" 
            className="font-semibold text-gray-700 dark:text-gray-300 hover:text-green-500 dark:hover:text-green-400 transition-colors"
          >
            Sign In
          </Link>
          <Link 
            to="/signup" 
            className="px-4 py-1.5 rounded-lg bg-green-400 text-gray-900 font-semibold shadow hover:bg-green-500 transition-colors"
          >
            Sign Up
          </Link>

          <button 
            onClick={() => setModalOpen(true)}
            className="px-4 py-1.5 rounded-lg bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-200 font-semibold shadow hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          >
            Profile
          </button>
          
          <button 
            onClick={toggleDarkMode}
            className="px-4 py-1.5 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-200 font-semibold shadow hover:bg-gray-200 dark:hover:bg-black transition-colors flex items-center gap-2"
          >
            {isDarkMode ? (
              <>
                <Sun className="w-4 h-4" />
                Light
              </>
            ) : (
              <>
                <Moon className="w-4 h-4" />
                Dark
              </>
            )}
          </button>
        </div>
      </div>

      {/* <ProfileModal isOpen={isModalOpen} onClose={() => setModalOpen(false)} /> */}
    </>
  );
}

export default Navbar;