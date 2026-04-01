# Written by V
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import search, documents, entities, timeline, ask, redactions, changelog

app = FastAPI(
    title="Devil Has Many Faces API",
    description="Declassified document intelligence platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(entities.router, prefix="/entities", tags=["entities"])
app.include_router(timeline.router, prefix="/timeline", tags=["timeline"])
app.include_router(ask.router, prefix="/ask", tags=["ask"])
app.include_router(redactions.router, prefix="/redactions", tags=["redactions"])
app.include_router(changelog.router, prefix="/changelog", tags=["changelog"])

@app.get("/")
def root():
    return {"status": "ok", "message": "Devil Has Many Faces API"}

@app.get("/health")
def health():
    return {"status": "healthy"}