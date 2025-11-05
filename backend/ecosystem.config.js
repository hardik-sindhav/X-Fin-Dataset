module.exports = {
  apps: [{
    name: 'x-fin-backend',
    script: 'admin_panel.py',
    interpreter: 'python3.11',
    cwd: '/var/www/x-fin-dataset/backend',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      FLASK_ENV: 'production',
      PORT: 5000
    },
    error_file: './logs/backend-error.log',
    out_file: './logs/backend-out.log',
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    merge_logs: true
  }]
};

