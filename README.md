# Mumbai Railway Management System

This project was developed for the Smart India Hackathon (SIH) 2025, addressing problem statement 25022. The system reached the top 30 out of over 125 teams in the internal college selection round.

The application is a unified platform for real-time train scheduling, conflict resolution, and network visualization, specifically designed for the Mumbai Suburban Railway network.

## Technical Architecture

The system is built using a modular architecture comprising three main components:

### Backend
The backend is powered by FastAPI and manages real-time data flow and simulation logic.
- Neo4j: Graph database used to model the complex railway topology, stations, and track segments.
- PuLP: Mixed Integer Linear Programming (MILP) library used for calculating optimal train schedules and resolving precedence conflicts.
- WebSockets: Enables real-time communication for live status updates and simulation data.

### Optimization and AI
The optimization layer utilizes advanced algorithms to manage dynamic railway operations.
- GNN-DQN: A Deep Reinforcement Learning model using Graph Convolutional Networks to predict and handle dispatching decisions based on live network states.
- TensorFlow: Framework used for training and deploying the GNN-DQN models.
- NetworkX: Used for graph-based pathfinding and network analysis.

### Frontend
The user interface is a modern dashboard providing deep insights into the railway operations.
- React and TypeScript: Core framework for a robust and type-safe user interface.
- Tailwind CSS: Used for professional and responsive styling.
- Three.js: Integrated for 3D visualization of the train network.

## Key Features

- Real-time Simulation: Live tracking and movement simulation of trains across the Mumbai Local corridors including Central, Western, and Harbour lines.
- Schedule Optimization: Automated generation of conflict-free schedules using MILP to minimize weighted delays.
- Dynamic Dispatching: AI-driven decision making for train prioritization and platform assignment.
- Graph Integration: Full representation of the railway network in Neo4j for efficient pathing and relationship management.
- Comprehensive Analytics: Dedicated views for network performance, incident management, and station-specific data.

## Project Structure

- /algo: Contains training scripts for the GNN-DQN model, data handling utilities, and corridor configurations.
- /backend: Fastapi server, MILP optimization logic, and Neo4j driver integrations.
- /frontend: React application with interactive dashboards and 3D visualization components.
- /configs: YAML and JSON configuration files for various railway scenarios and corridor layouts.

## Setup Instructions

### Backend Setup
1. Navigate to the backend directory.
2. Install dependencies: pip install -r requirements.txt
3. Configure environment variables in a .env file (NEO4J_URI, DB_USERNAME, DB_PASSWORD).
4. Start the server: uvicorn main:app --reload

### Frontend Setup
1. Navigate to the frontend directory.
2. Install dependencies: npm install
3. Start the development server: npm run dev
