import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ZoomIn, ZoomOut, Home, Play, Pause, Zap, Bell, Settings, 
  LogOut, User, TrendingUp, AlertTriangle, CheckCircle, Clock,
  Train, MapPin, Activity, BarChart3, Radio, RefreshCw, Download,
  List, Map as MapIcon, Calendar, HelpCircle, Maximize2, Filter
} from 'lucide-react';

// File: frontend/src/components/pages/EnhancedDashboard.tsx

const Toast = ({ message, show, onClose, type = 'success' }) => {
  useEffect(() => {
    if (show) {
      const timer = setTimeout(onClose, 3000);
      return () => clearTimeout(timer);
    }
  }, [show, onClose]);

  if (!show) return null;

  return (
    <div className={`fixed top-20 right-4 z-[100] p-4 ${type === 'success' ? 'bg-green-500' : 'bg-orange-500'} text-white rounded-lg shadow-xl transition-all duration-300 animate-slide-in-right flex items-center gap-2`}>
      {type === 'success' ? <CheckCircle className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
      <span>{message}</span>
    </div>
  );
};

// Optimization Modal Component
const OptimizationModal = ({ isOpen, onClose, onOptimize }) => {
  const [objectives, setObjectives] = useState({
    minimizeDelay: true,
    maxThroughput: true,
    balanceLoad: false
  });
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleOptimize = () => {
    setIsRunning(true);
    setProgress(0);
    
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setTimeout(() => {
            setIsRunning(false);
            onOptimize();
            onClose();
          }, 500);
          return 100;
        }
        return prev + 2;
      });
    }, 90);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-2xl max-w-md w-full mx-4">
        <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-4 rounded-t-xl">
          <h3 className="text-xl font-bold flex items-center gap-2">
            <Zap className="w-6 h-6" />
            Network Optimization
          </h3>
        </div>

        <div className="p-6">
          <h4 className="text-sm font-bold text-gray-800 mb-4">Optimization Objectives</h4>
          
          <div className="space-y-3 mb-6">
            <label className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer">
              <input
                type="checkbox"
                checked={objectives.minimizeDelay}
                onChange={(e) => setObjectives({...objectives, minimizeDelay: e.target.checked})}
                className="w-5 h-5 text-purple-600 rounded"
              />
              <div>
                <div className="text-sm font-medium text-gray-900">Minimize Global Delay</div>
                <div className="text-xs text-gray-500">Reduce average delay across all trains</div>
              </div>
            </label>

            <label className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer">
              <input
                type="checkbox"
                checked={objectives.maxThroughput}
                onChange={(e) => setObjectives({...objectives, maxThroughput: e.target.checked})}
                className="w-5 h-5 text-purple-600 rounded"
              />
              <div>
                <div className="text-sm font-medium text-gray-900">Maximize Throughput</div>
                <div className="text-xs text-gray-500">Increase number of trains processed</div>
              </div>
            </label>

            <label className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer">
              <input
                type="checkbox"
                checked={objectives.balanceLoad}
                onChange={(e) => setObjectives({...objectives, balanceLoad: e.target.checked})}
                className="w-5 h-5 text-purple-600 rounded"
              />
              <div>
                <div className="text-sm font-medium text-gray-900">Balance Load Distribution</div>
                <div className="text-xs text-gray-500">Distribute traffic evenly across routes</div>
              </div>
            </label>
          </div>

          {isRunning && (
            <div className="mb-6">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-600">Optimizing...</span>
                <span className="text-purple-600 font-semibold">{progress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-3">
                <div 
                  className="bg-gradient-to-r from-purple-600 to-blue-600 h-3 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            </div>
          )}

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="text-xs text-gray-600 mb-1">Estimated Time</div>
            <div className="text-2xl font-bold text-blue-600">~45 seconds</div>
          </div>

          <div className="flex gap-3">
            <button
              onClick={handleOptimize}
              disabled={isRunning}
              className="flex-1 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 disabled:from-gray-400 disabled:to-gray-500 text-white rounded-lg font-semibold transition-all flex items-center justify-center gap-2"
            >
              <Zap className="w-5 h-5" />
              {isRunning ? 'Optimizing...' : 'Start Optimization'}
            </button>
            <button
              onClick={onClose}
              disabled={isRunning}
              className="px-6 py-3 bg-gray-200 hover:bg-gray-300 disabled:bg-gray-100 text-gray-700 rounded-lg font-semibold transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main Dashboard Component
function EnhancedDashboard() {
  const navigate = useNavigate();
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString());
  const [activeTab, setActiveTab] = useState('live');
  const [viewMode, setViewMode] = useState('map'); // 'map' or 'gantt'
  const [viewBox, setViewBox] = useState({ x: -400, y: -300, width: 800, height: 600 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [isAnimating, setIsAnimating] = useState(true);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [showOptModal, setShowOptModal] = useState(false);
  const [selectedStation, setSelectedStation] = useState(null);
  const [showStationModal, setShowStationModal] = useState(false);

  // Enhanced station data with signals and platform info
  const [stations] = useState(new Map([
    ['CST', { 
      id: 'CST', name: 'CST', city: 'Mumbai', type: 'Terminal', 
      x: -200, y: 0, 
      signal: 'green', 
      platforms: { total: 18, occupied: 12 },
      connections: ['DADAR', 'MASJID'] 
    }],
    ['DADAR', { 
      id: 'DADAR', name: 'DADAR', city: 'Mumbai', type: 'Interstate', 
      x: -100, y: -100, 
      signal: 'yellow', 
      platforms: { total: 6, occupied: 5 },
      connections: ['CST', 'KURLA', 'BYC'] 
    }],
    ['KURLA', { 
      id: 'KURLA', name: 'KURLA', city: 'Mumbai', type: 'Interstate', 
      x: 0, y: -150, 
      signal: 'red', 
      platforms: { total: 8, occupied: 8 },
      connections: ['DADAR', 'THANE'],
      hasConflict: true
    }],
    ['THANE', { 
      id: 'THANE', name: 'THANE', city: 'Mumbai', type: 'Interstate', 
      x: 100, y: -100, 
      signal: 'green', 
      platforms: { total: 7, occupied: 4 },
      connections: ['KURLA', 'DOMBIVLI'] 
    }],
    ['DOMBIVLI', { 
      id: 'DOMBIVLI', name: 'DOMBIVLI', city: 'Thane', type: 'Local', 
      x: 200, y: 0, 
      signal: 'green', 
      platforms: { total: 4, occupied: 2 },
      connections: ['THANE'] 
    }],
  ]));

  const [connections] = useState([
    { from: 'CST', to: 'DADAR', id: 'CST-DADAR' },
    { from: 'DADAR', to: 'KURLA', id: 'DADAR-KURLA' },
    { from: 'KURLA', to: 'THANE', id: 'KURLA-THANE' },
    { from: 'THANE', to: 'DOMBIVLI', id: 'THANE-DOMBIVLI' },
  ]);

  const [trains, setTrains] = useState([
    { id: 'W01', route: 'CST → DADAR', progress: 0.3, delay: 0, connectionId: 'CST-DADAR', speed: 0.003, direction: 'forward', priority: 8 },
    { id: 'W02', route: 'DADAR → KURLA', progress: 0.6, delay: 2, connectionId: 'DADAR-KURLA', speed: 0.004, direction: 'forward', priority: 5 },
    { id: 'C01', route: 'KURLA → THANE', progress: 0.4, delay: 0, connectionId: 'KURLA-THANE', speed: 0.005, direction: 'forward', priority: 6 },
  ]);

  const [stats] = useState({
    activeTrains: 247,
    onTimePercent: 78,
    avgDelay: 4.2,
    conflicts: 3
  });

  // Handle tab navigation
  const handleTabClick = (tabId) => {
    setActiveTab(tabId);
    
    // Navigate to different routes based on tab
    switch(tabId) {
      case 'live':
        // Stay on current dashboard
        break;
      case 'network':
        navigate('/network');
        break;
      case 'analytics':
        navigate('/analytics');
        break;
      case 'incidents':
        navigate('/incidents');
        break;
      case 'settings':
        // Could navigate to settings page if you create one
        setToastMessage('Settings page coming soon!');
        setShowToast(true);
        break;
      default:
        break;
    }
  };

  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date().toLocaleTimeString()), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!isAnimating) return;
    const interval = setInterval(() => {
      setTrains(prevTrains => 
        prevTrains.map(train => ({
          ...train,
          progress: (train.progress + train.speed) % 1
        }))
      );
    }, 16);
    return () => clearInterval(interval);
  }, [isAnimating]);

  const getStationColor = (stationName) => {
    if (!stationName) return '#9ca3af';
    const firstLetter = stationName.charAt(0).toUpperCase();
    if (firstLetter >= 'A' && firstLetter <= 'I') return '#2563eb';
    if (firstLetter >= 'J' && firstLetter <= 'R') return '#dc2626';
    if (firstLetter >= 'S' && firstLetter <= 'Z') return '#059669';
    return '#f59e0b';
  };

  const getSignalColor = (signal) => {
    if (signal === 'green') return '#10b981';
    if (signal === 'yellow') return '#f59e0b';
    return '#ef4444';
  };

  const getTrainPosition = (train) => {
    const connection = connections.find(c => c.id === train.connectionId);
    if (!connection) return { x: 0, y: 0 };
    const fromStation = stations.get(connection.from);
    const toStation = stations.get(connection.to);
    if (!fromStation || !toStation) return { x: 0, y: 0 };
    const progress = train.direction === 'backward' ? 1 - train.progress : train.progress;
    return {
      x: fromStation.x + (toStation.x - fromStation.x) * progress,
      y: fromStation.y + (toStation.y - fromStation.y) * progress
    };
  };

  const handleMouseDown = (e) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    const dx = (e.clientX - dragStart.x) * (viewBox.width / 800);
    const dy = (e.clientY - dragStart.y) * (viewBox.height / 600);
    setViewBox(prev => ({ ...prev, x: prev.x - dx, y: prev.y - dy }));
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const handleMouseUp = () => setIsDragging(false);

  const handleWheel = (e) => {
    e.preventDefault();
    const scaleFactor = e.deltaY > 0 ? 1.1 : 0.9;
    const rect = containerRef.current.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    const svgX = viewBox.x + (mouseX / 800) * viewBox.width;
    const svgY = viewBox.y + (mouseY / 600) * viewBox.height;
    const newWidth = viewBox.width * scaleFactor;
    const newHeight = viewBox.height * scaleFactor;
    setViewBox({
      x: svgX - (mouseX / 800) * newWidth,
      y: svgY - (mouseY / 600) * newHeight,
      width: newWidth,
      height: newHeight
    });
  };

  const resetView = () => setViewBox({ x: -400, y: -300, width: 800, height: 600 });
  const zoomIn = () => setViewBox(prev => ({
    x: prev.x + prev.width * 0.1,
    y: prev.y + prev.height * 0.1,
    width: prev.width * 0.8,
    height: prev.height * 0.8
  }));
  const zoomOut = () => setViewBox(prev => ({
    x: prev.x - prev.width * 0.125,
    y: prev.y - prev.height * 0.125,
    width: prev.width * 1.25,
    height: prev.height * 1.25
  }));

  const handleStationClick = (station) => {
    setSelectedStation(station);
    setShowStationModal(true);
  };

  const handleOptimize = () => {
    setToastMessage('Network optimization completed successfully!');
    setShowToast(true);
  };

  return (
    <div className="h-screen w-full bg-gray-50 flex flex-col overflow-hidden">
      <Toast message={toastMessage} show={showToast} onClose={() => setShowToast(false)} />
      <OptimizationModal 
        isOpen={showOptModal} 
        onClose={() => setShowOptModal(false)}
        onOptimize={handleOptimize}
      />

      {/* Government Header */}
      <div className="bg-gradient-to-r from-blue-900 via-blue-800 to-blue-900 text-white px-6 py-3 shadow-lg border-b-4 border-orange-500">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center">
              <div className="text-blue-900 font-bold text-sm">IR</div>
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-wide">RAILWAY OPERATIONS CONTROL SYSTEM</h1>
              <p className="text-xs text-blue-200">Ministry of Railways • Government of India</p>
            </div>
          </div>
          <div className="flex items-center gap-6">
            <div className="text-right">
              <div className="text-sm font-semibold">{currentTime}</div>
              <div className="text-xs text-blue-200">IST</div>
            </div>
            <button className="p-2 hover:bg-blue-700 rounded-lg transition-colors relative">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>
            <button className="flex items-center gap-2 hover:bg-blue-700 px-3 py-2 rounded-lg transition-colors">
              <User className="w-5 h-5" />
              <span className="text-sm">Controller</span>
            </button>
            <button className="p-2 hover:bg-blue-700 rounded-lg transition-colors">
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white border-b border-gray-200 px-6">
        <div className="flex gap-1">
          {[
            { id: 'live', icon: Train, label: 'Live Ops' },
            { id: 'network', icon: MapIcon, label: 'Network' },
            { id: 'analytics', icon: BarChart3, label: 'Analytics' },
            { id: 'incidents', icon: AlertTriangle, label: 'Incidents' },
            { id: 'settings', icon: Settings, label: 'Settings' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => handleTabClick(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 font-medium transition-all ${
                activeTab === tab.id
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Strip */}
      <div className="bg-white border-b border-gray-200 px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-2">
              <Train className="w-5 h-5 text-blue-600" />
              <div>
                <div className="text-xs text-gray-500">Active Trains</div>
                <div className="text-lg font-bold text-gray-800">{stats.activeTrains}</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <div>
                <div className="text-xs text-gray-500">On-Time</div>
                <div className="text-lg font-bold text-green-600">{stats.onTimePercent}%</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-orange-600" />
              <div>
                <div className="text-xs text-gray-500">Avg Delay</div>
                <div className="text-lg font-bold text-orange-600">{stats.avgDelay} min</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-600" />
              <div>
                <div className="text-xs text-gray-500">Conflicts</div>
                <div className="text-lg font-bold text-red-600">{stats.conflicts}</div>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-600 font-medium">System Operational</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Panel - Train List */}
        <div className="w-64 bg-white border-r flex-shrink-0 flex flex-col">
          <div className="p-4 border-b">
            <h3 className="text-sm font-bold text-gray-800 mb-3">TRAIN LIST</h3>
            <select className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg">
              <option>All Trains ({trains.length})</option>
              <option>On Time</option>
              <option>Delayed</option>
            </select>
          </div>
          <div className="flex-1 overflow-y-auto">
            {trains.map(train => (
              <div key={train.id} className="p-3 border-b hover:bg-blue-50 cursor-pointer transition-colors">
                <div className="flex items-start justify-between mb-1">
                  <div className="text-sm font-semibold text-gray-800">{train.id}</div>
                  {train.delay > 0 ? (
                    <span className="text-xs px-2 py-0.5 bg-red-100 text-red-700 rounded-full">+{train.delay}m</span>
                  ) : (
                    <span className="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded-full">✓</span>
                  )}
                </div>
                <div className="text-xs text-gray-600 mb-1">{train.route}</div>
                <div className="text-xs text-gray-500 mb-2">Priority: {train.priority}</div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 bg-gray-200 rounded-full h-1">
                    <div 
                      className="bg-blue-600 h-1 rounded-full transition-all"
                      style={{ width: `${train.progress * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-xs text-gray-500">{Math.round(train.progress * 100)}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Center Panel - Map/Gantt */}
        <div className="flex-1 flex flex-col">
          {/* View Controls */}
          <div className="bg-white px-4 py-2 flex items-center justify-between border-b">
            <div className="flex items-center gap-3">
              <button
                onClick={() => setIsAnimating(!isAnimating)}
                className="flex items-center gap-2 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-all shadow-md text-sm font-semibold"
              >
                {isAnimating ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                {isAnimating ? 'Pause' : 'Start'}
              </button>
              
              <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setViewMode('map')}
                  className={`flex items-center gap-1 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    viewMode === 'map'
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <MapIcon className="w-4 h-4" />
                  Map View
                </button>
                <button
                  onClick={() => setViewMode('gantt')}
                  className={`flex items-center gap-1 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                    viewMode === 'gantt'
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  <List className="w-4 h-4" />
                  Gantt View
                </button>
              </div>

              <button
                onClick={() => setShowOptModal(true)}
                className="flex items-center gap-2 px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg transition-all shadow-md text-sm font-semibold"
              >
                <Zap className="w-4 h-4" />
                Optimize
              </button>
            </div>
            
            <div className="flex items-center gap-2">
              <button onClick={zoomIn} className="p-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
                <ZoomIn className="w-4 h-4 text-gray-700" />
              </button>
              <button onClick={zoomOut} className="p-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
                <ZoomOut className="w-4 h-4 text-gray-700" />
              </button>
              <button onClick={resetView} className="p-2 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
                <Home className="w-4 h-4 text-gray-700" />
              </button>
            </div>
          </div>

          {/* Map Canvas */}
          {viewMode === 'map' ? (
            <div 
              ref={containerRef}
              className="flex-1 overflow-hidden cursor-move bg-gradient-to-br from-gray-50 to-gray-100"
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              onWheel={handleWheel}
            >
              <svg
                ref={svgRef}
                width="100%"
                height="100%"
                viewBox={`${viewBox.x} ${viewBox.y} ${viewBox.width} ${viewBox.height}`}
              >
                <defs>
                  <pattern id="dots" width="25" height="25" patternUnits="userSpaceOnUse">
                    <circle cx="12.5" cy="12.5" r="1" fill="#d1d5db" opacity="0.6"/>
                  </pattern>
                  <filter id="glow">
                    <feGaussianBlur stdDeviation="2" result="coloredBlur"/>
                    <feMerge>
                      <feMergeNode in="coloredBlur"/>
                      <feMergeNode in="SourceGraphic"/>
                    </feMerge>
                  </filter>
                </defs>
                
                <rect x={viewBox.x} y={viewBox.y} width={viewBox.width} height={viewBox.height} fill="url(#dots)" />
                
                {/* Connections */}
                {connections.map(connection => {
                  const fromStation = stations.get(connection.from);
                  const toStation = stations.get(connection.to);
                  if (!fromStation || !toStation) return null;
                  
                  return (
                    <g key={connection.id}>
                      <line
                        x1={fromStation.x} y1={fromStation.y}
                        x2={toStation.x} y2={toStation.y}
                        stroke="#6b7280" strokeWidth="4"
                        opacity="0.6" strokeLinecap="round"
                      />
                    </g>
                  );
                })}
                
                {/* Trains */}
                {isAnimating && trains.map(train => {
                  const pos = getTrainPosition(train);
                  return (
                    <g key={train.id}>
                      <circle cx={pos.x} cy={pos.y} r="8" fill="#f97316" filter="url(#glow)" />
                      <circle cx={pos.x} cy={pos.y} r="4" fill="#fff" opacity="0.8" />
                    </g>
                  );
                })}
                
                {/* Stations with Enhanced Features */}
                {Array.from(stations.values()).map(station => (
                  <g key={station.id}>
                    {/* Conflict Diamond */}
                    {station.hasConflict && (
                      <rect
                        x={station.x - 20}
                        y={station.y - 20}
                        width="40"
                        height="40"
                        fill="none"
                        stroke="#ef4444"
                        strokeWidth="3"
                        transform={`rotate(45, ${station.x}, ${station.y})`}
                        className="animate-pulse"
                      />
                    )}
                    
                    {/* Station Glow */}
                    <circle
                      cx={station.x} cy={station.y} r="18"
                      fill={getStationColor(station.name)}
                      opacity="0.15" filter="url(#glow)"
                    />
                    
                    {/* Station Node */}
                    <circle
                      cx={station.x} cy={station.y} r="12"
                      fill={getStationColor(station.name)}
                      stroke="#ffffff" strokeWidth="3"
                      className="cursor-pointer hover:r-14 transition-all"
                      onClick={() => handleStationClick(station)}
                    />
                    
                    {/* Signal Indicator */}
                    <circle
                      cx={station.x + 15}
                      cy={station.y - 15}
                      r="6"
                      fill={getSignalColor(station.signal)}
                      stroke="#ffffff"
                      strokeWidth="2"
                      className="animate-pulse"
                    />
                    
                    {/* Station Name */}
                    <text
                      x={station.x} y={station.y - 25}
                      textAnchor="middle"
                      className="fill-gray-900 font-bold pointer-events-none"
                      style={{ fontSize: Math.max(10, 14 * (800 / viewBox.width)) }}
                    >
                      {station.name}
                    </text>
                    
                    {/* Platform Occupancy Bar */}
                    <g transform={`translate(${station.x - 20}, ${station.y + 20})`}>
                      <rect
                        x="0" y="0" width="40" height="4"
                        fill="#e5e7eb" rx="2"
                      />
                      <rect
                        x="0" y="0" 
                        width={40 * (station.platforms.occupied / station.platforms.total)} 
                        height="4"
                        fill={station.platforms.occupied / station.platforms.total > 0.8 ? '#ef4444' : '#10b981'}
                        rx="2"
                      />
                    </g>
                    
                    {/* Platform Count */}
                    <text
                      x={station.x} y={station.y + 35}
                      textAnchor="middle"
                      className="fill-gray-600 pointer-events-none text-xs"
                      style={{ fontSize: Math.max(8, 10 * (800 / viewBox.width)) }}
                    >
                      {station.platforms.occupied}/{station.platforms.total}
                    </text>
                  </g>
                ))}
              </svg>
            </div>
          ) : (
            /* Gantt View */
            <div className="flex-1 overflow-auto p-6 bg-gray-50">
              <div className="bg-white rounded-lg border shadow-sm p-6">
                <h3 className="text-lg font-bold text-gray-800 mb-4">Train Schedule - Gantt View</h3>
                
                {/* Timeline Header */}
                <div className="flex border-b pb-2 mb-4">
                  <div className="w-32 text-sm font-semibold text-gray-700">Train</div>
                  <div className="flex-1 flex justify-between text-xs text-gray-500">
                    <span>00:00</span>
                    <span>06:00</span>
                    <span>12:00</span>
                    <span>18:00</span>
                    <span>24:00</span>
                  </div>
                </div>

                {/* Gantt Rows */}
                {trains.map((train, idx) => (
                  <div key={train.id} className="flex items-center py-3 border-b hover:bg-gray-50">
                    <div className="w-32">
                      <div className="text-sm font-semibold text-gray-800">{train.id}</div>
                      <div className="text-xs text-gray-500">{train.route}</div>
                    </div>
                    <div className="flex-1 relative h-8 bg-gray-100 rounded">
                      <div 
                        className={`absolute h-full rounded ${train.delay > 0 ? 'bg-red-400' : 'bg-green-400'}`}
                        style={{ 
                          left: `${idx * 10}%`, 
                          width: '30%' 
                        }}
                      >
                        <span className="text-xs text-white font-medium px-2 leading-8">
                          {train.delay > 0 ? `+${train.delay}m` : 'On Time'}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Status Bar */}
          <div className="bg-white px-6 py-2 text-xs text-gray-600 border-t flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span>Zoom: {(800 / viewBox.width * 100).toFixed(0)}%</span>
              <span className="text-gray-400">|</span>
              <span>Animation: {isAnimating ? 'Running' : 'Paused'}</span>
            </div>
            <div className="flex items-center gap-2">
              <Radio className="w-3 h-3 text-green-500 animate-pulse" />
              <span className="text-green-600 font-medium">Connected</span>
              <span className="text-gray-400">•</span>
              <span>Latency: 24ms</span>
              <span className="text-gray-400">•</span>
              <span>Model: Active</span>
              <span className="text-gray-400">•</span>
              <span>v2.1.0</span>
            </div>
          </div>
        </div>

        {/* Right Panel - AI Recommendations */}
        <div className="w-80 bg-white border-l flex-shrink-0 flex flex-col">
          <div className="p-4 border-b bg-gradient-to-r from-purple-50 to-blue-50">
            <div className="flex items-center gap-2 mb-2">
              <Activity className="w-5 h-5 text-purple-600" />
              <h3 className="text-sm font-bold text-gray-800">AI ASSISTANT</h3>
            </div>
            <div className="text-xs text-gray-600">Powered by Deep RL</div>
          </div>
          
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Recommendation Card */}
            <div className="bg-gradient-to-br from-blue-50 to-purple-50 border-2 border-blue-200 rounded-lg p-4">
              <div className="flex items-start justify-between mb-2">
                <div className="text-sm font-semibold text-gray-800">Hold W03 at DADAR</div>
                <span className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded-full">
                  85% confidence
                </span>
              </div>
              <div className="text-xs text-gray-700 mb-3">
                Platform 3 will be free in 90 seconds. Prevents downstream congestion at KURLA.
              </div>
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="w-4 h-4 text-green-600" />
                <span className="text-xs text-green-700 font-medium">Impact: -3min global delay</span>
              </div>
              <div className="bg-blue-50 border border-blue-200 rounded p-2 mb-3 text-xs text-gray-700">
                <strong>Why?</strong> Analysis shows that holding reduces cascading delays by 40% based on historical patterns.
              </div>
              <div className="flex gap-2">
                <button className="flex-1 px-3 py-2 bg-green-600 hover:bg-green-700 text-white text-xs font-semibold rounded-lg transition-colors">
                  ✓ Apply
                </button>
                <button className="px-3 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 text-xs font-semibold rounded-lg transition-colors">
                  ✗ Reject
                </button>
                <button className="p-2 bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-lg transition-colors">
                  <HelpCircle className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Active Conflicts */}
            <div>
              <h4 className="text-xs font-semibold text-gray-700 mb-2 uppercase flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-orange-600" />
                Active Conflicts
              </h4>
              <div className="space-y-2">
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
                  <div className="text-sm font-semibold text-orange-900">KURLA Junction</div>
                  <div className="text-xs text-orange-700 mt-1">Platform conflict: W02 & C03</div>
                  <div className="text-xs text-orange-600 mt-1 font-medium">ETA: 5 min</div>
                </div>
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <div className="text-sm font-semibold text-red-900">DADAR</div>
                  <div className="text-xs text-red-700 mt-1">Signal delay affecting 3 trains</div>
                  <div className="text-xs text-red-600 mt-1 font-medium">ETA: 12 min</div>
                </div>
              </div>
            </div>

            {/* Legend */}
            <div className="bg-gray-50 rounded-lg p-3 border">
              <h4 className="text-xs font-semibold text-gray-700 mb-2">Signal Legend</h4>
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  <span className="text-xs text-gray-600">Green - Clear</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                  <span className="text-xs text-gray-600">Yellow - Caution</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                  <span className="text-xs text-gray-600">Red - Stop</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 border-2 border-red-500 rotate-45"></div>
                  <span className="text-xs text-gray-600">Diamond - Conflict</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Enhanced Station Modal */}
      {showStationModal && selectedStation && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[600px] overflow-hidden">
            <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-4 flex justify-between items-center">
              <div>
                <h3 className="text-xl font-bold flex items-center gap-2">
                  <MapPin className="w-5 h-5" />
                  {selectedStation.name} Station
                </h3>
                <p className="text-sm text-blue-100 mt-1">{selectedStation.city} • {selectedStation.type}</p>
              </div>
              <div className="flex items-center gap-3">
                <button className="flex items-center gap-2 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors text-sm font-semibold shadow-lg">
                  <Zap className="w-4 h-4" />
                  Optimize
                </button>
                <button 
                  onClick={() => setShowStationModal(false)}
                  className="text-3xl font-bold w-10 h-10 flex items-center justify-center rounded-lg hover:bg-blue-600 transition-colors"
                >
                  ×
                </button>
              </div>
            </div>

            <div className="p-6 overflow-y-auto max-h-[500px]">
              {/* Station Stats */}
              <div className="bg-gradient-to-br from-gray-50 to-blue-50 p-5 rounded-xl mb-6 border border-blue-100">
                <h4 className="text-sm font-bold text-gray-800 mb-4">Station Information</h4>
                <div className="grid grid-cols-3 gap-3">
                  <div className="bg-white p-3 rounded-lg shadow-sm">
                    <div className="text-xs text-gray-500 mb-1">Type</div>
                    <div className="text-sm font-bold text-gray-900">{selectedStation.type}</div>
                  </div>
                  <div className="bg-white p-3 rounded-lg shadow-sm">
                    <div className="text-xs text-gray-500 mb-1">Platforms</div>
                    <div className="text-sm font-bold text-blue-600">
                      {selectedStation.platforms.occupied}/{selectedStation.platforms.total}
                    </div>
                  </div>
                  <div className="bg-white p-3 rounded-lg shadow-sm">
                    <div className="text-xs text-gray-500 mb-1">Signal</div>
                    <div className="flex items-center gap-1">
                      <div className={`w-3 h-3 rounded-full`} style={{ backgroundColor: getSignalColor(selectedStation.signal) }}></div>
                      <span className="text-sm font-bold capitalize">{selectedStation.signal}</span>
                    </div>
                  </div>
                  <div className="bg-white p-3 rounded-lg shadow-sm">
                    <div className="text-xs text-gray-500 mb-1">Occupancy</div>
                    <div className="text-sm font-bold text-orange-600">
                      {Math.round((selectedStation.platforms.occupied / selectedStation.platforms.total) * 100)}%
                    </div>
                  </div>
                  <div className="bg-white p-3 rounded-lg shadow-sm">
                    <div className="text-xs text-gray-500 mb-1">Connections</div>
                    <div className="text-sm font-bold text-purple-600">{selectedStation.connections.length}</div>
                  </div>
                  <div className="bg-white p-3 rounded-lg shadow-sm">
                    <div className="text-xs text-gray-500 mb-1">Status</div>
                    <div className="text-sm font-bold text-green-600 flex items-center gap-1">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                      Active
                    </div>
                  </div>
                </div>
              </div>

              {/* Schedule */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-bold text-gray-800 mb-3 flex items-center gap-2">
                    <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                    Departures (8)
                  </h4>
                  <div className="space-y-2">
                    {['SINHAGAD EXP', 'DECCAN QUEEN', 'KOYNA EXP'].map((train, idx) => (
                      <div key={idx} className="bg-green-50 p-3 rounded-lg border-l-4 border-green-500">
                        <div className="text-sm font-semibold text-gray-900">{train}</div>
                        <div className="text-xs text-gray-600 mt-1">Departs: 06:{35 + idx * 10}</div>
                        <div className="text-xs text-gray-600">Platform: {idx + 1}</div>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-sm font-bold text-gray-800 mb-3 flex items-center gap-2">
                    <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                    Arrivals (6)
                  </h4>
                  <div className="space-y-2">
                    {['PUNE LOCAL', 'SHATABDI EXP', 'MUMBAI MAIL'].map((train, idx) => (
                      <div key={idx} className="bg-blue-50 p-3 rounded-lg border-l-4 border-blue-500">
                        <div className="text-sm font-semibold text-gray-900">{train}</div>
                        <div className="text-xs text-gray-600 mt-1">Arrives: 06:{30 + idx * 15}</div>
                        <div className="text-xs text-gray-600">Platform: {idx + 4}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="bg-gray-50 px-6 py-4 flex justify-between items-center border-t">
              <div className="flex gap-2">
                <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors flex items-center gap-2">
                  <Download className="w-4 h-4" />
                  Export
                </button>
                <button className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white text-sm rounded-lg transition-colors flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4" />
                  Report Issue
                </button>
              </div>
              <button 
                onClick={() => setShowStationModal(false)}
                className="px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors text-sm font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes slide-in-right {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
        
        .animate-slide-in-right {
          animation: slide-in-right 0.3s ease-out;
        }
        
        ::-webkit-scrollbar {
          width: 8px;
          height: 8px;
        }
        
        ::-webkit-scrollbar-track {
          background: #f1f5f9;
        }
        
        ::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 4px;
        }
      `}</style>
    </div>
  );
}

export default EnhancedDashboard;