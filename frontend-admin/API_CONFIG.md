# API Configuration Guide

## Automatic Environment Detection

The frontend-admin automatically detects the environment and uses the appropriate API URL:

### Development (Local)
- **Detected when:** Running on `localhost` or `127.0.0.1`
- **API URL:** `/api` (uses Vite proxy to `http://localhost:5000`)
- **How to run:** `npm run dev`

### Production
- **Detected when:** Running on any other hostname
- **API URL:** `https://api.xfinai.cloud/api`
- **How to build:** `npm run build`

## Configuration File

The API base URL is configured in `src/config.js`:

```javascript
export const API_BASE = isDevelopment 
  ? '/api'  // Development: uses Vite proxy
  : 'https://api.xfinai.cloud/api'  // Production
```

## How It Works

1. **Development Mode:**
   - Vite proxy forwards `/api/*` requests to `http://localhost:5000`
   - No CORS issues
   - Works with local backend

2. **Production Mode:**
   - Direct API calls to `https://api.xfinai.cloud/api`
   - Requires CORS to be configured on backend
   - Works with deployed backend

## Manual Override (Optional)

If you need to manually override the API URL, edit `src/config.js`:

```javascript
// Force development mode
export const API_BASE = '/api'

// Or force production URL
export const API_BASE = 'https://api.xfinai.cloud/api'
```

## Testing

### Local Development
```bash
# Start backend on localhost:5000
cd backend
python3 admin_panel.py

# Start frontend-admin
cd frontend-admin
npm run dev
# Open http://localhost:3000
```

### Production Build
```bash
cd frontend-admin
npm run build
# Deploy dist/ folder to your web server
```

## Files Updated

- ✅ `src/config.js` - New configuration file
- ✅ `src/App.jsx` - Uses config
- ✅ `src/components/Login.jsx` - Uses config
- ✅ `src/components/HomePage.jsx` - Uses config
- ✅ `src/components/Settings.jsx` - Uses config

All components now automatically use the correct API URL based on environment!

