import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ZoomIn, ZoomOut, Download, Filter, Zap, AlertTriangle, TrendingUp, MapPin } from 'lucide-react';

function NetworkView() {
  const navigate = useNavigate();
  const [selectedZone, setSelectedZone] = useState('all');
  const [viewMode, setViewMode] = useState('map');

  const zones = [
    { code: 'ALL', name: 'All Zones', color: 'gray' },
    { code: 'CR', name: 'Central Railway', color: 'blue' },
    { code: 'WR', name: 'Western Railway', color: 'green' },
    { code: 'SR', name: 'Southern Railway', color: 'red' },
    { code: 'NR', name: 'Northern Railway', color: 'yellow' },
    { code: 'ER', name: 'Eastern Railway', color: 'purple' },
    { code: 'SCR', name: 'South Central', color: 'orange' },
    { code: 'ECR', name: 'East Central', color: 'pink' },
  ];

  const incidents = [
    { zone: 'ECR', type: 'Signal Failure', severity: 'high', eta: '2h' },
    { zone: 'SR', type: 'Track Maintenance', severity: 'medium', eta: '4h' },
    { zone: 'NER', type: 'Weather Delay', severity: 'low', eta: '1h' },
  ];

  return (
    <div className="h-screen bg-gray-50 flex flex-col overflow-hidden">
      {/* Government Header */}
      <div className="bg-gradient-to-r from-blue-900 via-blue-800 to-blue-900 text-white px-6 py-3 border-b-4 border-orange-500">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-xl font-bold">NETWORK COMMAND CENTER</h1>
            <p className="text-sm text-blue-200">All India Railways • Real-Time Overview</p>
          </div>
          <div className="flex items-center gap-3">
            <button 
              onClick={() => navigate('/dashboard')}
              className="px-4 py-2 bg-blue-700 hover:bg-blue-600 rounded-lg text-sm font-semibold transition-colors"
            >
              Back to Dashboard
            </button>
            <button 
              onClick={() => navigate('/')}
              className="px-4 py-2 bg-blue-700 hover:bg-blue-600 rounded-lg text-sm font-semibold transition-colors"
            >
              Home
            </button>
          </div>
        </div>
      </div>

      {/* Zone Filter Bar */}
      <div className="bg-white border-b px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <span className="text-sm font-semibold text-gray-700 flex items-center gap-2">
            <Filter className="w-4 h-4" />
            Zone Filter:
          </span>
          <div className="flex gap-2">
            {zones.map(zone => (
              <button
                key={zone.code}
                onClick={() => setSelectedZone(zone.code.toLowerCase())}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  selectedZone === zone.code.toLowerCase()
                    ? 'bg-blue-600 text-white shadow-lg scale-105'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {zone.code}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-600">View:</span>
          <div className="flex gap-2">
            <button
              onClick={() => setViewMode('map')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                viewMode === 'map'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Map
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                viewMode === 'table'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Table
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Map/Graph Area */}
        <div className="flex-1 p-6 overflow-auto">
          <div className="bg-white rounded-xl border-2 border-gray-200 h-full shadow-lg relative overflow-hidden">
            {/* Map Controls */}
            <div className="absolute top-4 right-4 z-10 flex flex-col gap-2">
              <button className="p-2 bg-white hover:bg-gray-100 rounded-lg shadow-lg border transition-colors">
                <ZoomIn className="w-5 h-5 text-gray-700" />
              </button>
              <button className="p-2 bg-white hover:bg-gray-100 rounded-lg shadow-lg border transition-colors">
                <ZoomOut className="w-5 h-5 text-gray-700" />
              </button>
            </div>

            {/* Network Visualization Placeholder */}
            <div className="w-full h-full flex flex-col items-center justify-center bg-gradient-to-br from-blue-50 to-gray-50">
              <MapPin className="w-16 h-16 text-blue-300 mb-4" />
              <p className="text-gray-500 text-lg font-semibold mb-2">Network Topology Visualization</p>
              <p className="text-gray-400 text-sm">Interactive railway network graph with zone-based coloring</p>
              
              {/* Sample Network Nodes */}
              <div className="mt-8 grid grid-cols-4 gap-6">
                <div className="flex flex-col items-center">
                  <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center shadow-lg mb-2">
                    <span className="text-white font-bold">CR</span>
                  </div>
                  <span className="text-xs text-gray-600">Central</span>
                </div>
                <div className="flex flex-col items-center">
                  <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center shadow-lg mb-2">
                    <span className="text-white font-bold">WR</span>
                  </div>
                  <span className="text-xs text-gray-600">Western</span>
                </div>
                <div className="flex flex-col items-center">
                  <div className="w-16 h-16 bg-red-500 rounded-full flex items-center justify-center shadow-lg mb-2">
                    <span className="text-white font-bold">SR</span>
                  </div>
                  <span className="text-xs text-gray-600">Southern</span>
                </div>
                <div className="flex flex-col items-center">
                  <div className="w-16 h-16 bg-yellow-500 rounded-full flex items-center justify-center shadow-lg mb-2">
                    <span className="text-white font-bold">NR</span>
                  </div>
                  <span className="text-xs text-gray-600">Northern</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Panel - Stats & Controls */}
        <div className="w-96 bg-white border-l flex flex-col overflow-hidden">
          {/* Network Stats */}
          <div className="p-6 border-b">
            <h3 className="text-sm font-bold text-gray-800 mb-4 flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-blue-600" />
              NETWORK STATISTICS
            </h3>
            <div className="space-y-3">
              <div className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg border border-blue-200">
                <div className="text-3xl font-bold text-blue-600 mb-1">12,847</div>
                <div className="text-xs text-gray-600 font-medium">Total Active Trains</div>
              </div>
              <div className="p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-lg border border-green-200">
                <div className="text-3xl font-bold text-green-600 mb-1">82%</div>
                <div className="text-xs text-gray-600 font-medium">On-Time Performance</div>
              </div>
              <div className="p-4 bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg border border-orange-200">
                <div className="text-3xl font-bold text-orange-600 mb-1">8.2 min</div>
                <div className="text-xs text-gray-600 font-medium">Average Delay</div>
              </div>
              <div className="p-4 bg-gradient-to-br from-red-50 to-red-100 rounded-lg border border-red-200">
                <div className="text-3xl font-bold text-red-600 mb-1">23</div>
                <div className="text-xs text-gray-600 font-medium">Congested Zones</div>
              </div>
            </div>
          </div>

          {/* Optimize Section */}
          <div className="p-6 border-b bg-gradient-to-br from-purple-50 to-blue-50">
            <h3 className="text-sm font-bold text-gray-800 mb-3 flex items-center gap-2">
              <Zap className="w-4 h-4 text-purple-600" />
              NETWORK OPTIMIZATION
            </h3>
            <button className="w-full py-3 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 text-white rounded-lg font-bold shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-2 mb-3">
              <Zap className="w-5 h-5" />
              Optimize Network
            </button>
            <div className="space-y-2 text-xs">
              <label className="flex items-center gap-2">
                <input type="checkbox" defaultChecked className="rounded" />
                <span className="text-gray-700">Minimize Global Delay</span>
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" defaultChecked className="rounded" />
                <span className="text-gray-700">Maximize Throughput</span>
              </label>
              <label className="flex items-center gap-2">
                <input type="checkbox" className="rounded" />
                <span className="text-gray-700">Balance Load Distribution</span>
              </label>
            </div>
            <div className="mt-3 p-3 bg-white rounded-lg border">
              <div className="text-xs text-gray-500 mb-1">Estimated Time</div>
              <div className="text-lg font-bold text-purple-600">~45 seconds</div>
            </div>
          </div>

          {/* Active Incidents */}
          <div className="flex-1 p-6 overflow-y-auto">
            <h3 className="text-sm font-bold text-gray-800 mb-3 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-orange-600" />
              ACTIVE INCIDENTS
            </h3>
            <div className="space-y-3">
              {incidents.map((incident, idx) => (
                <div key={idx} className={`p-3 rounded-lg border-l-4 ${
                  incident.severity === 'high' 
                    ? 'bg-red-50 border-red-500' 
                    : incident.severity === 'medium'
                    ? 'bg-orange-50 border-orange-500'
                    : 'bg-yellow-50 border-yellow-500'
                }`}>
                  <div className="flex items-start justify-between mb-1">
                    <span className={`text-sm font-semibold ${
                      incident.severity === 'high' 
                        ? 'text-red-900' 
                        : incident.severity === 'medium'
                        ? 'text-orange-900'
                        : 'text-yellow-900'
                    }`}>
                      {incident.type}
                    </span>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      incident.severity === 'high' 
                        ? 'bg-red-200 text-red-800' 
                        : incident.severity === 'medium'
                        ? 'bg-orange-200 text-orange-800'
                        : 'bg-yellow-200 text-yellow-800'
                    }`}>
                      {incident.severity.toUpperCase()}
                    </span>
                  </div>
                  <div className={`text-xs mb-1 ${
                    incident.severity === 'high' 
                      ? 'text-red-700' 
                      : incident.severity === 'medium'
                      ? 'text-orange-700'
                      : 'text-yellow-700'
                  }`}>
                    Zone: {incident.zone}
                  </div>
                  <div className={`text-xs font-medium ${
                    incident.severity === 'high' 
                      ? 'text-red-600' 
                      : incident.severity === 'medium'
                      ? 'text-orange-600'
                      : 'text-yellow-600'
                  }`}>
                    ETA: {incident.eta}
                  </div>
                </div>
              ))}
            </div>
            <button 
              onClick={() => navigate('/incidents')}
              className="w-full mt-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors"
            >
              View All Incidents ({incidents.length + 7})
            </button>
          </div>

          {/* Export Button */}
          <div className="p-6 border-t bg-gray-50">
            <button className="w-full py-3 bg-white hover:bg-gray-50 text-gray-700 border-2 border-gray-300 rounded-lg font-semibold transition-all flex items-center justify-center gap-2">
              <Download className="w-4 h-4" />
              Export Network Data
            </button>
          </div>
        </div>
      </div>

      {/* Bottom Status Bar */}
      <div className="bg-white border-t px-6 py-3 flex items-center justify-between text-sm">
        <div className="flex items-center gap-4 text-gray-600">
          <span className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            System: Operational
          </span>
          <span>•</span>
          <span>Last Updated: 5 seconds ago</span>
          <span>•</span>
          <span>Active Zones: 16/18</span>
        </div>
        <div className="text-gray-500">
          Network Health: <span className="text-green-600 font-semibold">94%</span>
        </div>
      </div>
    </div>
  );
}

export default NetworkView;