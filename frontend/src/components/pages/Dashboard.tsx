import React, { useState, useRef, useEffect, useCallback } from 'react';
import { ZoomIn, ZoomOut, Home, Play, Pause, Zap } from 'lucide-react'; // Added Zap icon
import { NavLink } from 'react-router-dom';
import axios from 'axios';

//deployement commit
const Toast = ({ message, show, onClose }) => {
    useEffect(() => {
        if (show) {
            const timer = setTimeout(() => {
                onClose();
            }, 3000); // Hide after 3 seconds
            return () => clearTimeout(timer);
        }
    }, [show, onClose]);

    if (!show) return null;

    return (
        <div className="fixed top-4 right-4 z-[100] p-4 bg-green-500 text-white rounded-lg shadow-xl transition-opacity duration-300">
            {message}
        </div>
    );
};

function Dashboard() {
  const svgRef = useRef(null);
  const containerRef = useRef(null);
  const [viewBox, setViewBox] = useState({ x: -400, y: -300, width: 800, height: 600 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [stations, setStations] = useState(new Map());
  const [connections, setConnections] = useState([]);
  const [trains, setTrains] = useState([]);
  const [isAnimating, setIsAnimating] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [fetchedData, setFetchedData] = useState([]);
  const [selectedStation, setSelectedStation] = useState(null);
  const[showPopup, setShowPopup] = useState(false)
  const [stationTrains, setStationTrains] = useState({ arrivals: [], departures: [], allTrains: [] }); 
  
  // 🌟 NEW STATE for Toast notification
  const [showToast, setShowToast] = useState(false);

  //ASYNC FUNCTION TO FETCH TRAINS
  const fetchStationTrains = async (stationCode: string) => {
    const backend_url = " https://sih-25-sn32.onrender.com";
    try {
      // NOTE: Assuming stationCode is the actual station code (e.g., 'DADAR')
      const response = await axios.get(`${backend_url}/trains/station/${stationCode}`);
      
      const allTrains = response.data.trains || [];
      
      // Filter the trains into arrivals and departures based on times
      const categorizedTrains = allTrains.map(train => {
        // Assuming the query returns only one entry per train for the specified station
        const arrivalTime = train.arrival_times[0];
        const departureTime = train.departure_times[0];
        
        let type = '';
        if (arrivalTime !== '00:00:00' && departureTime !== '00:00:00' && arrivalTime !== departureTime) {
          type = 'Stop'; // Arrives and departs
        } else if (arrivalTime === '00:00:00' || arrivalTime === departureTime) {
          type = 'Departure'; // Starts here or is a pass-through with no explicit arrival
        } else if (departureTime === '00:00:00' || arrivalTime !== departureTime) {
          type = 'Arrival'; // Terminates here or is a stop with no explicit departure (unlikely)
        } else {
          type = 'Pass-Through';
        }
        
        return {
          ...train,
          type,
          arrival: arrivalTime,
          departure: departureTime
        };
      });

      setStationTrains({
        arrivals: categorizedTrains.filter(t => t.type === 'Arrival' || t.type === 'Stop').sort((a, b) => a.arrival.localeCompare(b.arrival)),
        departures: categorizedTrains.filter(t => t.type === 'Departure' || t.type === 'Stop').sort((a, b) => a.departure.localeCompare(b.departure)),
        allTrains: categorizedTrains
      });
      
    } catch (error) {
      console.error("Error fetching station trains:", error);
      setStationTrains({ arrivals: [], departures: [], allTrains: [] });
    }
  };

  // Smart positioning algorithm for better station layout
  const processData = useCallback((data) => {
    const stationMap = new Map();
    const connectionList = [];
    
    // First pass: collect all stations and connections
    data.forEach(item => {
      if (item.p && item.p.length === 3) {
        const [origin, relation, destination] = item.p;
        
        if (relation === 'CONNECTS_TO' || relation === 'TRACK') {
          console.log(origin, destination);
          const originKey = `${origin.city}-${origin.name}`;
          const destKey = `${destination.city}-${destination.name}`;
          
          if (!stationMap.has(originKey)) {
            stationMap.set(originKey, {
              ...origin,
              id: originKey,
              connections: []
            });
          }
          
          if (!stationMap.has(destKey)) {
            stationMap.set(destKey, {
              ...destination,
              id: destKey,
              connections: []
            });
          }
          
          connectionList.push({
            from: originKey,
            to: destKey,
            id: `${originKey}-${destKey}`
          });
          
          // Track connections for positioning
          stationMap.get(originKey).connections.push(destKey);
          stationMap.get(destKey).connections.push(originKey);
        }
      }
    });
    
    // Smart positioning algorithm
    const positionStations = () => {
      const stations = Array.from(stationMap.values());
      const cityGroups = {};
      
      // Group stations by city
      stations.forEach(station => {
        if (!cityGroups[station.city]) {
          cityGroups[station.city] = [];
        }
        cityGroups[station.city].push(station);
      });
      
      // Position cities in a larger circular layout for better visibility
      const cities = Object.keys(cityGroups);
      const cityPositions = {};
      const radius = 400; // Increased radius for better spacing
      
      cities.forEach((city, index) => {
        const angle = (index * 2 * Math.PI) / cities.length;
        cityPositions[city] = {
          x: Math.cos(angle) * radius,
          y: Math.sin(angle) * radius
        };
      });
      
      // Position stations within each city with better spacing
      Object.entries(cityGroups).forEach(([city, cityStations]) => {
        const cityPos = cityPositions[city];
        
        if (cityStations.length === 1) {
          cityStations[0].x = cityPos.x;
          cityStations[0].y = cityPos.y;
        } else {
          // Create a circular arrangement for multiple stations in same city
          const stationRadius = Math.max(30, cityStations.length * 8);
          cityStations.forEach((station, index) => {
            const angle = (index * 2 * Math.PI) / cityStations.length;
            station.x = cityPos.x + Math.cos(angle) * stationRadius;
            station.y = cityPos.y + Math.sin(angle) * stationRadius;
          });
        }
      });
      
      // Apply force-directed positioning for better layout
      for (let i = 0; i < 150; i++) {
        stations.forEach(station => {
          let fx = 0, fy = 0;
          
          // Repulsion from other stations
          stations.forEach(other => {
            if (station.id !== other.id) {
              const dx = station.x - other.x;
              const dy = station.y - other.y;
              const dist = Math.sqrt(dx * dx + dy * dy) || 1;
              if (dist < 200) { // Increased minimum distance
                const force = 100000 / (dist * dist);
                fx += (dx / dist) * force;
                fy += (dy / dist) * force;
              }
            }
          });
          
          // Attraction to connected stations (weaker force)
          station.connections.forEach(connId => {
            const connected = stationMap.get(connId);
            if (connected) {
              const dx = connected.x - station.x;
              const dy = connected.y - station.y;
              const dist = Math.sqrt(dx * dx + dy * dy) || 1;
              const force = Math.min(dist / 300, 0.8);
              fx += (dx / dist) * force * 1.5;
              fy += (dy / dist) * force * 1.5;
            }
          });
          
          station.x += fx * 0.08;
          station.y += fy * 0.08;
        });
      }
    };
    
    positionStations();
    setStations(stationMap);
    setConnections(connectionList);
    
    // Create trains for animation
    const trainList = connectionList.map((conn, index) => ({
      id: `train-${index}`,
      connectionId: conn.id,
      progress: Math.random(),
      speed: 0.003 + Math.random() * 0.007,
      direction: Math.random() > 0.5 ? 'forward' : 'backward'
    }));
    
    setTrains(trainList);
  }, []);

  // Handle backend data fetching
  useEffect(() => {
    const backend_url = " https://sih-25-sn32.onrender.com"
    axios.get(`${backend_url}/stations/map`)
      .then(response => {
        setFetchedData(response.data.stations);
        setIsLoading(false);
      })
      .catch(error => {
        console.error('Error fetching data:', error);
        setIsLoading(false);
      });
    
    setIsLoading(false);
  }, []);

  useEffect(() => {
    if (fetchedData.length > 0) {
      processData(fetchedData);
    }
  }, [fetchedData, processData]);

  // Animation loop
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
  
  // Assigns color based on the first letter of the station name
  const getStationColor = (stationType, stationName) => {
    if (!stationName) return '#9ca3af'; 

    const firstLetter = stationName.charAt(0).toUpperCase();

    if (firstLetter >= 'A' && firstLetter <= 'I') {
      return '#2563eb'; // Blue (A-I)
    } else if (firstLetter >= 'J' && firstLetter <= 'R') {
      return '#dc2626'; // Red (J-R)
    } else if (firstLetter >= 'S' && firstLetter <= 'Z') {
      return '#059669'; // Green (S-Z)
    } else {
      return '#f59e0b'; // Amber/Orange for numbers/symbols/other
    }
  };

  // 🌟 NEW HANDLER for Optimize button click
  const handleOptimizeClick = () => {
    console.log(`Optimizing station: ${selectedStation.name}`);
    setShowToast(true);
    // You could add an API call here to actually optimize the station
  };

  const handleMouseDown = (e) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const handleMouseMove = (e) => {
    if (!isDragging) return;
    
    const dx = (e.clientX - dragStart.x) * (viewBox.width / 800);
    const dy = (e.clientY - dragStart.y) * (viewBox.height / 600);
    
    setViewBox(prev => ({
      ...prev,
      x: prev.x - dx,
      y: prev.y - dy
    }));
    
    setDragStart({ x: e.clientX, y: e.clientY });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

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
      y: svgY - (mouseY / 600) * newWidth,
      width: newWidth,
      height: newHeight
    });
  };

  const resetView = () => {
    setViewBox({ x: -400, y: -300, width: 800, height: 600 });
  };

  const zoomIn = () => {
    setViewBox(prev => ({
      x: prev.x + prev.width * 0.1,
      y: prev.y + prev.height * 0.1,
      width: prev.width * 0.8,
      height: prev.height * 0.8
    }));
  };

  const zoomOut = () => {
    setViewBox(prev => ({
      x: prev.x - prev.width * 0.125,
      y: prev.y - prev.height * 0.125,
      width: prev.width * 1.25,
      height: prev.height * 1.25
    }));
  };

  const getTrainPosition = (train) => {
    const connection = connections.find(c => c.id === train.connectionId);
    if (!connection) return { x: 0, y: 0 };
    
    const fromStation = stations.get(connection.from);
    const toStation = stations.get(connection.to);
    
    if (!fromStation || !toStation) return { x: 0, y: 0 };
    
    let progress = train.progress;
    if (train.direction === 'backward') {
      progress = 1 - progress;
    }
    
    const x = fromStation.x + (toStation.x - fromStation.x) * progress;
    const y = fromStation.y + (toStation.y - fromStation.y) * progress;
    
    return { x, y };
  };

const handleStationClick = (station) => {
    setSelectedStation(station);
    fetchStationTrains(station.name); 
    setShowPopup(true);
  };

  const getStationTrains = (stationId) => {
    const arrivals = [];
    const departures = [];
    
    connections.forEach(conn => {
      if (conn.from === stationId) {
        departures.push({
          to: stations.get(conn.to)?.name,
          city: stations.get(conn.to)?.city,
          type: 'Departure'
        });
      }
      if (conn.to === stationId) {
        arrivals.push({
          from: stations.get(conn.from)?.name,
          city: stations.get(conn.from)?.city,
          type: 'Arrival'
        });
      }
    });
    
    return { arrivals, departures };
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen w-full bg-gray-50 text-gray-700">
        <svg className="animate-spin h-8 w-8 text-gray-600 mr-3" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" className="opacity-25"></circle>
          <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" className="opacity-75"></path>
        </svg>
        <p>Loading network data...</p>
      </div>
    );
  }

  return (
    <div className="h-screen w-full bg-gray-50 flex flex-col">
      <Toast 
        message={`${selectedStation?.name} is now optimized! 🚀`} 
        show={showToast} 
        onClose={() => setShowToast(false)} 
      />
      {/* Navbar */}
      <div className="bg-white text-gray-800 px-6 py-4 shadow-lg border-b flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-700">Train Network Dashboard</h1>
        <NavLink 
          to="/" 
          className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
        >
          Home
        </NavLink>
      </div>
      
      {/* Controls */}
      <div className="bg-white px-6 py-2 flex items-center justify-between border-b border-gray-200 shadow-sm">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setIsAnimating(!isAnimating)}
            className="flex items-center space-x-2 px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors shadow-md"
          >
            {isAnimating ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            <span>{isAnimating ? 'Pause' : 'Start'} Animation</span>
          </button>
          
          <div className="text-sm text-gray-600 font-medium">
            Stations: {stations.size} | Connections: {connections.length} | Trains: {trains.length}
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <button onClick={zoomIn} className="p-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded border shadow-sm">
            <ZoomIn className="w-4 h-4" />
          </button>
          <button onClick={zoomOut} className="p-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded border shadow-sm">
            <ZoomOut className="w-4 h-4" />
          </button>
          <button onClick={resetView} className="p-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded border shadow-sm">
            <Home className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      {/* Legend - Updated to reflect the alphabetical coloring scheme */}
      <div className="bg-white px-6 py-2 flex items-center space-x-6 text-sm text-gray-700 border-b border-gray-200 shadow-sm">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded-full bg-blue-600"></div>
          <span>Interstate (Blue)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded-full bg-red-500"></div>
          <span>Terminal (Red)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded-full bg-green-600"></div>
          <span>Local (Green)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-orange-400"></div>
          <span>Trains</span>
        </div>
        <div className="text-xs text-gray-500 italic ml-4">
          Click on any station for details
        </div>
      </div>
      
      {/* Main Canvas */}
      <div 
        ref={containerRef}
        className="flex-1 overflow-hidden cursor-move bg-gray-50"
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
          className="w-full h-full"
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
          
          {/* Dotted Background */}
          <rect x={viewBox.x} y={viewBox.y} width={viewBox.width} height={viewBox.height} fill="url(#dots)" />
          
          {/* Connections */}
          {connections.map(connection => {
            const fromStation = stations.get(connection.from);
            const toStation = stations.get(connection.to);
            
            if (!fromStation || !toStation) return null;
            
            return (
              <g key={connection.id}>
                <line
                  x1={fromStation.x}
                  y1={fromStation.y}
                  x2={toStation.x}
                  y2={toStation.y}
                  stroke="#6b7280"
                  strokeWidth="3"
                  opacity="0.7"
                />
                {/* Direction arrow */}
                <polygon
                  points={`${toStation.x - 10},${toStation.y - 5} ${toStation.x - 10},${toStation.y + 5} ${toStation.x - 2},${toStation.y}`}
                  fill="#9ca3af"
                  opacity="0.8"
                  transform={`rotate(${Math.atan2(toStation.y - fromStation.y, toStation.x - fromStation.x) * 180 / Math.PI}, ${toStation.x - 6}, ${toStation.y})`}
                />
              </g>
            );
          })}
          
          {/* Trains */}
          {isAnimating && trains.map(train => {
            const pos = getTrainPosition(train);
            return (
              <g key={train.id}>
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r="5"
                  fill="#f97316"
                  filter="url(#glow)"
                />
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r="3"
                  fill="#ea580c"
                />
              </g>
            );
          })}
          
          {/* Stations */}
          {Array.from(stations.values()).map(station => (
            <g key={station.id}>
              {/* Station glow */}
              <circle
                cx={station.x}
                cy={station.y}
                r="15"
                // 🌟 Passing station.name to determine the color
                fill={getStationColor(station.type, station.name)} 
                opacity="0.2"
                filter="url(#glow)"
              />
              {/* Station circle */}
              <circle
                cx={station.x}
                cy={station.y}
                r="10"
                // 🌟 Passing station.name to determine the color
                fill={getStationColor(station.type, station.name)}
                stroke="#ffffff"
                strokeWidth="2"
                className="cursor-pointer hover:r-12 transition-all"
                onClick={() => handleStationClick(station)}
              />
              {/* Station label */}
              <text
                x={station.x}
                y={station.y - 20}
                textAnchor="middle"
                className="text-sm fill-gray-800 font-semibold pointer-events-none"
                style={{ fontSize: Math.max(10, 14 * (800 / viewBox.width)) }}
              >
                {station.name}
              </text>
              <text
                x={station.x}
                y={station.y + 30}
                textAnchor="middle"
                className="text-xs fill-gray-600 pointer-events-none"
                style={{ fontSize: Math.max(8, 11 * (800 / viewBox.width)) }}
              >
                {station.city}
              </text>
            </g>
          ))}
        </svg>
      </div>
      
      {/* Status Bar */}
      <div className="bg-white px-6 py-2 text-xs text-gray-600 border-t border-gray-200 shadow-sm">
        Zoom: {(800 / viewBox.width * 100).toFixed(0)}% | 
        View: ({viewBox.x.toFixed(0)}, {viewBox.y.toFixed(0)}) | 
        Animation: {isAnimating ? 'Running' : 'Paused'}
      </div>

      {/* Station Details Popup */}
      {showPopup && selectedStation && (
        <div className="fixed inset-0 bg-black/45 flex items-center justify-center z-50">
          {/* 🌟 MODIFIED: max-w-lg for bigger size and max-h increased */}
          <div className="bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[500px] overflow-hidden">
            
            {/* 🌟 MODIFIED HEADER: Added Optimize Button */}
            <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-4 flex justify-between items-center">
              <div>
                <h3 className="text-lg font-bold">{selectedStation.name}</h3>
                <p className="text-sm text-blue-100">{selectedStation.city} • {selectedStation.type}</p>
              </div>
              <div className="flex items-center space-x-3">
                {/* Optimize Button */}
                <button
                  onClick={handleOptimizeClick}
                  className="flex items-center space-x-1 px-3 py-1 bg-green-500 hover:bg-green-600 text-white rounded-lg transition-colors text-sm font-semibold shadow-md"
                >
                  <Zap className="w-4 h-4" />
                  <span>Optimize</span>
                </button>
                {/* Close Button */}
                <button 
                  onClick={() => setShowPopup(false)}
                  className="text-blue-100 hover:text-white text-2xl font-bold w-8 h-8 flex items-center justify-center rounded hover:bg-blue-500 transition-colors"
                >
                  ×
                </button>
              </div>
            </div>

            {/* Popup Content */}
            {/* 🌟 MODIFIED: max-h-96 for more content space */}
            <div className="p-6 overflow-y-auto max-h-96"> 
              {stationTrains.allTrains.length === 0 ? (
                <div className="text-center p-8 text-gray-500">
                  Loading train schedule...
                </div>
              ) : (
                <div className="space-y-4">
                  
                  {/* Station Stats - UPDATED with total count */}
                  <div className="bg-gray-100 p-4 rounded-lg">
                    <h4 className="text-sm font-semibold text-gray-800 mb-3">Station Information</h4>
                    <div className="grid grid-cols-2 gap-3 text-xs">
                      <div className="bg-white p-2 rounded">
                        <span className="text-gray-600">Type:</span>
                        <span className="ml-1 font-medium text-gray-800">{selectedStation.type}</span>
                      </div>
                      <div className="bg-white p-2 rounded">
                        <span className="text-gray-600">City:</span>
                        <span className="ml-1 font-medium text-gray-800">{selectedStation.city}</span>
                      </div>
                      <div className="bg-white p-2 rounded">
                        <span className="text-gray-600">Total Trains:</span>
                        <span className="ml-1 font-medium text-blue-600">{stationTrains.allTrains.length}</span>
                      </div>
                      <div className="bg-white p-2 rounded">
                        <span className="text-gray-600">Status:</span>
                        <span className="ml-1 font-medium text-green-600">Active</span>
                      </div>
                    </div>
                  </div>

                  {/* Arrivals and Departures */}
                  <div className="grid grid-cols-2 gap-4">
                    
                    {/* Departures Column */}
                    <div>
                      <h4 className="text-md font-semibold text-gray-800 mb-3 flex items-center">
                        <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
                        Departures ({stationTrains.departures.length})
                      </h4>
                      {stationTrains.departures.length > 0 ? (
                        // 🌟 MODIFIED: Increased max-h for scrollable list
                        <div className="space-y-2 max-h-60 overflow-y-auto pr-2"> 
                          {stationTrains.departures.map((train) => (
                            <div key={train.train_id} className="bg-green-50 p-3 rounded-lg border-l-4 border-green-500">
                              <div className="text-sm font-medium text-gray-800">{train.train_name} ({train.train_id})</div>
                              <div className="text-xs text-gray-600 mt-1">
                                Departs: <span className="font-semibold">{train.departure}</span>
                                {train.type === 'Stop' ? ` (Arr: ${train.arrival})` : ''}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-gray-500 italic bg-gray-50 p-3 rounded">No departures scheduled</p>
                      )}
                    </div>

                    {/* Arrivals Column */}
                    <div>
                      <h4 className="text-md font-semibold text-gray-800 mb-3 flex items-center">
                        <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
                        Arrivals ({stationTrains.arrivals.length})
                      </h4>
                      {stationTrains.arrivals.length > 0 ? (
                         // 🌟 MODIFIED: Increased max-h for scrollable list
                        <div className="space-y-2 max-h-60 overflow-y-auto pr-2">
                          {stationTrains.arrivals.map((train) => (
                            <div key={train.train_id} className="bg-blue-50 p-3 rounded-lg border-l-4 border-blue-500">
                              <div className="text-sm font-medium text-gray-800">{train.train_name} ({train.train_id})</div>
                              <div className="text-xs text-gray-600 mt-1">
                                Arrives: <span className="font-semibold">{train.arrival}</span>
                                {train.type === 'Stop' ? ` (Dep: ${train.departure})` : ''}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-gray-500 italic bg-gray-50 p-3 rounded">No arrivals scheduled</p>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Popup Footer */}
            <div className="bg-gray-50 px-6 py-3 flex justify-end border-t">
              <button 
                onClick={() => setShowPopup(false)}
                className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors"
              >
                Close
              </button>
            </div>
            
          </div>
        </div> 
      )} 
    </div>
  );
}

export default Dashboard;