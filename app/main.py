from fastapi import FastAPI

from app.api.analyse import router as router_analyse

app = FastAPI(
    title="Fish Farm AI Service",
    version="0.1.0",
)

# Les routes d'analyse sont définies dans app/api/ (couche API du manuel).
app.include_router(router_analyse)


@app.get("/health")
def health_check():
    return {"status": "ok"}
