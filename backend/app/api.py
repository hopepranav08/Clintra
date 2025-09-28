from fastapi import FastAPI

app = FastAPI(title="Clintra API")

@app.get("/")
def root():
    return {"message": "Clintra Backend Running 🚀"}
