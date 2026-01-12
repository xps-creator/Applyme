import os
import datetime

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from jose import jwt
from passlib.hash import bcrypt
from sqlalchemy import create_engine, text

DATABASE_URL = os.environ["DATABASE_URL"]
JWT_SECRET = os.environ.get("APP_JWT_SECRET", "dev")
INTERNAL_API_KEY = os.environ.get("INTERNAL_API_KEY", "dev-internal")
CORS_ORIGIN = os.environ.get("CORS_ORIGIN", "http://localhost:8080")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

app = FastAPI(title="Applyme API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[CORS_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def make_token(user_id: str):
    payload = {"sub": user_id, "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7)}
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")

def require_user(authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing token")
    token = authorization.split(" ", 1)[1]
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return data["sub"]
    except Exception:
        raise HTTPException(401, "Invalid token")

class SignupIn(BaseModel):
    email: EmailStr
    password: str

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class BatchCreateIn(BaseModel):
    field: str
    location: str
    job_type: str

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/auth/signup")
def signup(body: SignupIn):
    pw_hash = bcrypt.hash(body.password)
    with engine.begin() as conn:
        try:
            user_id = conn.execute(
                text("insert into users(email,password_hash) values(:e,:p) returning id"),
                {"e": body.email, "p": pw_hash},
            ).scalar_one()
        except Exception:
            raise HTTPException(409, "Email already exists")
    return {"token": make_token(str(user_id))}

@app.post("/auth/login")
def login(body: LoginIn):
    with engine.begin() as conn:
        row = conn.execute(
            text("select id, password_hash from users where email=:e"),
            {"e": body.email},
        ).mappings().first()

    if not row or not bcrypt.verify(body.password, row["password_hash"]):
        raise HTTPException(401, "Invalid credentials")

    return {"token": make_token(str(row["id"]))}

@app.post("/batches")
def create_batch(body: BatchCreateIn, authorization: str | None = Header(default=None)):
    user_id = require_user(authorization)

    with engine.begin() as conn:
        batch_id = conn.execute(
            text(
                """insert into batches(user_id,status,field,location,job_type)
                   values(:u,'running',:f,:l,:t) returning id"""
            ),
            {"u": user_id, "f": body.field, "l": body.location, "t": body.job_type},
        ).scalar_one()

    return {"batchId": str(batch_id), "status": "running"}

@app.get("/dashboard/{batch_id}")
def dashboard(batch_id: str, authorization: str | None = Header(default=None)):
    user_id = require_user(authorization)

    with engine.begin() as conn:
        b = conn.execute(
            text("select * from batches where id=:id and user_id=:u"),
            {"id": batch_id, "u": user_id},
        ).mappings().first()

        if not b:
            raise HTTPException(404, "Batch not found")

        apps = conn.execute(
            text("select * from applications where batch_id=:id order by created_at desc"),
            {"id": batch_id},
        ).mappings().all()

    return {"batch": dict(b), "applications": [dict(a) for a in apps]}

class AppUpsertIn(BaseModel):
    batchId: str
    jobUrl: str
    company: str | None = None
    title: str | None = None
    recruiterEmail: str | None = None
    status: str
    error: str | None = None

@app.post("/internal/applications/upsert")
def upsert_application(body: AppUpsertIn, x_internal_key: str | None = Header(default=None)):
    if x_internal_key != INTERNAL_API_KEY:
        raise HTTPException(403, "Forbidden")

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                insert into applications(batch_id, job_url, company, title, recruiter_email, status, error)
                values(:b,:u,:c,:t,:re,:s,:e)
                on conflict (batch_id, job_url) do update set
                  company=excluded.company,
                  title=excluded.title,
                  recruiter_email=excluded.recruiter_email,
                  status=excluded.status,
                  error=excluded.error
                """
            ),
            {
                "b": body.batchId,
                "u": body.jobUrl,
                "c": body.company,
                "t": body.title,
                "re": body.recruiterEmail,
                "s": body.status,
                "e": body.error,
            },
        )

    return {"ok": True}