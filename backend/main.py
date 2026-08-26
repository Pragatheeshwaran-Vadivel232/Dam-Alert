from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import farmers, dams, alerts

app = FastAPI(
    title="KaLai Dam Alert API",
    version="1.0",
    description="Dam water level alert system for village farmers"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(farmers.router)
app.include_router(dams.router)
app.include_router(alerts.router)

@app.get("/")
def root():
    return {"message": "KaLai Dam Alert API is running ✅"}

@app.get("/health")
def health():
    return {"status": "ok"}
