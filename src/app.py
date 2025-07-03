from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .workflow import Workflow
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

workflow = Workflow()

class AnalyzeRequest(BaseModel):
    company_url: str

@app.post("/analyze")
async def analyze(request: AnalyzeRequest):
    company_url = request.company_url
    try:
        result = workflow.run(company_url)
        def model_to_dict(obj):
            if hasattr(obj, 'model_dump'):
                return obj.model_dump()
            if isinstance(obj, list):
                return [model_to_dict(i) for i in obj]
            return obj
        response = {
            'company_profile': model_to_dict(result["company_profile"]),
            'competitors': model_to_dict(result["competitors"]),
            'competitor_analyses': model_to_dict(result["competitor_analyses"]),
            'strategic_insights': model_to_dict(result["strategic_insights"]),
            'analysis_report': result["analysis_report"]
        }
        return response
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
async def index():
    return {"message": "AI Startup Competitive Intelligence Analyzer Backend (FastAPI) is running."}

if __name__ == "__main__":
    uvicorn.run("src.app:app", host="0.0.0.0", port=5000, reload=True) 