import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Query, File, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Index, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
import google.auth
import json
import PyPDF2
import io

# Load environment variables
load_dotenv()

# Configure Google Cloud
try:
    _, project_id = google.auth.default()
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", project_id)
except Exception:
    pass

os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "europe-west1")

# Configure ADK model connection
gemma_model_name = os.getenv("GEMMA_MODEL_NAME", "gemma3:270m")
api_base = os.getenv("OLLAMA_API_BASE", "http://localhost:10010")

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:anPVKtbUFJh2qSR9@db.fdsixtggqgxjronydsaf.supabase.co:5432/postgres")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ==================== DATABASE MODELS ====================
class JobsDatabase(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String(255), index=True)
    title = Column(String(255), index=True)
    link = Column(String(500), index=True)
    description = Column(Text, index=True)
    experience_level = Column(String(100), index=True)
    location = Column(String(255), index=True)
    company = Column(String(255), index=True)
    salary_range = Column(String(100))
    job_type = Column(String(50), index=True)
    remote_option = Column(String(50), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('ix_jobs_title_location', 'title', 'location'),
        Index('ix_jobs_experience_location', 'experience_level', 'location'),
        Index('ix_jobs_company_title', 'company', 'title'),
        Index('ix_jobs_created_desc', 'created_at', postgresql_ops={'created_at': 'DESC'}),
    )

# Create tables
Base.metadata.create_all(bind=engine)

# ==================== PYDANTIC MODELS ====================
class JobCreate(BaseModel):
    job_name: Optional[str] = None
    title: str
    link: Optional[str] = None
    description: Optional[str] = None
    experience_level: Optional[str] = None
    location: Optional[str] = None
    company: Optional[str] = None
    salary_range: Optional[str] = None
    job_type: Optional[str] = None
    remote_option: Optional[str] = None

class JobResponse(BaseModel):
    id: int
    job_name: Optional[str]
    title: str
    link: Optional[str]
    description: Optional[str]
    experience_level: Optional[str]
    location: Optional[str]
    company: Optional[str]
    salary_range: Optional[str]
    job_type: Optional[str]
    remote_option: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ==================== AI AGENTS ====================

# Combined CV Analysis & Skills Extraction Agent
cv_processor_agent = Agent(
    model=LiteLlm(model=f"ollama_chat/{gemma_model_name}", api_base=api_base),
    name="cv_processor",
    description="CV analysis and skills extraction agent",
    instruction="""You are a CV analysis expert. Analyze the CV and provide feedback in JSON format.

**Output Format:**
Return ONLY this JSON structure:

{
    "summary": "Brief 2-3 sentence summary of the candidate's profile",
    "strengths": ["strength 1", "strength 2", "strength 3"],
    "improvements": ["improvement 1", "improvement 2"],
    "skills": ["Python", "Java", "React", "AWS", "Docker", "Backend Developer"],
    "experience_level": "Junior/Mid/Senior"
}

**Rules:**
1. Extract ALL technical skills, tools, frameworks, and job roles
2. Provide constructive feedback
3. Return ONLY valid JSON - no markdown, no explanation
4. Keep feedback concise and actionable""",
    tools=[],
)

# ==================== HELPER FUNCTIONS ====================
def extract_text_from_pdf(pdf_file: UploadFile) -> str:
    """Extract text from PDF"""
    try:
        pdf_content = pdf_file.file.read()
        pdf_file.file.seek(0)
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
        
        text_content = []
        for page in pdf_reader.pages:
            text_content.append(page.extract_text())
        
        full_text = "\n\n".join(text_content).strip()
        
        if not full_text:
            raise ValueError("No text could be extracted from the PDF")
        
        return full_text
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")

def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==================== FASTAPI APP ====================
app = FastAPI(
    title="Simple CV Upload & Job Match API",
    description="Upload your CV and instantly get review + job recommendations",
    version="3.0.0"
)

# ==================== MAIN ENDPOINT ====================

