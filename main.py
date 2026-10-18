import json
import time
import uuid
from collections import deque

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest

EMAIL = "25f1002436@ds.study.iitm.ac.in"  # your exam login email
START = time.time()
LOGS = deque(maxlen=1000)

REQUESTS = Counter("http_requests_total", "Total HTTP requests")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def observe(request: Request, call_next):
    REQUESTS.inc()  # counted before handling, so /metrics includes itself
    request_id = str(uuid.uuid4())
    response = await call_next(request)
    entry = {
        "level": "INFO",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "Z",
        "path": request.url.path,
        "request_id": request_id,
        "method": request.method,
        "status": response.status_code,
    }
    LOGS.append(entry)
    print(json.dumps(entry), flush=True)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/work")
def work(n: int = 1):
    n = max(0, min(n, 1_000_000))
    total = 0
    for i in range(n):
        total += i * i
    return {"email": EMAIL, "done": n}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/healthz")
def healthz():
    return {"status": "ok", "uptime_s": float(time.time() - START)}


@app.get("/logs/tail")
def logs_tail(limit: int = 50):
    if limit <= 0:
        return []
    return list(LOGS)[-limit:]
