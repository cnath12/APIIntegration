import multiprocessing

# Server socket
bind = "0.0.0.0:8000"  # Use port 8000 by default, adjust as needed

workers = multiprocessing.cpu_count() * 2 + 1  # Dynamically set based on available CPUs

#worker_class = "gevent"

# Logging
accesslog = "-" 
errorlog = "-"  
loglevel = "info"

# Security
limit_request_line = 4094 
limit_request_fields = 100 

# Timeouts
timeout = 30 
keepalive = 5

forwarded_allow_ips = '127.0.0.1'
# Worker process name
proc_name = 'gunicorn_process'