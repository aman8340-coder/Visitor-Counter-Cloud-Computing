from flask import Flask, jsonify
import os
import redis

app = Flask(__name__)
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
)

@app.get("/")
def home():
    try:
        visits = redis_client.incr("visitor_count")
        return f"""
        <!doctype html>
        <html>
          <head><title>Visitor Counter</title></head>
          <body style="font-family:Arial;text-align:center;margin-top:12%">
            <h1>Visitor Counter Web Application</h1>
            <h2>Total visits: {visits}</h2>
            <p>Powered by Flask, Redis, Docker and Kubernetes</p>
          </body>
        </html>
        """
    except redis.RedisError:
        return "Redis is temporarily unavailable. Please try again.", 503

@app.get("/health")
def health():
    return jsonify(status="ok"), 200

@app.get("/ready")
def ready():
    try:
        redis_client.ping()
        return jsonify(ready=True), 200
    except redis.RedisError:
        return jsonify(ready=False), 503

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
