import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  AlertTriangle, Filter, Search, Clock, MapPin, User, 
  CheckCircle, XCircle, AlertCircle, TrendingUp, Download, Home, ArrowLeft
} from 'lucide-react';

function IncidentsPage() {
  const navigate = useNavigate();
  const [filterSeverity, setFilterSeverity] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  const incidents = [
    {
      id: 'INC-2025-001',
      type: 'Signal Failure',
      severity: 'high',
      zone: 'ECR',
      location: 'Patna Junction',
      description: 'Signal system malfunction causing delays on Platform 4-6',
      reportedAt: '2025-01-15 08:30',
      reportedBy: 'Station Master - Patna',
      status: 'active',
      affectedTrains: 12,
      estimatedResolution: '2 hours',
      updates: [
        { time: '08:45', message: 'Engineering team dispatched', user: 'Control Center' },
        { time: '08:30', message: 'Incident reported', user: 'Station Master' }
      ]
    },
    {
      id: 'INC-2025-002',
      type: 'Track Maintenance',
      severity: 'medium',
      zone: 'SR',
      location: 'Chennai Central - Tambaram',
      description: 'Scheduled track maintenance causing single-line operation',
      reportedAt: '2025-01-15 06:00',
      reportedBy: 'Engineering Department',
      status: 'active',
      affectedTrains: 8,
      estimatedResolution: '4 hours',
      updates: [
        { time: '07:30', message: 'Work 50% complete', user: 'Engineer' },
        { time: '06:00', message: 'Maintenance started', user: 'Engineering Dept' }
      ]
    },
    {
      id: 'INC-2025-003',
      type: 'Weather Delay',
      severity: 'low',
      zone: 'NER',
      location: 'Gorakhpur - Lucknow',
      description: 'Dense fog causing reduced visibility, speed restrictions in effect',
      reportedAt: '2025-01-15 05:15',
      reportedBy: 'Weather Monitoring System',
      status: 'monitoring',
      affectedTrains: 6,
      estimatedResolution: '1 hour',
      updates: [
        { time: '08:00', message: 'Visibility improving', user: 'Weather System' },
        { time: '05:15', message: 'Fog alert triggered', user: 'Auto System' }
      ]
    },
    {
      id: 'INC-2025-004',
      type: 'Platform Congestion',
      severity: 'high',
      zone: 'CR',
      location: 'Mumbai CSMT',
      description: 'Overcrowding on platforms 1-3 during peak hours',
      reportedAt: '2025-01-15 08:00',
      reportedBy: 'Platform Supervisor',
      status: 'active',
      affectedTrains: 15,
      estimatedResolution: '30 minutes',
      updates: [
        { time: '08:15', message: 'Additional staff deployed', user: 'Operations Manager' },
        { time: '08:00', message: 'Congestion detected', user: 'Platform Supervisor' }
      ]
    },
    {
      id: 'INC-2025-005',
      type: 'Equipment Failure',
      severity: 'medium',
      zone: 'WR',
      location: 'Surat Junction',
      description: 'Point machine failure on Track 2, using alternate routing',
      reportedAt: '2025-01-15 07:45',
      reportedBy: 'Signal Maintainer',
      status: 'resolving',
      affectedTrains: 5,
      estimatedResolution: '1.5 hours',
      updates: [
        { time: '08:30', message: 'Replacement part installed', user: 'Technician' },
        { time: '08:00', message: 'Part ordered', user: 'Maintenance' },
        { time: '07:45', message: 'Equipment failure detected', user: 'Signal Maintainer' }
      ]
    }
  ];

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'high': return { bg: 'bg-red-50 dark:bg-red-900/20', border: 'border-red-500', text: 'text-red-900 dark:text-red-100', badge: 'bg-red-100 dark:bg-red-900/50 text-red-700 dark:text-red-400' };
      case 'medium': return { bg: 'bg-orange-50 dark:bg-orange-900/20', border: 'border-orange-500', text: 'text-orange-900 dark:text-orange-100', badge: 'bg-orange-100 dark:bg-orange-900/50 text-orange-700 dark:text-orange-400' };
      case 'low': return { bg: 'bg-yellow-50 dark:bg-yellow-900/20', border: 'border-yellow-500', text: 'text-yellow-900 dark:text-yellow-100', badge: 'bg-yellow-100 dark:bg-yellow-900/50 text-yellow-700 dark:text-yellow-400' };
      default: return { bg: 'bg-gray-50 dark:bg-gray-800', border: 'border-gray-500', text: 'text-gray-900 dark:text-gray-100', badge: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300' };
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'active': return <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />;
      case 'resolving': return <Clock className="w-5 h-5 text-orange-600 dark:text-orange-400" />;
      case 'monitoring': return <TrendingUp className="w-5 h-5 text-blue-600 dark:text-blue-400" />;
      case 'resolved': return <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />;
      default: return <XCircle className="w-5 h-5 text-gray-600 dark:text-gray-400" />;
    }
  };

  const filteredIncidents = incidents.filter(incident => {
    const matchesSeverity = filterSeverity === 'all' || incident.severity === filterSeverity;
    const matchesSearch = incident.location.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         incident.type.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         incident.zone.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSeverity && matchesSearch;
  });

  const stats = {
    total: incidents.length,
    active: incidents.filter(i => i.status === 'active').length,
    resolving: incidents.filter(i => i.status === 'resolving').length,
    high: incidents.filter(i => i.severity === 'high').length
  };

  return (
    <div className="h-screen bg-gray-50 dark:bg-gray-900 flex flex-col transition-colors duration-300">
      {/* Header */}
      <div className="bg-gradient-to-r from-orange-600 to-red-600 text-white px-6 py-4 shadow-lg">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <AlertTriangle className="w-7 h-7" />
              INCIDENT MANAGEMENT
            </h1>
            <p className="text-sm text-orange-100 mt-1">Real-time incident tracking and resolution</p>
          </div>
          <div className="flex items-center gap-3">
            <button 
              onClick={() => navigate(-1)}
              className="px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-lg font-semibold transition-colors flex items-center gap-2"
            >
              <ArrowLeft className="w-4 h-4" />
              Back
            </button>
            <button 
              onClick={() => navigate('/')}
              className="px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-lg font-semibold transition-colors flex items-center gap-2"
            >
              <Home className="w-4 h-4" />
              Home
            </button>
            <button className="px-4 py-2 bg-white text-orange-600 rounded-lg font-semibold hover:bg-orange-50 transition-colors flex items-center gap-2">
              <Download className="w-4 h-4" />
              Export Report
            </button>
          </div>
        </div>
      </div>

      {/* Stats Bar */}
      <div className="bg-white dark:bg-gray-800 border-b dark:border-gray-700 px-6 py-4 transition-colors duration-300">
        <div className="grid grid-cols-4 gap-6">
          <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 p-4 rounded-lg border border-blue-200 dark:border-blue-700 transition-colors duration-300">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Incidents</div>
            <div className="text-3xl font-bold text-blue-600 dark:text-blue-400">{stats.total}</div>
          </div>
          <div className="bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 p-4 rounded-lg border border-red-200 dark:border-red-700 transition-colors duration-300">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Active</div>
            <div className="text-3xl font-bold text-red-600 dark:text-red-400">{stats.active}</div>
          </div>
          <div className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 p-4 rounded-lg border border-orange-200 dark:border-orange-700 transition-colors duration-300">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">Resolving</div>
            <div className="text-3xl font-bold text-orange-600 dark:text-orange-400">{stats.resolving}</div>
          </div>
          <div className="bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 p-4 rounded-lg border border-purple-200 dark:border-purple-700 transition-colors duration-300">
            <div className="text-sm text-gray-600 dark:text-gray-400 mb-1">High Priority</div>
            <div className="text-3xl font-bold text-purple-600 dark:text-purple-400">{stats.high}</div>
          </div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-white dark:bg-gray-800 border-b dark:border-gray-700 px-6 py-3 flex items-center gap-4 transition-colors duration-300">
        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500 dark:text-gray-400" />
          <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">Severity:</span>
          <div className="flex gap-2">
            {['all', 'high', 'medium', 'low'].map(severity => (
              <button
                key={severity}
                onClick={() => setFilterSeverity(severity)}
                className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                  filterSeverity === severity
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                {severity.charAt(0).toUpperCase() + severity.slice(1)}
              </button>
            ))}
          </div>
        </div>

        <div className="flex-1"></div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 dark:text-gray-500" />
          <input
            type="text"
            placeholder="Search incidents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 transition-colors duration-300"
          />
        </div>
      </div>

      {/* Incidents List */}
      <div className="flex-1 overflow-auto p-6">
        <div className="space-y-4">
          {filteredIncidents.map(incident => {
            const colors = getSeverityColor(incident.severity);
            return (
              <div key={incident.id} className={`${colors.bg} border-l-4 ${colors.border} rounded-lg p-5 shadow-sm hover:shadow-md transition-all duration-300`}>
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-start gap-3">
                    {getStatusIcon(incident.status)}
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className={`text-lg font-bold ${colors.text}`}>{incident.type}</h3>
                        <span className={`text-xs px-2 py-1 rounded-full font-semibold ${colors.badge}`}>
                          {incident.severity.toUpperCase()}
                        </span>
                        <span className="text-xs px-2 py-1 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-full font-semibold">
                          {incident.id}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                        <span className="flex items-center gap-1">
                          <MapPin className="w-4 h-4" />
                          {incident.location} ({incident.zone})
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          {incident.reportedAt}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="text-right">
                    <div className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                      Status: <span className="capitalize">{incident.status}</span>
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      ETA: {incident.estimatedResolution}
                    </div>
                  </div>
                </div>

                {/* Description */}
                <p className="text-sm text-gray-700 dark:text-gray-300 mb-3">{incident.description}</p>

                {/* Stats */}
                <div className="flex items-center gap-6 mb-3 text-sm">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                    <span className="text-gray-600 dark:text-gray-400">
                      <strong className="text-gray-900 dark:text-gray-100">{incident.affectedTrains}</strong> trains affected
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <User className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                    <span className="text-gray-600 dark:text-gray-400">Reported by: {incident.reportedBy}</span>
                  </div>
                </div>

                {/* Timeline Updates */}
                <div className="bg-white dark:bg-gray-700/50 rounded-lg p-3 border dark:border-gray-600 transition-colors duration-300">
                  <h4 className="text-xs font-bold text-gray-700 dark:text-gray-300 mb-2 uppercase">Recent Updates</h4>
                  <div className="space-y-2">
                    {incident.updates.map((update, idx) => (
                      <div key={idx} className="flex items-start gap-3">
                        <div className="text-xs text-gray-500 dark:text-gray-400 w-12 flex-shrink-0">{update.time}</div>
                        <div className="flex-1">
                          <div className="text-sm text-gray-800 dark:text-gray-200">{update.message}</div>
                          <div className="text-xs text-gray-500 dark:text-gray-400">by {update.user}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-2 mt-3">
                  <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg font-semibold transition-colors">
                    View Details
                  </button>
                  <button className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm rounded-lg font-semibold transition-colors">
                    Add Update
                  </button>
                  {incident.status === 'active' && (
                    <button className="px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white text-sm rounded-lg font-semibold transition-colors">
                      Mark Resolving
                    </button>
                  )}
                  {incident.status === 'resolving' && (
                    <button className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm rounded-lg font-semibold transition-colors">
                      Mark Resolved
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default IncidentsPage;