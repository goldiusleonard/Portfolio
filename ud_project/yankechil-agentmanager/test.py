import asyncio

async def cleanup():
    loop = asyncio.get_running_loop()
    tasks = [task for task in asyncio.all_tasks(loop) if task is not asyncio.current_task()]
    
    for task in tasks:
        task.cancel()
    
    await asyncio.gather(*tasks, return_exceptions=True)

asyncio.run(cleanup())