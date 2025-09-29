import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Header from './components/pages/Header';
import Dashboard from './components/pages/Dashboard';
import EnhancedDashboard from './components/pages/EnhancedDashboard';
import NetworkView from './components/pages/NetworkView';
import AnalyticsPage from './components/pages/AnalyticsPage';
import IncidentsPage from './components/pages/IncidentsPage';
import MumbaiLocal from './components/pages/MumbaiLocal';
import SignIn from './components/pages/SignIn';
import SignUp from './components/pages/SignUp';

function App() {
  return (
    <Router>
      <Routes>
        {/* Home/Landing Page */}
        <Route path='/' element={<Header />} />
        
        {/* Dashboard Routes */}
        <Route path="/dashboard" element={<EnhancedDashboard />} />
        <Route path="/dashboard-simple" element={<Dashboard />} />
        
        {/* Network & Analytics Routes */}
        <Route path="/network" element={<NetworkView />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/incidents" element={<IncidentsPage />} />
        
        {/* Mumbai Local Route */}
        <Route path="/mumbai-local" element={<MumbaiLocal />} />
        
        {/* Authentication Routes */}
        <Route path="/signin" element={<SignIn />} />
        <Route path="/signup" element={<SignUp />} />
        
        {/* About Page */}
        <Route path="/about" element={<AboutPage />} />
        <Route path="/AboutUs" element={<AboutPage />} />
        
        {/* Catch-all route for 404 */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Router>
  );
}

// Simple About Page Component
function AboutPage() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-300 flex items-center justify-center p-6">
      <div className="max-w-4xl bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-2xl p-8 shadow-xl transition-colors duration-300">
        <h1 className="text-4xl font-bold mb-6 text-gray-900 dark:text-gray-100">About AlgoYatri</h1>
        <p className="text-lg text-gray-700 dark:text-gray-300 mb-4">
          AlgoYatri is an advanced Railway Operations Control System powered by Deep Reinforcement Learning and AI optimization algorithms.
        </p>
        <p className="text-lg text-gray-700 dark:text-gray-300 mb-6">
          Our system helps optimize train schedules, reduce delays, and improve overall network efficiency across the Indian Railways network.
        </p>
        <div className="grid grid-cols-2 gap-6 mt-8">
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-700 rounded-lg p-4 transition-colors duration-300">
            <h3 className="text-xl font-bold mb-2 text-gray-900 dark:text-gray-100">Real-Time Tracking</h3>
            <p className="text-gray-700 dark:text-gray-300">Monitor train movements across the entire network in real-time.</p>
          </div>
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg p-4 transition-colors duration-300">
            <h3 className="text-xl font-bold mb-2 text-gray-900 dark:text-gray-100">AI Optimization</h3>
            <p className="text-gray-700 dark:text-gray-300">Deep RL algorithms optimize scheduling and routing decisions.</p>
          </div>
          <div className="bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-700 rounded-lg p-4 transition-colors duration-300">
            <h3 className="text-xl font-bold mb-2 text-gray-900 dark:text-gray-100">Incident Management</h3>
            <p className="text-gray-700 dark:text-gray-300">Proactive detection and resolution of network incidents.</p>
          </div>
          <div className="bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-700 rounded-lg p-4 transition-colors duration-300">
            <h3 className="text-xl font-bold mb-2 text-gray-900 dark:text-gray-100">Analytics Dashboard</h3>
            <p className="text-gray-700 dark:text-gray-300">Comprehensive insights into network performance metrics.</p>
          </div>
        </div>
        <div className="mt-8 flex gap-4">
          <a href="/" className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg font-semibold transition-colors text-white">
            Back to Home
          </a>
          <a href="/dashboard" className="px-6 py-3 bg-green-600 hover:bg-green-700 rounded-lg font-semibold transition-colors text-white">
            View Dashboard
          </a>
        </div>
      </div>
    </div>
  );
}

// 404 Not Found Component
function NotFound() {
  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-300 flex items-center justify-center p-6">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-gray-900 dark:text-gray-100 mb-4">404</h1>
        <p className="text-2xl text-gray-700 dark:text-gray-300 mb-8">Page Not Found</p>
        <a 
          href="/" 
          className="px-8 py-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-colors inline-block"
        >
          Return to Home
        </a>
      </div>
    </div>
  );
}

export default App;