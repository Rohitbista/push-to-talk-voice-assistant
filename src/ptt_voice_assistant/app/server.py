from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Voice Assistant Server is up and running"}

def main():
    host = "0.0.0.0"
    port = 8000
    uvicorn.run(
        "ptt_voice_assistant.app.server:app",
        host=host,
        port=port,
        reload=False,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )