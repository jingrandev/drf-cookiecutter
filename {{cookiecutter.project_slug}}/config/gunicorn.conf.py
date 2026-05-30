import multiprocessing

worker_class = "uvicorn.workers.UvicornWorker"
workers = multiprocessing.cpu_count() * 2 + 1
threads = 1
worker_connections = 1000
max_requests = 10000
max_requests_jitter = 200
loglevel = "info"
accesslog = "-"
access_log_format = '%(h)s %(l)s %(u)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(L)s'
forwarded_allow_ips = "*"
backlog = 512
timeout = 120
graceful_timeout = 300
keepalive = 3
limit_request_line = 5120
limit_request_fields = 101
limit_request_field_size = 0
