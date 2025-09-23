import AnimatedText from "./HoverAnimation";
import { NavLink } from "react-router-dom";

function Navbar() {
  return (
    <div className="flex justify-between items-center h-14 px-6 shadow-lg ">
      {/* Logo */}
      <div className="font-bold text-lg tracking-wide cursor-pointer hover:scale-105 transition-transform">
        LOGO
      </div>

      {/* Nav Links */}
      <div>
        <ul className="flex gap-8 font-medium">
          <li className="cursor-pointer  transition-colors"><NavLink to="/" className={(e)=> {return e.isActive? "bg-green-500 text-white p-1.5 rounded-2xl": undefined}} ><AnimatedText>Home</AnimatedText> </NavLink> </li>
          <li className="cursor-pointer  transition-colors"><NavLink to="/AboutUs" className={(e)=> {return e.isActive? "bg-green-500 text-white p-1.5 rounded-2xl": undefined}} ><AnimatedText>About Us</AnimatedText> </NavLink></li>
          <li className="cursor-pointer  transition-colors"><NavLink to="/dashboard" className={(e)=> {return e.isActive? "bg-green-500 text-white p-1.5 rounded-2xl": undefined}} ><AnimatedText>Dashboard</AnimatedText> </NavLink></li>
        </ul>
      </div>

      {/* Buttons */}
      <div className="flex gap-3">
        <button className="px-4 py-1.5 rounded-lg bg-green-400 border-green-700  text-gray-900 hover:border-green-400 hover:bg-green-700 hover:text-white font-semibold shadow  transition-colors">
          Profile
        </button>
        <button className="px-4 py-1.5 rounded-lg bg-white  text-gray-900 font-semibold shadow  hover:bg-gray-200 transition-colors">
          Dark Mode
        </button>
      </div>
    </div>
  );
}

export default Navbar;
