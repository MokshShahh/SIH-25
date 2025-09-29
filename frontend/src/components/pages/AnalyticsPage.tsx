import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  BarChart3, TrendingUp, TrendingDown, Calendar, Download,
  Clock, Train, AlertTriangle, CheckCircle, Activity, Filter, Home, ArrowLeft
} from 'lucide-react';

function AnalyticsPage() {
  const navigate = useNavigate();
  const [timeRange, setTimeRange] = useState('today');
  const [selectedZone, setSelectedZone] = useState('all');

  const performanceData = {
    today: {
      onTimePercent: 78,
      avgDelay: 4.2,
      totalTrains: 247,
      incidents: 12,
      peakHourDelay: 6.8,
      trend: '+2.3%'
    },
    week: {
      onTimePercent: 82,
      avgDelay: 3.8,
      totalTrains: 1729,
      incidents: 45,
      peakHourDelay: 5.5,
      trend: '+5.1%'
    },
    month: {
      onTimePercent: 85,
      avgDelay: 3.2,
      totalTrains: 7420,
      incidents: 178,
      peakHourDelay: 4.9,
      trend: '+8.7%'
    }
  };

  const currentData = performanceData[timeRange];

  const zonePerformance = [
    { zone: 'CR', name: 'Central Railway', onTime: 82, trains: 450, avgDelay: 3.5 },
    { zone: 'WR', name: 'Western Railway', onTime: 79, trains: 380, avgDelay: 4.1 },
    { zone: 'SR', name: 'Southern Railway', onTime: 88, trains: 320, avgDelay: 2.8 },
    { zone: 'NR', name: 'Northern Railway', onTime: 75, trains: 410, avgDelay: 5.2 },
    { zone: 'ER', name: 'Eastern Railway', onTime: 81, trains: 290, avgDelay: 3.9 },
  ];

  const hourlyPerformance = [
    { hour: '00:00', trains: 12, onTime: 95, delay: 1.2 },
    { hour: '03:00', trains: 8, onTime: 98, delay: 0.8 },
    { hour: '06:00', trains: 45, onTime: 72, delay: 5.8 },
    { hour: '09:00', trains: 68, onTime: 65, delay: 7.2 },
    { hour: '12:00', trains: 52, onTime: 75, delay: 4.5 },
    { hour: '15:00', trains: 58, onTime: 70, delay: 6.1 },
    { hour: '18:00', trains: 72, onTime: 62, delay: 8.3 },
    { hour: '21:00', trains: 48, onTime: 80, delay: 3.8 },
  ];

  const incidentTypes = [
    { type: 'Signal Failure', count: 24, impact: 'High', avgResolution: '2.5h' },
    { type: 'Track Maintenance', count: 18, impact: 'Medium', avgResolution: '4.0h' },
    { type: 'Weather', count: 15, impact: 'Low', avgResolution: '1.5h' },
    { type: 'Equipment', count: 12, impact: 'Medium', avgResolution: '3.0h' },
    { type: 'Congestion', count: 32, impact: 'High', avgResolution: '1.0h' },
  ];

  return (
    <div className="h-screen bg-gray-50 dark:bg-gray-900 flex flex-col overflow-hidden transition-colors duration-300">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-4 shadow-lg">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <BarChart3 className="w-7 h-7" />
              ANALYTICS & INSIGHTS
            </h1>
            <p className="text-sm text-purple-100 mt-1">Performance metrics and operational analytics</p>
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
            <button className="px-4 py-2 bg-white text-purple-600 rounded-lg font-semibold hover:bg-purple-50 transition-colors flex items-center gap-2">
              <Download className="w-4 h-4" />
              Export Report
            </button>
          </div>
        </div>
      </div>

      {/* Time Range Selector */}
      <div className="bg-white dark:bg-gray-800 border-b dark:border-gray-700 px-6 py-3 flex items-center justify-between transition-colors duration-300">
        <div className="flex items-center gap-4">
          <Calendar className="w-5 h-5 text-gray-500 dark:text-gray-400" />
          <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">Time Range:</span>
          <div className="flex gap-2">
            {[
              { id: 'today', label: 'Today' },
              { id: 'week', label: 'This Week' },
              { id: 'month', label: 'This Month' }
            ].map(range => (
              <button
                key={range.id}
                onClick={() => setTimeRange(range.id)}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  timeRange === range.id
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                }`}
              >
                {range.label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Filter className="w-4 h-4 text-gray-500 dark:text-gray-400" />
          <select 
            value={selectedZone}
            onChange={(e) => setSelectedZone(e.target.value)}
            className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 transition-colors duration-300"
          >
            <option value="all">All Zones</option>
            <option value="cr">Central Railway</option>
            <option value="wr">Western Railway</option>
            <option value="sr">Southern Railway</option>
            <option value="nr">Northern Railway</option>
          </select>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto p-6">
        {/* KPI Cards */}
        <div className="grid grid-cols-4 gap-6 mb-6">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border-l-4 border-green-500 transition-colors duration-300">
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">On-Time Performance</div>
                <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">{currentData.onTimePercent}%</div>
              </div>
              <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-lg">
                <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
              </div>
            </div>
            <div className="flex items-center gap-1 text-sm">
              <TrendingUp className="w-4 h-4 text-green-600 dark:text-green-400" />
              <span className="text-green-600 dark:text-green-400 font-semibold">{currentData.trend}</span>
              <span className="text-gray-500 dark:text-gray-400">vs last period</span>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border-l-4 border-orange-500 transition-colors duration-300">
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Average Delay</div>
                <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">{currentData.avgDelay} min</div>
              </div>
              <div className="p-3 bg-orange-100 dark:bg-orange-900/30 rounded-lg">
                <Clock className="w-6 h-6 text-orange-600 dark:text-orange-400" />
              </div>
            </div>
            <div className="flex items-center gap-1 text-sm">
              <TrendingDown className="w-4 h-4 text-green-600 dark:text-green-400" />
              <span className="text-green-600 dark:text-green-400 font-semibold">-0.8 min</span>
              <span className="text-gray-500 dark:text-gray-400">improvement</span>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border-l-4 border-blue-500 transition-colors duration-300">
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Total Trains</div>
                <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">{currentData.totalTrains}</div>
              </div>
              <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                <Train className="w-6 h-6 text-blue-600 dark:text-blue-400" />
              </div>
            </div>
            <div className="flex items-center gap-1 text-sm">
              <Activity className="w-4 h-4 text-blue-600 dark:text-blue-400" />
              <span className="text-blue-600 dark:text-blue-400 font-semibold">Active</span>
              <span className="text-gray-500 dark:text-gray-400">operations</span>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border-l-4 border-red-500 transition-colors duration-300">
            <div className="flex items-start justify-between mb-3">
              <div>
                <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">Incidents</div>
                <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">{currentData.incidents}</div>
              </div>
              <div className="p-3 bg-red-100 dark:bg-red-900/30 rounded-lg">
                <AlertTriangle className="w-6 h-6 text-red-600 dark:text-red-400" />
              </div>
            </div>
            <div className="flex items-center gap-1 text-sm">
              <TrendingDown className="w-4 h-4 text-green-600 dark:text-green-400" />
              <span className="text-green-600 dark:text-green-400 font-semibold">-15%</span>
              <span className="text-gray-500 dark:text-gray-400">vs last period</span>
            </div>
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-2 gap-6 mb-6">
          {/* Hourly Performance Chart */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 transition-colors duration-300">
            <h3 className="text-lg font-bold text-gray-800 dark:text-gray-100 mb-4">Hourly Performance</h3>
            <div className="space-y-3">
              {hourlyPerformance.map((hour, idx) => (
                <div key={idx} className="flex items-center gap-4">
                  <div className="w-16 text-sm text-gray-600 dark:text-gray-400 font-medium">{hour.hour}</div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-6 relative overflow-hidden">
                        <div 
                          className={`h-full rounded-full transition-all ${
                            hour.onTime >= 80 ? 'bg-green-500' : 
                            hour.onTime >= 70 ? 'bg-orange-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${hour.onTime}%` }}
                        >
                          <span className="absolute inset-0 flex items-center justify-center text-xs font-bold text-white">
                            {hour.onTime}%
                          </span>
                        </div>
                      </div>
                      <div className="text-sm text-gray-500 dark:text-gray-400 w-20">
                        {hour.trains} trains
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Zone Performance */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 transition-colors duration-300">
            <h3 className="text-lg font-bold text-gray-800 dark:text-gray-100 mb-4">Zone Performance</h3>
            <div className="space-y-4">
              {zonePerformance.map((zone, idx) => (
                <div key={idx} className="border-l-4 border-blue-500 pl-4 py-2 bg-gray-50 dark:bg-gray-700/50 rounded transition-colors duration-300">
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <div className="font-bold text-gray-900 dark:text-gray-100">{zone.zone} - {zone.name}</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">{zone.trains} trains operated</div>
                    </div>
                    <div className="text-right">
                      <div className={`text-2xl font-bold ${
                        zone.onTime >= 85 ? 'text-green-600 dark:text-green-400' : 
                        zone.onTime >= 75 ? 'text-orange-600 dark:text-orange-400' : 'text-red-600 dark:text-red-400'
                      }`}>
                        {zone.onTime}%
                      </div>
                      <div className="text-xs text-gray-500 dark:text-gray-400">on-time</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                      <div 
                        className={`h-full rounded-full ${
                          zone.onTime >= 85 ? 'bg-green-500' : 
                          zone.onTime >= 75 ? 'bg-orange-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${zone.onTime}%` }}
                      ></div>
                    </div>
                    <div className="text-sm text-gray-600 dark:text-gray-400">
                      Avg delay: <span className="font-semibold">{zone.avgDelay} min</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Incident Analysis */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 transition-colors duration-300">
          <h3 className="text-lg font-bold text-gray-800 dark:text-gray-100 mb-4">Incident Analysis</h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b-2 border-gray-200 dark:border-gray-700">
                  <th className="text-left py-3 px-4 text-sm font-bold text-gray-700 dark:text-gray-300">Incident Type</th>
                  <th className="text-center py-3 px-4 text-sm font-bold text-gray-700 dark:text-gray-300">Count</th>
                  <th className="text-center py-3 px-4 text-sm font-bold text-gray-700 dark:text-gray-300">Impact</th>
                  <th className="text-center py-3 px-4 text-sm font-bold text-gray-700 dark:text-gray-300">Avg Resolution</th>
                  <th className="text-right py-3 px-4 text-sm font-bold text-gray-700 dark:text-gray-300">Trend</th>
                </tr>
              </thead>
              <tbody>
                {incidentTypes.map((incident, idx) => (
                  <tr key={idx} className="border-b border-gray-100 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors duration-200">
                    <td className="py-4 px-4">
                      <div className="font-semibold text-gray-900 dark:text-gray-100">{incident.type}</div>
                    </td>
                    <td className="text-center py-4 px-4">
                      <span className="px-3 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 rounded-full font-bold">
                        {incident.count}
                      </span>
                    </td>
                    <td className="text-center py-4 px-4">
                      <span className={`px-3 py-1 rounded-full font-semibold ${
                        incident.impact === 'High' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-400' :
                        incident.impact === 'Medium' ? 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-400' :
                        'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400'
                      }`}>
                        {incident.impact}
                      </span>
                    </td>
                    <td className="text-center py-4 px-4 text-gray-700 dark:text-gray-300 font-medium">
                      {incident.avgResolution}
                    </td>
                    <td className="text-right py-4 px-4">
                      <div className="flex items-center justify-end gap-1">
                        <TrendingDown className="w-4 h-4 text-green-600 dark:text-green-400" />
                        <span className="text-green-600 dark:text-green-400 font-semibold">-12%</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Key Insights */}
        <div className="mt-6 grid grid-cols-3 gap-6">
          <div className="bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 border border-green-200 dark:border-green-700 rounded-xl p-6 transition-colors duration-300">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-3 bg-green-500 rounded-lg">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
              <h4 className="font-bold text-gray-900 dark:text-gray-100">Best Performance</h4>
            </div>
            <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
              Southern Railway achieved <strong>88% on-time</strong> performance with lowest average delay of <strong>2.8 minutes</strong>.
            </p>
            <button className="text-sm text-green-700 dark:text-green-400 font-semibold hover:text-green-800 dark:hover:text-green-300">
              View Details →
            </button>
          </div>

          <div className="bg-gradient-to-br from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 border border-orange-200 dark:border-orange-700 rounded-xl p-6 transition-colors duration-300">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-3 bg-orange-500 rounded-lg">
                <Clock className="w-6 h-6 text-white" />
              </div>
              <h4 className="font-bold text-gray-900 dark:text-gray-100">Peak Hour Impact</h4>
            </div>
            <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
              Evening peak (18:00) shows <strong>62% on-time</strong> rate. Consider capacity optimization during this period.
            </p>
            <button className="text-sm text-orange-700 dark:text-orange-400 font-semibold hover:text-orange-800 dark:hover:text-orange-300">
              View Recommendations →
            </button>
          </div>

          <div className="bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border border-blue-200 dark:border-blue-700 rounded-xl p-6 transition-colors duration-300">
            <div className="flex items-center gap-3 mb-3">
              <div className="p-3 bg-blue-500 rounded-lg">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <h4 className="font-bold text-gray-900 dark:text-gray-100">Improvement Trend</h4>
            </div>
            <p className="text-sm text-gray-700 dark:text-gray-300 mb-2">
              Overall performance improved by <strong>2.3%</strong> with incident count reduced by <strong>15%</strong> compared to last period.
            </p>
            <button className="text-sm text-blue-700 dark:text-blue-400 font-semibold hover:text-blue-800 dark:hover:text-blue-300">
              View Trend Analysis →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AnalyticsPage;