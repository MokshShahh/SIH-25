import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { Play, Pause, RotateCcw, Train, MapPin, Clock } from 'lucide-react';

const MumbaiLocal = () => {
  const [isSimulationRunning, setIsSimulationRunning] = useState(false);
  const [trains, setTrains] = useState([]);
  const [selectedStation, setSelectedStation] = useState(null);
  const [showStationModal, setShowStationModal] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());

  // Mumbai Local Lines Data with better spacing
  const lines = {
    western: {
      name: 'Western Line',
      color: '#e11d48',
      yOffset: 100,
      stations: [
        { id: 'CCG', name: 'Churchgate', x: 100, isTerminal: true },
        { id: 'MRN', name: 'Marine Lines', x: 200 },
        { id: 'CST', name: 'Charni Road', x: 300 },
        { id: 'GRD', name: 'Grant Road', x: 400 },
        { id: 'BCT', name: 'Mumbai Central', x: 500, isJunction: true },
        { id: 'LPR', name: 'Lower Parel', x: 600 },
        { id: 'EPH', name: 'Elphinstone', x: 700 },
        // Dadar junction will be handled separately
        { id: 'MHM', name: 'Matunga', x: 900 },
        { id: 'MHG', name: 'Mahim', x: 1000 },
        { id: 'BVI', name: 'Bandra', x: 1100, isJunction: true },
        { id: 'KHR', name: 'Khar', x: 1200 },
        { id: 'STR', name: 'Santacruz', x: 1300 },
        { id: 'VLE', name: 'Vile Parle', x: 1400 },
        { id: 'ADH', name: 'Andheri', x: 1500, isJunction: true },
        { id: 'JVP', name: 'Jogeshwari', x: 1600 },
        { id: 'RAM', name: 'Ram Mandir', x: 1700 },
        { id: 'GRG', name: 'Goregaon', x: 1800 },
        { id: 'MLV', name: 'Malad', x: 1900 },
        { id: 'KDV', name: 'Kandivali', x: 2000 },
        { id: 'BOR', name: 'Borivali', x: 2100, isJunction: true },
        { id: 'DHN', name: 'Dahisar', x: 2200 },
        { id: 'MRA', name: 'Mira Road', x: 2300 },
        { id: 'BHP', name: 'Bhayander', x: 2400 },
        { id: 'NLN', name: 'Naigaon', x: 2500 },
        { id: 'VSV', name: 'Vasai Road', x: 2600, isJunction: true },
        { id: 'NLU', name: 'Nallasopara', x: 2700 },
        { id: 'VLJ', name: 'Virar', x: 2800, isTerminal: true }
      ]
    },
    central: {
      name: 'Central Line',
      color: '#1d4ed8',
      yOffset: 300,
      stations: [
        // CSMT junction will be handled separately
        { id: 'MJD', name: 'Masjid', x: 200 },
        { id: 'SNH', name: 'Sandhurst Road', x: 300 },
        { id: 'CYR', name: 'Currey Road', x: 400 },
        { id: 'PRL', name: 'Parel', x: 500 },
        // Dadar junction will be handled separately
        { id: 'MTN', name: 'Matunga', x: 900 },
        { id: 'SIU', name: 'Sion', x: 1000 },
        { id: 'KRL', name: 'Kurla', x: 1100, isJunction: true },
        { id: 'VDR', name: 'Vidyavihar', x: 1200 },
        { id: 'GHT', name: 'Ghatkopar', x: 1300, isJunction: true },
        { id: 'VKH', name: 'Vikhroli', x: 1400 },
        { id: 'KJV', name: 'Kanjurmarg', x: 1500 },
        { id: 'BHD', name: 'Bhandup', x: 1600 },
        { id: 'NHV', name: 'Nahur', x: 1700 },
        { id: 'MLD', name: 'Mulund', x: 1800 },
        { id: 'THN', name: 'Thane', x: 1900, isJunction: true },
        { id: 'KLY', name: 'Kalyan', x: 2000, isJunction: true },
        { id: 'VTN', name: 'Vithalwadi', x: 2100 },
        { id: 'ULH', name: 'Ulhasnagar', x: 2200 },
        { id: 'ATG', name: 'Ambernath', x: 2300 },
        { id: 'BDL', name: 'Badlapur', x: 2400 },
        { id: 'VGL', name: 'Vangani', x: 2500 },
        { id: 'SYN', name: 'Shelu', x: 2600 },
        { id: 'NRL', name: 'Neral', x: 2700 },
        { id: 'BHP_C', name: 'Bhivpuri', x: 2800 },
        { id: 'KJT', name: 'Karjat', x: 2900, isTerminal: true }
      ]
    },
    harbour: {
      name: 'Harbour Line',
      color: '#059669',
      yOffset: 500,
      stations: [
        // CSMT junction will be handled separately
        { id: 'MJD_H', name: 'Masjid', x: 200 },
        { id: 'SNH_H', name: 'Sandhurst Road', x: 300 },
        { id: 'DKY', name: 'Dockyard Road', x: 400 },
        { id: 'RBY', name: 'Reay Road', x: 500 },
        { id: 'CTN', name: 'Cotton Green', x: 600 },
        { id: 'SWR', name: 'Sewri', x: 700 },
        { id: 'WDN', name: 'Wadala Road', x: 800 },
        { id: 'GTB', name: 'GTB Nagar', x: 900 },
        { id: 'CHB', name: 'Chunabhatti', x: 1000 },
        { id: 'KRL_H', name: 'Kurla', x: 1100, isJunction: true },
        { id: 'TVR', name: 'Tilak Nagar', x: 1200 },
        { id: 'CHG', name: 'Chembur', x: 1300 },
        { id: 'GVN', name: 'Govandi', x: 1400 },
        { id: 'MNK', name: 'Mankhurd', x: 1500 },
        { id: 'VAS', name: 'Vashi', x: 1600, isJunction: true },
        { id: 'SPD', name: 'Sanpada', x: 1700 },
        { id: 'JPN', name: 'Juinagar', x: 1800 },
        { id: 'NRL_H', name: 'Nerul', x: 1900 },
        { id: 'SWD', name: 'Seawoods', x: 2000 },
        { id: 'BLP', name: 'Belapur', x: 2100 },
        { id: 'KHG', name: 'Kharghar', x: 2200 },
        { id: 'MNS', name: 'Mansarovar', x: 2300 },
        { id: 'KHD', name: 'Khandeshwar', x: 2400 },
        { id: 'PRB', name: 'Panvel', x: 2500, isTerminal: true }
      ]
    }
  };

  // Shared junction stations with 45-degree connections
  const junctionStations = [
    {
      id: 'CSMT',
      name: 'CSMT',
      x: 100,
      y: 400, // Center between Central (300) and Harbour (500)
      isTerminal: true,
      isShared: true,
      connectedLines: [
        { line: 'central', yOffset: 300, connectionAngle: -45 },
        { line: 'harbour', yOffset: 500, connectionAngle: 45 }
      ]
    },
    {
      id: 'DDR',
      name: 'Dadar',
      x: 800,
      y: 200, // Center between Western (100) and Central (300)
      isJunction: true,
      isShared: true,
      connectedLines: [
        { line: 'western', yOffset: 100, connectionAngle: -45 },
        { line: 'central', yOffset: 300, connectionAngle: 45 }
      ]
    }
  ];

  // Generate trains for simulation
  const generateTrains = () => {
    const allTrains = [];
    
    Object.entries(lines).forEach(([lineKey, line]) => {
      // Up trains (towards terminals)
      for (let i = 0; i < 2; i++) {
        allTrains.push({
          id: `${lineKey}_up_${i}`,
          line: lineKey,
          direction: 'up',
          position: Math.random() * 2900,
          speed: 1.5 + Math.random() * 1.5,
          trainNumber: `${lineKey.charAt(0).toUpperCase()}${String(i + 1).padStart(2, '0')}`,
          nextStation: ''
        });
      }
      
      // Down trains (from terminals)
      for (let i = 0; i < 2; i++) {
        allTrains.push({
          id: `${lineKey}_down_${i}`,
          line: lineKey,
          direction: 'down',
          position: Math.random() * 2900,
          speed: 1.5 + Math.random() * 1.5,
          trainNumber: `${lineKey.charAt(0).toUpperCase()}${String(i + 3).padStart(2, '0')}`,
          nextStation: ''
        });
      }
    });
    
    setTrains(allTrains);
  };

  // Update train positions
  useEffect(() => {
    if (isSimulationRunning) {
      const interval = setInterval(() => {
        setTrains(prevTrains => 
          prevTrains.map(train => {
            let newPosition = train.position;
            const maxPosition = train.line === 'central' ? 2900 : train.line === 'harbour' ? 2500 : 2800;
            
            if (train.direction === 'up') {
              newPosition += train.speed;
              if (newPosition > maxPosition) newPosition = 100;
            } else {
              newPosition -= train.speed;
              if (newPosition < 100) newPosition = maxPosition;
            }
            
            // Find next station
            const line = lines[train.line];
            const allStations = [...line.stations, ...junctionStations.filter(s => 
              s.connectedLines.some(conn => conn.line === train.line)
            )];
            const nextStation = allStations.find(station => 
              train.direction === 'up' ? station.x > newPosition : station.x < newPosition
            );
            
            return {
              ...train,
              position: newPosition,
              nextStation: nextStation ? nextStation.name : 'Terminal'
            };
          })
        );
      }, 150);
      
      return () => clearInterval(interval);
    }
  }, [isSimulationRunning]);

  // Update current time
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  // Initialize trains on component mount
  useEffect(() => {
    generateTrains();
  }, []);

  const handleStationClick = (station, lineKey) => {
    setSelectedStation({ ...station, line: lineKey });
    setShowStationModal(true);
  };

  // Line Component with dual tracks and proper junction routing
  const LineComponent = ({ lineKey, line }) => {
    const junctionPoints = junctionStations.filter(junction => 
      junction.connectedLines.some(conn => conn.line === lineKey)
    );

    return (
      <g key={lineKey}>
        {/* Dual track lines with junction routing */}
        <g>
          {/* Handle CSMT junction for Central and Harbour lines */}
          {(lineKey === 'central' || lineKey === 'harbour') && (
            <g key="csmt-junction-tracks">
              {/* 45-degree connection to CSMT - Up track */}
              <line
                x1={50}
                y1={line.yOffset - 15}
                x2={90}
                y2={400 - 10}
                stroke={line.color}
                strokeWidth="4"
                opacity="0.8"
              />
              
              {/* 45-degree connection to CSMT - Down track */}
              <line
                x1={50}
                y1={line.yOffset + 15}
                x2={90}
                y2={400 + 10}
                stroke={line.color}
                strokeWidth="4"
                opacity="0.8"
              />
              
              {/* 45-degree connection from CSMT - Up track */}
              <line
                x1={110}
                y1={400 - 10}
                x2={150}
                y2={line.yOffset - 15}
                stroke={line.color}
                strokeWidth="4"
                opacity="0.8"
              />
              
              {/* 45-degree connection from CSMT - Down track */}
              <line
                x1={110}
                y1={400 + 10}
                x2={150}
                y2={line.yOffset + 15}
                stroke={line.color}
                strokeWidth="4"
                opacity="0.8"
              />
            </g>
          )}
          
          {/* Regular track segments */}
          {line.stations.map((station, index) => {
            const nextStation = line.stations[index + 1];
            if (!nextStation) return null;
            
            // Skip the first segment for Central and Harbour lines (handled by CSMT junction)
            if ((lineKey === 'central' || lineKey === 'harbour') && index === 0) {
              // Start from after CSMT junction
              return (
                <g key={`segment-${index}`}>
                  {/* Up track from CSMT */}
                  <line
                    x1={150}
                    y1={line.yOffset - 15}
                    x2={nextStation.x}
                    y2={line.yOffset - 15}
                    stroke={line.color}
                    strokeWidth="4"
                    opacity="0.8"
                  />
                  
                  {/* Down track from CSMT */}
                  <line
                    x1={150}
                    y1={line.yOffset + 15}
                    x2={nextStation.x}
                    y2={line.yOffset + 15}
                    stroke={line.color}
                    strokeWidth="4"
                    opacity="0.8"
                  />
                </g>
              );
            }
            
            // Check if there's a Dadar junction between these stations (for Western and Central)
            const junctionBetween = junctionStations.find(jp => 
              jp.id === 'DDR' && jp.x > station.x && jp.x < nextStation.x &&
              jp.connectedLines.some(conn => conn.line === lineKey)
            );
            
            if (junctionBetween) {
              // Route through Dadar junction with 45-degree connections
              const junctionConnection = junctionBetween.connectedLines.find(conn => conn.line === lineKey);
              const connectionY = junctionConnection ? junctionBetween.y : line.yOffset;
              
              return (
                <g key={`segment-${index}`}>
                  {/* Up track to junction */}
                  <line
                    x1={station.x}
                    y1={line.yOffset - 15}
                    x2={junctionBetween.x - 50}
                    y2={line.yOffset - 15}
                    stroke={line.color}
                    strokeWidth="4"
                    opacity="0.8"
                  />
                  
                  {/* Down track to junction */}
                  <line
                    x1={station.x}
                    y1={line.yOffset + 15}
                    x2={junctionBetween.x - 50}
                    y2={line.yOffset + 15}
                    stroke={line.color}
                    strokeWidth="4"
                    opacity="0.8"
                  />
                  
                  {/* 45-degree connection to junction - Up track */}
                  <line
                    x1={junctionBetween.x - 50}
                    y1={line.yOffset - 15}
                    x2={junctionBetween.x - 10}
                    y2={connectionY - 10}
                    stroke={line.color}
                    strokeWidth="4"
                    opacity="0.8"
                  />
                  
                  {/* 45-degree connection to junction - Down track */}
                  <line
                    x1={junctionBetween.x - 50}
                    y1={line.yOffset + 15}
                    x2={junctionBetween.x - 10}
                    y2={connectionY + 10}
                    stroke={line.color}
                    strokeWidth="4"
                    opacity="0.8"
                  />
                  
                  {/* 45-degree connection from junction - Up track */}
                  <line
                    x1={junctionBetween.x + 10}
                    y1={connectionY - 10}
                    x2={junctionBetween.x + 50}
                    y2={line.yOffset - 15}
                    stroke={line.color}
                    strokeWidth="4"
                    opacity="0.8"
                  />
                  
                  {/* 45-degree connection from junction - Down track */}
                  <line
                    x1={junctionBetween.x + 10}
                    y1={connectionY + 10}
                    x2={junctionBetween.x + 50}
                    y2={line.yOffset + 15}
                    stroke={line.color}
                    strokeWidth="4"
                    opacity="0.8"
                  />
                  
                  {/* Up track from junction */}
                  <line
                    x1={junctionBetween.x + 50}
                    y1={line.yOffset - 15}
                    x2={nextStation.x}
                    y2={line.yOffset - 15}
                    stroke={line.color}
                    strokeWidth="4"
                    opacity="0.8"
                  />
                  
                  {/* Down track from junction */}
                  <line
                    x1={junctionBetween.x + 50}
                    y1={line.yOffset + 15}
                    x2={nextStation.x}
                    y2={line.yOffset + 15}
                    stroke={line.color}
                    strokeWidth="4"
                    opacity="0.8"
                  />
                </g>
              );
            } else {
              // Normal dual track segment
              return (
                <g key={`segment-${index}`}>
                  {/* Up track */}
                  <line
                    x1={station.x}
                    y1={line.yOffset - 15}
                    x2={nextStation.x}
                    y2={line.yOffset - 15}
                    stroke={line.color}
                    strokeWidth="4"
                    opacity="0.8"
                  />
                  
                  {/* Down track */}
                  <line
                    x1={station.x}
                    y1={line.yOffset + 15}
                    x2={nextStation.x}
                    y2={line.yOffset + 15}
                    stroke={line.color}
                    strokeWidth="4"
                    opacity="0.8"
                  />
                </g>
              );
            }
          })}
          
          {/* Center divider line */}
          <line
            x1={150}
            y1={line.yOffset}
            x2={lineKey === 'central' ? 2920 : lineKey === 'harbour' ? 2520 : 2820}
            y2={line.yOffset}
            stroke="#9ca3af"
            strokeWidth="1"
            strokeDasharray="10,5"
            opacity="0.4"
          />
        </g>
        
        {/* Regular stations */}
        {line.stations.map((station, index) => (
          <g key={`${lineKey}-${station.id}`}>
            {/* Station marker */}
            <circle
              cx={station.x}
              cy={line.yOffset}
              r={station.isTerminal ? 10 : station.isJunction ? 8 : 6}
              fill={station.isTerminal ? '#dc2626' : station.isJunction ? '#f59e0b' : '#6b7280'}
              stroke="#ffffff"
              strokeWidth="3"
              className="cursor-pointer hover:opacity-80"
              onClick={() => handleStationClick(station, lineKey)}
            />
            
            {/* Station name with better spacing */}
            <text
              x={station.x}
              y={index % 2 === 0 ? line.yOffset - 60 : line.yOffset + 80}
              textAnchor="middle"
              className="text-sm fill-gray-700 font-semibold pointer-events-none"
            >
              {station.name}
            </text>
            
            {/* Station code */}
            <text
              x={station.x}
              y={index % 2 === 0 ? line.yOffset - 45 : line.yOffset + 65}
              textAnchor="middle"
              className="text-xs fill-gray-500 pointer-events-none"
            >
              {station.id}
            </text>
          </g>
        ))}
        
        {/* Trains moving on correct tracks */}
        {trains
          .filter(train => train.line === lineKey)
          .map(train => {
            // Calculate train position considering junctions
            let trainY = line.yOffset;
            let trainX = train.position;
            
            // Check if train is passing through a junction
            const nearJunction = junctionStations.find(junction => 
              junction.connectedLines.some(conn => conn.line === lineKey) &&
              Math.abs(trainX - junction.x) < 60
            );
            
            if (nearJunction) {
              // Route train through junction
              const junctionConnection = nearJunction.connectedLines.find(conn => conn.line === lineKey);
              if (trainX >= nearJunction.x - 50 && trainX <= nearJunction.x + 50) {
                // Train is in junction area - interpolate position
                const progress = (trainX - (nearJunction.x - 50)) / 100;
                if (trainX < nearJunction.x) {
                  // Approaching junction
                  trainY = line.yOffset + (nearJunction.y - line.yOffset) * (progress * 2);
                } else {
                  // Leaving junction
                  trainY = nearJunction.y + (line.yOffset - nearJunction.y) * ((progress - 0.5) * 2);
                }
              }
            } else {
              // Normal track - use up/down track positioning
              trainY = train.direction === 'up' ? line.yOffset - 15 : line.yOffset + 15;
            }
            
            return (
              <g key={train.id}>
                {/* Train body */}
                <rect
                  x={trainX - 15}
                  y={trainY - 12}
                  width="30"
                  height="24"
                  fill={line.color}
                  stroke="#ffffff"
                  strokeWidth="2"
                  rx="6"
                  className="cursor-pointer"
                  title={`${train.trainNumber} - Next: ${train.nextStation}`}
                />
                
                {/* Direction indicator */}
                <polygon
                  points={train.direction === 'up' 
                    ? `${trainX + 15},${trainY} ${trainX + 25},${trainY - 5} ${trainX + 25},${trainY + 5}`
                    : `${trainX - 15},${trainY} ${trainX - 25},${trainY - 5} ${trainX - 25},${trainY + 5}`
                  }
                  fill="#ffffff"
                />
                
                {/* Train number - positioned to avoid overlap */}
                <text
                  x={trainX}
                  y={trainY - 35}
                  textAnchor="middle"
                  className="text-sm fill-gray-800 font-bold pointer-events-none"
                  style={{ textShadow: '1px 1px 2px rgba(255,255,255,0.8)' }}
                >
                  {train.trainNumber}
                </text>
              </g>
            );
          })}
        
        {/* Line label */}
        <text
          x={50}
          y={line.yOffset + 5}
          textAnchor="middle"
          className="text-lg font-bold pointer-events-none"
          fill={line.color}
          transform={`rotate(-90, 50, ${line.yOffset + 5})`}
        >
          {line.name}
        </text>
      </g>
    );
  };

  // Junction Stations Component with proper dual track connections
  const JunctionStationsComponent = () => {
    return (
      <g key="junction-stations">
        {junctionStations.map(junction => (
          <g key={`junction-${junction.name}`}>
            {/* Junction tracks - show all connecting track segments */}
            {junction.connectedLines.map((connection, index) => (
              <g key={`junction-tracks-${connection.line}-${index}`}>
                {/* Up track connection */}
                <line
                  x1={junction.x - 10}
                  y1={junction.y - 10}
                  x2={junction.x + 10}
                  y2={junction.y - 10}
                  stroke={lines[connection.line].color}
                  strokeWidth="4"
                  opacity="0.9"
                />
                
                {/* Down track connection */}
                <line
                  x1={junction.x - 10}
                  y1={junction.y + 10}
                  x2={junction.x + 10}
                  y2={junction.y + 10}
                  stroke={lines[connection.line].color}
                  strokeWidth="4"
                  opacity="0.9"
                />
              </g>
            ))}
            
            {/* Junction station marker */}
            <circle
              cx={junction.x}
              cy={junction.y}
              r="16"
              fill="#8b5cf6"
              stroke="#ffffff"
              strokeWidth="4"
              className="cursor-pointer hover:opacity-80"
              onClick={() => handleStationClick(junction, 'junction')}
            />
            
            {/* Inner circle for better visibility */}
            <circle
              cx={junction.x}
              cy={junction.y}
              r="8"
              fill="#ffffff"
              opacity="0.9"
            />
            
            {/* Station name */}
            <text
              x={junction.x}
              y={junction.y - 40}
              textAnchor="middle"
              className="text-lg fill-gray-800 font-bold pointer-events-none"
              style={{ textShadow: '2px 2px 4px rgba(255,255,255,0.8)' }}
            >
              {junction.name}
            </text>
            
            {/* Junction indicator */}
            <text
              x={junction.x}
              y={junction.y + 50}
              textAnchor="middle"
              className="text-sm fill-purple-600 font-bold pointer-events-none"
            >
              INTERCHANGE
            </text>
            
            {/* Connected lines indicator */}
            <text
              x={junction.x}
              y={junction.y + 70}
              textAnchor="middle"
              className="text-xs fill-purple-500 font-medium pointer-events-none"
            >
              {junction.connectedLines.map(conn => conn.line.charAt(0).toUpperCase()).join(' • ')}
            </text>
          </g>
        ))}
      </g>
    );
  };

  return (
    <div className="h-screen w-full bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-white text-gray-800 px-6 py-4 shadow-lg border-b flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold text-gray-700">Mumbai Local Train Tracking</h1>
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <Clock className="w-4 h-4" />
            <span>{currentTime.toLocaleTimeString()}</span>
          </div>
        </div>
        <NavLink 
          to="/" 
          className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
        >
          Home
        </NavLink>
      </div>
      
      {/* Controls */}
      <div className="bg-white px-6 py-3 flex items-center justify-between border-b border-gray-200 shadow-sm">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => setIsSimulationRunning(!isSimulationRunning)}
            className={`flex items-center space-x-2 px-4 py-2 ${
              isSimulationRunning ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'
            } text-white rounded-lg transition-colors shadow-md`}
          >
            {isSimulationRunning ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            <span>{isSimulationRunning ? 'Pause' : 'Start'} Simulation</span>
          </button>
          
          <button
            onClick={generateTrains}
            className="flex items-center space-x-2 px-4 py-2 bg-gray-500 hover:bg-gray-600 text-white rounded-lg transition-colors shadow-md"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Reset Trains</span>
          </button>
          
          <div className="flex items-center space-x-4 text-sm text-gray-600">
            <div className="flex items-center space-x-1">
              <Train className="w-4 h-4" />
              <span>Active Trains: {trains.length}</span>
            </div>
            <div className="flex items-center space-x-1">
              <MapPin className="w-4 h-4" />
              <span>Total Stations: {Object.values(lines).reduce((acc, line) => acc + line.stations.length, 0) + junctionStations.length}</span>
            </div>
          </div>
        </div>
      </div>
      
      {/* Legend */}
      <div className="bg-white px-6 py-2 flex items-center space-x-6 text-sm text-gray-700 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded-full bg-red-600"></div>
          <span>Terminal Stations</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded-full bg-amber-500"></div>
          <span>Junction Stations</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded-full bg-purple-500"></div>
          <span>Interchange Stations</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 rounded-full bg-gray-500"></div>
          <span>Regular Stations</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="flex space-x-1">
            <div className="w-4 h-3 bg-red-500"></div>
            <div className="w-4 h-3 bg-blue-600"></div>
            <div className="w-4 h-3 bg-green-600"></div>
          </div>
          <span>Western | Central | Harbour Lines</span>
        </div>
      </div>
      
      {/* Main Track Display */}
      <div className="flex-1 overflow-auto bg-gray-50 p-6">
        <div className="min-w-max">
          <svg width="3100" height="650" className="bg-white rounded-lg shadow-lg border">
            <defs>
              <pattern id="grid" width="100" height="100" patternUnits="userSpaceOnUse">
                <path d="M 100 0 L 0 0 0 100" fill="none" stroke="#f3f4f6" strokeWidth="1"/>
              </pattern>
            </defs>
            
            {/* Grid background */}
            <rect width="100%" height="100%" fill="url(#grid)" />
            
            {/* Render each line */}
            <LineComponent lineKey="western" line={lines.western} />
            <LineComponent lineKey="central" line={lines.central} />
            <LineComponent lineKey="harbour" line={lines.harbour} />
            
            {/* Render junction stations */}
            <JunctionStationsComponent />
          </svg>
        </div>
      </div>
      
      {/* Live Train Status */}
      <div className="bg-white border-t border-gray-200 p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(lines).map(([lineKey, line]) => (
            <div key={lineKey} className="bg-gray-50 rounded-lg p-3">
              <h3 className="font-semibold text-gray-700 mb-2 flex items-center">
                <div className={`w-3 h-3 rounded-full mr-2`} style={{ backgroundColor: line.color }}></div>
                {line.name}
              </h3>
              <div className="space-y-1 text-xs max-h-32 overflow-y-auto">
                {trains
                  .filter(train => train.line === lineKey)
                  .map(train => (
                    <div key={train.id} className="flex justify-between items-center bg-white p-2 rounded">
                      <span className="font-medium">{train.trainNumber}</span>
                      <span className="text-blue-600 text-xs">
                        {train.direction === 'up' ? '↑' : '↓'} {train.direction.toUpperCase()}
                      </span>
                      <span className="text-gray-600">→ {train.nextStation}</span>
                    </div>
                  ))}
                {trains.filter(train => train.line === lineKey).length === 0 && (
                  <div className="text-gray-500 text-center py-2">No active trains</div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Station Details Modal */}
      {showStationModal && selectedStation && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
            <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white px-6 py-4 rounded-t-lg">
              <h3 className="text-lg font-bold">{selectedStation.name} Station</h3>
              <p className="text-sm text-blue-100">
                {selectedStation.line === 'junction' 
                  ? `Interchange Station`
                  : `${lines[selectedStation.line]?.name} • ${selectedStation.id}`
                }
              </p>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="bg-gray-100 p-3 rounded">
                    <span className="text-gray-600">Type:</span>
                    <span className="ml-1 font-medium">
                      {selectedStation.line === 'junction' ? 'Interchange' :
                       selectedStation.isTerminal ? 'Terminal' : 
                       selectedStation.isJunction ? 'Junction' : 'Regular'}
                    </span>
                  </div>
                  <div className="bg-gray-100 p-3 rounded">
                    <span className="text-gray-600">Status:</span>
                    <span className="ml-1 font-medium text-green-600">Active</span>
                  </div>
                </div>
                
                {/* Station Schedule */}
                <div>
                  <h4 className="font-semibold text-gray-700 mb-2">Today's Schedule</h4>
                  <div className="bg-gray-50 p-3 rounded text-sm">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <span className="text-gray-600 text-xs">First Train:</span>
                        <div className="font-medium">05:15 AM</div>
                      </div>
                      <div>
                        <span className="text-gray-600 text-xs">Last Train:</span>
                        <div className="font-medium">12:45 AM</div>
                      </div>
                      <div>
                        <span className="text-gray-600 text-xs">Peak Frequency:</span>
                        <div className="font-medium">3-4 mins</div>
                      </div>
                      <div>
                        <span className="text-gray-600 text-xs">Off-Peak Frequency:</span>
                        <div className="font-medium">6-8 mins</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="bg-gray-50 px-6 py-3 flex justify-end border-t rounded-b-lg">
              <button 
                onClick={() => setShowStationModal(false)}
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
};

export default MumbaiLocal;