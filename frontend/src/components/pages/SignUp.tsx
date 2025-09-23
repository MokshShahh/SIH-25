import React from 'react';
import { Link } from 'react-router-dom';

function SignUp() {
  return (
    <div className="flex justify-center items-center min-h-screen bg-gray-900 text-gray-200">
      <form className="bg-gray-800 p-10 rounded-lg shadow-xl w-full max-w-sm">
        <h2 className="text-3xl font-bold mb-2 text-white text-center">Create Account</h2>
        <p className="text-gray-400 mb-6 text-center">Join the system and get started.</p>
        <div className="mb-4">
          <label htmlFor="username" className="block mb-2 text-sm font-medium text-gray-400">Username</label>
          <input type="text" id="username" name="username" required 
                 className="w-full p-2.5 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-green-500 focus:border-green-500"/>
        </div>
        <div className="mb-4">
          <label htmlFor="email" className="block mb-2 text-sm font-medium text-gray-400">Email</label>
          <input type="email" id="email" name="email" required 
                 className="w-full p-2.5 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-green-500 focus:border-green-500"/>
        </div>
        <div className="mb-6">
          <label htmlFor="password" className="block mb-2 text-sm font-medium text-gray-400">Password</label>
          <input type="password" id="password" name="password" required 
                 className="w-full p-2.5 bg-gray-700 border border-gray-600 rounded-lg text-white focus:ring-green-500 focus:border-green-500"/>
        </div>
        <button type="submit" 
                className="w-full py-2.5 rounded-lg bg-green-500 hover:bg-green-600 text-white font-bold transition-colors">
          Sign Up
        </button>
        <div className="mt-6 text-center text-sm">
          <p className="text-gray-400">Already have an account? <Link to="/signin" className="text-green-400 hover:underline">Sign In</Link></p>
        </div>
      </form>
    </div>
  );
}

export default SignUp;