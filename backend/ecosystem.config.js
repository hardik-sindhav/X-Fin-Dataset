module.exports = {
  apps: [{
    name: 'x-fin-backend',
    script: 'admin_panel.py',
    interpreter: 'python3',  // Change to 'python3.11' if you installed Python 3.11 specifically
    cwd: '/var/www/xfinai/backend',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      FLASK_ENV: 'production',
      PORT: 5000,
      AUTO_START_SCHEDULERS: 'true'
    },
    error_file: './logs/backend-error.log',
    out_file: './logs/backend-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true
  }]
};

