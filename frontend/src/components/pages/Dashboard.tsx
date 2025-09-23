import React, { useState, useRef, useEffect, useCallback } from 'react';
import { ZoomIn, ZoomOut, Home, Play, Pause, RotateCcw } from 'lucide-react';
import axios from 'axios';

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
  const [isLoading, setIsLoading] = useState(true);
  const [fetchedData, setFetchedData] = useState([]);

  const processData = useCallback((data) => {
    const stationMap = new Map();
    const connectionList = [];
    
    data.forEach(item => {
      if (item.p && item.p.length === 3) {
        const [origin, relation, destination] = item.p;
        
        if (relation === 'TRACK') {
          const originKey = `${origin.city}-${origin.name}`;
          const destKey = `${destination.city}-${destination.name}`;
          
          if (!stationMap.has(originKey)) {
            stationMap.set(originKey, {
              ...origin,
              id: originKey,
              x: Math.random() * 600 - 300,
              y: Math.random() * 400 - 200
            });
          }
          
          if (!stationMap.has(destKey)) {
            stationMap.set(destKey, {
              ...destination,
              id: destKey,
              x: Math.random() * 600 - 300,
              y: Math.random() * 400 - 200
            });
          }
          
          connectionList.push({
            from: originKey,
            to: destKey,
            id: `${originKey}-${destKey}`
          });
        }
      }
    });
    
    setStations(stationMap);
    setConnections(connectionList);
    
    const trainList = connectionList.map((conn, index) => ({
      id: `train-${index}`,
      connectionId: conn.id,
      progress: Math.random(),
      speed: 0.005 + Math.random() * 0.01
    }));
    
    setTrains(trainList);
  }, []);

  useEffect(() => {
    const backend_url = "http://127.0.0.1:8000"
    axios.get(`${backend_url}/stations/map`)
      .then(response => {
        setFetchedData(response.data.stations);
        setIsLoading(false);
      })
      .catch(error => {
        console.error('Error fetching data:', error);
        setIsLoading(false);
      });
  }, []);

  useEffect(() => {
    if (fetchedData.length > 0) {
      processData(fetchedData);
    }
  }, [fetchedData, processData]);

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

  const getStationColor = (type) => {
    switch (type) {
      case 'Interstate': return '#2563eb'; 
      case 'Terminal': return '#dc2626';     
      case 'Local': return '#059669';     
      default: return '#6b7280';          
    }
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
      y: svgY - (mouseY / 600) * newHeight,
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
    
    const x = fromStation.x + (toStation.x - fromStation.x) * train.progress;
    const y = fromStation.y + (toStation.y - fromStation.y) * train.progress;
    
    return { x, y };
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
      <div className="bg-white text-gray-800 px-6 py-4 shadow-lg border-b">
        <h1 className="text-2xl font-bold text-gray-700">Train Network Dashboard</h1>
      </div>
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
      
      <div className="bg-white px-6 py-2 flex items-center space-x-6 text-sm text-gray-700 border-b border-gray-200 shadow-sm">
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded-full bg-blue-600"></div>
          <span>Interstate</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded-full bg-red-500"></div>
          <span>Terminal</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 rounded-full bg-green-600"></div>
          <span>Local</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-3 h-3 bg-orange-400"></div>
          <span>Trains</span>
        </div>
      </div>
      
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
          
          <rect x={viewBox.x} y={viewBox.y} width={viewBox.width} height={viewBox.height} fill="url(#dots)" />
          
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
                  strokeWidth="2"
                  opacity="0.8"
                />
                <polygon
                  points={`${toStation.x - 8},${toStation.y - 4} ${toStation.x - 8},${toStation.y + 4} ${toStation.x - 2},${toStation.y}`}
                  fill="#9ca3af"
                  opacity="0.8"
                  transform={`rotate(${Math.atan2(toStation.y - fromStation.y, toStation.x - fromStation.x) * 180 / Math.PI}, ${toStation.x - 5}, ${toStation.y})`}
                />
              </g>
            );
          })}
          
          {isAnimating && trains.map(train => {
            const pos = getTrainPosition(train);
            return (
              <g key={train.id}>
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r="4"
                  fill="#f97316"
                  filter="url(#glow)"
                />
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r="2"
                  fill="#ea580c"
                />
              </g>
            );
          })}
          
          {Array.from(stations.values()).map(station => (
            <g key={station.id}>
              <circle
                cx={station.x}
                cy={station.y}
                r="12"
                fill={getStationColor(station.type)}
                opacity="0.3"
                filter="url(#glow)"
              />
              <circle
                cx={station.x}
                cy={station.y}
                r="8"
                fill={getStationColor(station.type)}
                stroke="#ffffff"
                strokeWidth="2"
                className="cursor-pointer hover:r-10 transition-all"
              />
              <text
                x={station.x}
                y={station.y - 15}
                textAnchor="middle"
                className="text-xs fill-gray-800 font-semibold pointer-events-none"
                style={{ fontSize: Math.max(8, 12 * (800 / viewBox.width)) }}
              >
                {station.name}
              </text>
              <text
                x={station.x}
                y={station.y + 25}
                textAnchor="middle"
                className="text-xs fill-gray-600 pointer-events-none"
                style={{ fontSize: Math.max(6, 10 * (800 / viewBox.width)) }}
              >
                {station.city}
              </text>
            </g>
          ))}
        </svg>
      </div>
      
      <div className="bg-white px-6 py-2 text-xs text-gray-600 border-t border-gray-200 shadow-sm">
        Zoom: {(800 / viewBox.width * 100).toFixed(0)}% | 
        View: ({viewBox.x.toFixed(0)}, {viewBox.y.toFixed(0)}) | 
        Animation: {isAnimating ? 'Running' : 'Paused'}
      </div>
    </div>
  );
}

export default Dashboard;