@app.post("/upload-cv", tags=["CV Processing"])
async def upload_cv_and_get_jobs(
    file: UploadFile = File(..., description="PDF file of your CV/Resume"),
    limit: int = Query(10, ge=1, le=50, description="Number of job recommendations"),
    db: Session = Depends(get_db)
):
    """
    🎯 MAIN ENDPOINT: Upload CV and get instant review + job recommendations
    
    **What you get:**
    1. ✅ CV Review (strengths, improvements, summary)
    2. 🎯 Extracted Skills
    3. 💼 Top Matching Jobs (ranked by relevance)
    
    **Usage:**
    - Upload your PDF CV
    - Get everything in one response
    - No additional steps needed!
    
    **Example:**
    ```bash
    curl -X POST "http://localhost:8080/upload-cv?limit=10" \
         -F "file=@my_cv.pdf"
    ```
    """
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Step 1: Extract text from PDF
        cv_text = extract_text_from_pdf(file)
        
        # Step 2: Analyze CV and extract skills using AI
        response = cv_processor_agent.run(cv_text)
        
        # Get response text
        response_text = ""
        if hasattr(response, 'text'):
            response_text = response.text
        elif hasattr(response, 'content'):
            response_text = response.content
        else:
            response_text = str(response)
        
        # Parse AI response
        try:
            # Clean response
            clean_response = response_text.strip()
            if clean_response.startswith("```json"):
                clean_response = clean_response.replace("```json", "").replace("```", "").strip()
            elif clean_response.startswith("```"):
                clean_response = clean_response.replace("```", "").strip()
            
            # Parse JSON
            cv_analysis = json.loads(clean_response)
            skills = cv_analysis.get("skills", [])
            
        except json.JSONDecodeError:
            # Fallback: extract skills manually
            skills = []
            for line in response_text.split('\n'):
                line = line.strip().replace('"', '').replace(',', '').strip()
                if line and len(line) > 2 and not line.startswith('{') and not line.startswith('}'):
                    skills.append(line)
            
            cv_analysis = {
                "summary": "CV analysis completed",
                "strengths": ["Experience in multiple technologies"],
                "improvements": ["Consider adding more specific achievements"],
                "skills": skills,
                "experience_level": "Not specified"
            }
        
        # Step 3: Find matching jobs
        if not skills:
            return JSONResponse(content={
                "cv_review": cv_analysis,
                "matching_jobs": [],
                "message": "No skills extracted - unable to match jobs"
            })
        
        # Search for jobs
        keywords = [skill.lower().strip() for skill in skills]
        or_conditions = []
        for keyword in keywords:
            or_conditions.extend([
                JobsDatabase.title.ilike(f"%{keyword}%"),
                JobsDatabase.description.ilike(f"%{keyword}%"),
                JobsDatabase.job_name.ilike(f"%{keyword}%")
            ])
        
        jobs = db.query(JobsDatabase).filter(or_(*or_conditions))\
                 .order_by(JobsDatabase.created_at.desc())\
                 .limit(limit * 3).all()  # Get more to rank properly
        
        # Calculate relevance scores
        job_matches = []
        for job in jobs:
            matched_keywords = []
            relevance_score = 0
            
            job_text = f"{job.title or ''} {job.description or ''} {job.job_name or ''}".lower()
            
            for keyword in keywords:
                if keyword in job_text:
                    matched_keywords.append(keyword)
                    if job.title and keyword in job.title.lower():
                        relevance_score += 3
                    if job.job_name and keyword in job.job_name.lower():
                        relevance_score += 2
                    if job.description and keyword in job.description.lower():
                        relevance_score += 1
            
            if matched_keywords:
                job_matches.append({
                    "job": {
                        "id": job.id,
                        "title": job.title,
                        "company": job.company,
                        "location": job.location,
                        "experience_level": job.experience_level,
                        "job_type": job.job_type,
                        "remote_option": job.remote_option,
                        "salary_range": job.salary_range,
                        "link": job.link,
                        "description": job.description[:250] + "..." if job.description and len(job.description) > 250 else job.description
                    },
                    "relevance_score": relevance_score,
                    "matched_skills": matched_keywords
                })
        
        # Sort by relevance and limit
        job_matches.sort(key=lambda x: x["relevance_score"], reverse=True)
        job_matches = job_matches[:limit]
        
        # Return complete response
        return JSONResponse(content={
            "success": True,
            "cv_review": {
                "summary": cv_analysis.get("summary", ""),
                "strengths": cv_analysis.get("strengths", []),
                "improvements": cv_analysis.get("improvements", []),
                "experience_level": cv_analysis.get("experience_level", "Not specified"),
                "extracted_skills": skills
            },
            "job_recommendations": {
                "total_matches": len(job_matches),
                "jobs": job_matches
            },
            "message": f"Found {len(job_matches)} matching jobs for your profile!"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing CV: {str(e)}")


# ==================== JOB MANAGEMENT ENDPOINTS ====================

@app.post("/jobs", response_model=JobResponse, tags=["Job Management"])
def create_job(job: JobCreate, db: Session = Depends(get_db)):
    """
    Create a new job posting
    
    **Example:**
    ```bash
    curl -X POST "http://localhost:8080/jobs" \
         -H "Content-Type: application/json" \
         -d '{
           "title": "Senior Python Developer",
           "company": "Tech Corp",
           "location": "Remote",
           "description": "Looking for experienced Python developer...",
           "experience_level": "Senior",
           "job_type": "Full-time",
           "remote_option": "Remote",
           "salary_range": "$120k-$150k"
         }'
    ```
    """
    try:
        db_job = JobsDatabase(
            job_name=job.job_name,
            title=job.title,
            link=job.link,
            description=job.description,
            experience_level=job.experience_level,
            location=job.location,
            company=job.company,
            salary_range=job.salary_range,
            job_type=job.job_type,
            remote_option=job.remote_option
        )
        
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        
        return db_job
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating job: {str(e)}")

@app.post("/jobs/bulk", tags=["Job Management"])
def create_jobs_bulk(jobs: List[JobCreate], db: Session = Depends(get_db)):
    """
    Create multiple job postings at once
    
    **Example:**
    ```bash
    curl -X POST "http://localhost:8080/jobs/bulk" \
         -H "Content-Type: application/json" \
         -d '[
           {
             "title": "Backend Developer",
             "company": "StartupXYZ",
             "location": "New York"
           },
           {
             "title": "Frontend Developer",
             "company": "StartupXYZ",
             "location": "New York"
           }
         ]'
    ```
    """
    try:
        db_jobs = []
        for job in jobs:
            db_job = JobsDatabase(
                job_name=job.job_name,
                title=job.title,
                link=job.link,
                description=job.description,
                experience_level=job.experience_level,
                location=job.location,
                company=job.company,
                salary_range=job.salary_range,
                job_type=job.job_type,
                remote_option=job.remote_option
            )
            db_jobs.append(db_job)
        
        db.add_all(db_jobs)
        db.commit()
        
        return {
            "success": True,
            "message": f"Successfully created {len(db_jobs)} jobs",
            "count": len(db_jobs)
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating jobs: {str(e)}")

@app.get("/jobs", tags=["Job Management"])
def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    company: Optional[str] = None,
    location: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get list of all jobs with optional filters"""
    query = db.query(JobsDatabase)
    
    if company:
        query = query.filter(JobsDatabase.company.ilike(f"%{company}%"))
    if location:
        query = query.filter(JobsDatabase.location.ilike(f"%{location}%"))
    
    total = query.count()
    jobs = query.order_by(JobsDatabase.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "jobs": jobs
    }

@app.get("/jobs/{job_id}", response_model=JobResponse, tags=["Job Management"])
def get_job(job_id: int, db: Session = Depends(get_db)):
    """Get a specific job by ID"""
    job = db.query(JobsDatabase).filter(JobsDatabase.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.delete("/jobs/{job_id}", tags=["Job Management"])
def delete_job(job_id: int, db: Session = Depends(get_db)):
    """Delete a job by ID"""
    job = db.query(JobsDatabase).filter(JobsDatabase.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    db.delete(job)
    db.commit()
    
    return {"success": True, "message": f"Job {job_id} deleted successfully"}

# ==================== GENERAL ENDPOINTS ====================

@app.get("/", tags=["General"])
def root():
    """API information"""
    return {
        "service": "Simple CV Upload & Job Match API",
        "version": "3.0.0",
        "main_endpoint": "/upload-cv (POST with PDF file)",
        "job_management": {
            "create_job": "POST /jobs",
            "bulk_create": "POST /jobs/bulk",
            "list_jobs": "GET /jobs",
            "get_job": "GET /jobs/{job_id}",
            "delete_job": "DELETE /jobs/{job_id}"
        },
        "description": "Upload your CV PDF and instantly get review + job recommendations",
        "docs": "/docs"
    }

@app.get("/health", tags=["General"])
def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "service": "cv-job-match-api",
        "timestamp": datetime.utcnow()
    }

@app.get("/stats", tags=["Statistics"])
def get_stats(db: Session = Depends(get_db)):
    """Get database statistics"""
    total_jobs = db.query(JobsDatabase).count()
    
    return {
        "total_jobs": total_jobs,
        "service": "ready",
        "last_updated": datetime.utcnow()
    }

# ==================== RUN SERVER ====================
if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Simple CV Upload & Job Match API...")
    print("📚 API Documentation: http://localhost:8080/docs")
    print("🎯 Main Endpoint: POST http://localhost:8080/upload-cv")
    print("💼 Job Management: POST /jobs, GET /jobs")
    print("💡 Just upload your CV PDF and get everything instantly!")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")