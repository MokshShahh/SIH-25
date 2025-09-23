import React from 'react';

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
}

function ProfileModal({ isOpen, onClose }: ProfileModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-70" onClick={onClose}>
      <div className="bg-gray-800 text-gray-200 rounded-lg shadow-xl w-full max-w-md p-6 relative" onClick={e => e.stopPropagation()}>
        <button className="absolute top-4 right-4 text-gray-400 hover:text-white text-2xl" onClick={onClose}>&times;</button>
        <h2 className="text-2xl font-bold mb-4 text-white">User Profile</h2>
        <div className="space-y-3">
          <p className="border-b border-gray-700 pb-3"><strong className="text-green-400">Name:</strong> Alex Doe</p>
          <p className="border-b border-gray-700 pb-3"><strong className="text-green-400">User ID:</strong> AD_0451</p>
          <p className="border-b border-gray-700 pb-3"><strong className="text-green-400">Role:</strong> System Operator</p>
          <p className="border-b border-gray-700 pb-3"><strong className="text-green-400">Access Level:</strong> Admin</p>
          <p><strong className="text-green-400">Last Login:</strong> 23 Sept 2025, 11:30 PM</p>
        </div>
      </div>
    </div>
  );
}

export default ProfileModal;