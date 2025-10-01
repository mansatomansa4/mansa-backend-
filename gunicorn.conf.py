import multiprocessing
import os

bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
workers = int(multiprocessing.cpu_count() * 2) + 1
worker_class = "gthread"
threads = 4
preload_app = True
accesslog = "-"  # stdout
errorlog = "-"  # stderr
loglevel = "info"
