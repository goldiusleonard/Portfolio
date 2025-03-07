import asyncio
from arq.connections import RedisSettings
from arq.worker import Worker
from api import process_filter_task, process_direct_task, logger, redis_url 


# Startup function for ARQ worker
async def startup(ctx):
    """Startup function for Arq worker."""
    logger.info("ARQ worker started")


# Shutdown function for ARQ worker
async def shutdown(ctx):
    """Shutdown function for Arq worker."""
    logger.info("ARQ worker shutting down")



# Configuration for ARQ worker as a class
class WorkerSettings:
    """Configuration for ARQ worker."""
    functions = [process_filter_task, process_direct_task]  
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings.from_dsn(redis_url)  



# Redis connection check function
async def check_redis_connection(redis_url):
    try:
        redis_settings = RedisSettings.from_dsn(redis_url)  # Create RedisSettings from the DSN
        redis_client = await redis_settings.create_client()  # Correct way to create a Redis client in ARQ
        await redis_client.ping()  # Ping Redis to check if it's alive
        logger.info("Successfully connected to Redis.")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {str(e)}")


if __name__ == "__main__":
    print("@@@@@@@@@@@@@@@@@@@@@@@")
    print(type(process_filter_task))  # Should print <class 'function'>
    print(type(process_direct_task))  # Should print <class 'function'> 
    print(redis_url)

    redis_settings = RedisSettings.from_dsn(redis_url)  # Ensure redis_url is correct
    # Check Redis connection before starting the worker
    loop = asyncio.get_event_loop()
    loop.run_until_complete(check_redis_connection(redis_url))

    functions = [process_filter_task, process_direct_task]  # List of functions to process

    # Initialize the worker with simplified config
    worker = Worker(
        functions=functions,  # Directly pass the functions here
        on_startup=startup,
        on_shutdown=shutdown,
        redis_settings=redis_settings
    )
    asyncio.run(worker.run())
    # asyncio.run(Worker(WorkerSettings).start())