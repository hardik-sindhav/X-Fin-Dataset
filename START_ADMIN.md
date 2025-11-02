# 🚀 Quick Start Guide - React Admin Panel

## Prerequisites

- Node.js 18+ and npm installed
- Python 3.7+ installed
- MongoDB running

## Setup Steps

### 1. Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 3. Start the Backend API Server

In one terminal:

```bash
cd backend
python admin_panel.py
```

The API server will run on: **http://localhost:5000**

### 4. Start the Frontend Development Server

In another terminal:

```bash
cd frontend
npm run dev
```

The React app will run on: **http://localhost:3000**

## Features

✨ **Modern UI**: Beautiful dark-themed interface  
⚡ **Fast**: Built with Vite for instant hot-reload  
📊 **Real-time**: Auto-refreshes every 30 seconds  
🎯 **Interactive**: One-click manual data collection  
📈 **Visual**: Color-coded trend indicators  

## Architecture

- **Backend**: Flask API server (port 5000)
- **Frontend**: React + Vite (port 3000)
- **Communication**: REST API with CORS enabled

## Production Build

To build the frontend for production:

```bash
cd frontend
npm run build
```

The built files will be in `frontend/dist/`

