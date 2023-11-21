from fastapi import FastAPI
from . import models, database, auth, chat

# Create Tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Healthcare System API")

# Include Routers
app.include_router(auth.router, tags=["Authentication"])
app.include_router(chat.router, tags=["Chat & Records"])

@app.get("/")
def read_root():
    return {"message": "Healthcare System API is running"}
