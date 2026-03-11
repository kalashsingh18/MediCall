from fastapi import FastAPI
import redis

app = FastAPI()

r = redis.Redis(host="redis", port=6373, decode_responses=True)

@app.get("/")
def home():
    return {"message": "Backend is running"}
