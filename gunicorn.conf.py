import multiprocessing

# Gunicorn configuration file
# https://docs.gunicorn.org/en/latest/configure.html

# Server socket
bind = "0.0.0.0:8000"  # Use port 8000 by default, adjust as needed

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1  # Dynamically set based on available CPUs

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = "info"

# Security
limit_request_line = 4094  # Limit the allowed size of the HTTP request line
limit_request_fields = 100  # Limit the number of HTTP headers

# Timeouts
timeout = 30  # Worker silent for more than this many seconds are killed and restarted
keepalive = 2  # The number of seconds to wait for requests on a Keep-Alive connection

# SSL (uncomment and modify if using HTTPS)
# keyfile = '/path/to/key'
# certfile = '/path/to/cert'

# Worker process name
proc_name = 'gunicorn_process'