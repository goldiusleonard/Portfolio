import subprocess
from celery import Celery

app = Celery(
    "tasks", broker="pyamqp://guest:guest@rabbitmq:5672//"
)  # RabbitMQ broker setup


# Subprocess-based crawling functions
def perform_crawl_with_subprocess(command: str):
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during crawl: {e}")


@app.task
def keyword_task(keyword: str):
    # Run the keyword crawler with subprocess
    command = f"python run.py --type keyword --keyword '{keyword}' --region MY --count 2 --cursor 0"
    perform_crawl_with_subprocess(command)


@app.task
def trending_task():
    # Run the trending crawler with subprocess
    command = "python run.py --type trending --region MY --count 2"
    perform_crawl_with_subprocess(command)


@app.task
def user_task(username: str):
    # Run the user crawler with subprocess
    command = (
        f"python run.py --type username --username '{username}' --count 2 --cursor 0"
    )
    perform_crawl_with_subprocess(command)


@app.task
def url_task(url: str):
    # Run the URL crawler with subprocess
    command = f"python run.py --type url --url '{url}'"
    perform_crawl_with_subprocess(command)


# celery -A tasks worker --loglevel=INFO -n worker1@%n
# celery -A tasks worker --loglevel=INFO --concurrency=10 -n worker2@%h
