from typing import Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration lue dans les variables d'environnement / le fichier .env.

    Ex. : LLM_MODEL=google_genai:gemini-2.5-flash dans .env
          -> settings.llm_model == "google_genai:gemini-2.5-flash".
    """

    app_env: str = "development"

    # --- Modèle de langage ---
    # Format "fournisseur:modele". Changer de modèle = changer cette valeur (+ la clé).
    #   tests      : google_genai:gemini-2.5-flash
    #   production : openai:gpt-6.2-sol   (nécessite le paquet langchain-openai)
    llm_model: str = "google_genai:gemini-2.5-flash"
    llm_api_key: str = ""  # clé du fournisseur choisi ; secret : uniquement dans .env
    llm_timeout_s: float = 30.0  # au-delà, on abandonne : la plateforme ne reste pas bloquée
    llm_temperature: Optional[float] = 0.2  # vide = non envoyé (modèles qui le refusent)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("llm_temperature", mode="before")
    @classmethod
    def temperature_vide_vaut_none(cls, valeur):
        return None if valeur == "" else valeur

    @field_validator("llm_model")
    @classmethod
    def modele_avec_fournisseur(cls, valeur: str) -> str:
        # Sans préfixe, LangChain devine le fournisseur et peut se tromper
        # ("gemini-2.5-flash" seul -> Vertex AI au lieu de l'API Gemini).
        fournisseur, separateur, modele = valeur.partition(":")
        if not (fournisseur and separateur and modele):
            raise ValueError(
                f"LLM_MODEL doit avoir la forme 'fournisseur:modele' "
                f"(ex. google_genai:gemini-2.5-flash), reçu : {valeur!r}."
            )
        return valeur


settings = Settings()
