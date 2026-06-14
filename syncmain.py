import time
import asyncio
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def home():
    wait asyncio.sleep(3)
    return {"message": "Hello World VNV"}
# async def task():
#     await asyncio.sleep(3)
#     return "Task completed"