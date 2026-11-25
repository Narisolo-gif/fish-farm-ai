"""Contrat de la route d'analyse du service IA.

- AnalyseRequest  : ce que Django envoie (le lot et l'alerte à expliquer).
- ReponseLLM      : ce que le LLM DOIT produire (les 3 parties du manuel).
- AnalyseResponse : ce que le service IA renvoie à Django.

`extra="forbid"` refuse tout champ non prévu : une entrée ou une sortie inattendue
est rejetée au lieu d'être utilisée en silence.
"""

from pydantic import BaseModel, ConfigDict, Field


class AnalyseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lot_id: int = Field(gt=0, description="Identifiant du lot de grossissement dans Django")
    code_alerte: str = Field(
        pattern=r"^[A-Z][A-Z0-9_]*$",  # format des codes Django, ex. PESEE_EN_RETARD
        max_length=50,
        description="Code de l'alerte à expliquer",
    )


class ReponseLLM(BaseModel):
    """Réponse structurée attendue du LLM.

    Ce schéma sera aussi donné au LLM (structured output) pour lui imposer ce format.
    `str_strip_whitespace` retire les espaces en trop ; `min_length=1` interdit une
    partie vide.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    constat: str = Field(
        min_length=1,
        description="Ce que montrent l'alerte et les indicateurs. Faits uniquement.",
    )
    explication: str = Field(
        min_length=1,
        description="Causes possibles, formulées comme des hypothèses si non confirmées.",
    )
    action_proposee: str = Field(
        min_length=1,
        description="Action concrète, cohérente avec les données et les règles métier.",
    )


class AnalyseResponse(BaseModel):
    lot_id: int
    code_alerte: str
    analyse: ReponseLLM
