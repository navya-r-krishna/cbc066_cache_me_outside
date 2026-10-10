
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="Interview Question Generator",
    version="1.0.0"
)


class JobDescriptionRequest(BaseModel):
    job_title: str
    job_description: str


@app.get("/")
def home():
    return {"message": "Interview Question Generator API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/analyze-job")
def analyze_job(request: JobDescriptionRequest):
    return {
        "job_title": request.job_title,
        "job_description": request.job_description,
        "status": "received"
    }
