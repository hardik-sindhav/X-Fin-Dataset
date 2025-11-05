# Frontend Admin - React Admin Panel

Modern React + Vite admin panel for X Fin Dataset - Admin Interface.

This is the admin interface project, identical to the main frontend but kept separate for admin-specific deployments.

## Installation

```bash
npm install
```

## Development

Start the development server:

```bash
npm run dev
```

The app will be available at `http://localhost:3000`

Make sure the Flask backend is running on `http://localhost:5000`

## Build

Build for production:

```bash
npm run build
```

## Features

- 🎨 Modern, beautiful UI with dark theme
- ⚡ Fast and responsive
- 🔄 Auto-refresh every 30 seconds
- 📊 Real-time status monitoring
- 📈 Data visualization with trend indicators
- 🎯 One-click manual trigger
- ⚙️ Settings page for scheduler configuration
- 📅 Holiday management

## Project Structure

```
frontend-admin/
├── src/
│   ├── App.jsx          # Main application component
│   ├── App.css          # Main styles
│   ├── main.jsx         # Entry point
│   ├── index.css        # Global styles
│   └── components/
│       ├── HomePage.jsx
│       ├── Login.jsx
│       ├── Settings.jsx
│       ├── Pricing.jsx
│       └── Footer.jsx
├── package.json
├── vite.config.js
└── index.html
```

## Usage

This is a duplicate of the main frontend project. Use this for:
- Separate admin-only deployments
- Different domain/subdomain deployments
- Admin-specific customizations

All functionality is identical to the main `frontend` project.
