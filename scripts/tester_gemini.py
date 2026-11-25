"""Vérifie que la clé Gemini du fichier .env fonctionne et que le modèle répond.

Usage (depuis le dossier fish-farm-ai) :
    docker compose run --rm ai-service python scripts/tester_gemini.py
    py scripts/tester_gemini.py   # ou directement, si Python est installé sous Windows
    py scripts/tester_gemini.py --modele gemini-3-flash-preview
    py scripts/tester_gemini.py --question "Pourquoi le GMQ baisse-t-il ?"

La clé est lue dans .env (LLM_API_KEY) et n'est jamais affichée.
N'utilise que la bibliothèque standard : aucune installation nécessaire.
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

URL = "https://generativelanguage.googleapis.com/v1beta/models/{modele}:generateContent"
MODELE_PAR_DEFAUT = "gemini-3.5-flash-lite"
QUESTION_PAR_DEFAUT = (
    "Réponds en une phrase, en français : quel est le rôle de l'oxygène "
    "dissous pour les poissons d'élevage ?"
)
AIDE_PAR_CODE = {
    400: "Clé invalide ou région non autorisée : recopiez la clé depuis AI Studio.",
    403: "Accès refusé : recréez la clé depuis AI Studio (l'API sera activée).",
    404: "Modèle introuvable ou fermé aux nouveaux utilisateurs : essayez --modele gemini-3.5-flash-lite.",
    429: "Quota gratuit atteint : attendez une minute (ou le lendemain pour le quota journalier).",
    503: "Modèle surchargé côté Google : réessayez plus tard ou changez de modèle.",
}


def lire_env(chemin: Path) -> dict:
    valeurs = {}
    if not chemin.exists():
        return valeurs
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, valeur = ligne.split("=", 1)
        valeurs[cle.strip()] = valeur.strip().strip('"').strip("'")
    return valeurs


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    env = lire_env(Path(__file__).resolve().parent.parent / ".env")
    parser = argparse.ArgumentParser(description="Teste la clé et le modèle Gemini.")
    parser.add_argument("--modele", default=env.get("LLM_MODEL") or MODELE_PAR_DEFAUT)
    parser.add_argument("--question", default=QUESTION_PAR_DEFAUT)
    args = parser.parse_args()
    # LLM_MODEL a la forme « fournisseur:modele » (ex. google_genai:gemini-2.5-flash) ;
    # l'URL de Google n'attend que le nom du modèle.
    args.modele = args.modele.split(":", 1)[-1]

    cle = env.get("LLM_API_KEY", "")
    if not cle:
        print("ÉCHEC : LLM_API_KEY absente ou vide dans .env")
        return 1
    print(f"Clé trouvée ({len(cle)} caractères, début {cle[:4]}…)")
    print(f"Modèle : {args.modele}")
    print(f"Question : {args.question}\n")

    corps = json.dumps({"contents": [{"parts": [{"text": args.question}]}]}).encode("utf-8")
    requete = urllib.request.Request(
        URL.format(modele=args.modele),
        data=corps,
        headers={"Content-Type": "application/json; charset=utf-8", "x-goog-api-key": cle},
        method="POST",
    )

    debut = time.perf_counter()
    try:
        with urllib.request.urlopen(requete, timeout=60) as reponse:
            donnees = json.loads(reponse.read().decode("utf-8"))
    except urllib.error.HTTPError as erreur:
        try:
            message = json.loads(erreur.read().decode("utf-8"))["error"]["message"]
        except Exception:
            message = "(pas de détail)"
        print(f"ÉCHEC HTTP {erreur.code} : {message}")
        print(f"→ {AIDE_PAR_CODE.get(erreur.code, 'Erreur inattendue.')}")
        return 1
    except (urllib.error.URLError, TimeoutError) as erreur:
        print(f"ÉCHEC réseau : {erreur}")
        print("→ Vérifiez la connexion Internet, puis réessayez.")
        return 1
    duree = time.perf_counter() - debut

    try:
        candidat = donnees["candidates"][0]
        morceaux = candidat.get("content", {}).get("parts", [])
        # Assemble tous les morceaux de texte, sans les éventuelles « pensées » du modèle.
        texte = "".join(p.get("text", "") for p in morceaux if not p.get("thought")).strip()
        raison = candidat.get("finishReason", "inconnue")
    except (KeyError, IndexError):
        texte, raison = "", "inconnue"
    if not texte:
        print(f"ÉCHEC : réponse sans texte (raison d'arrêt : {raison}).")
        print(json.dumps(donnees, ensure_ascii=False, indent=2)[:800])
        return 1

    print(f"OK en {duree:.1f} s (raison d'arrêt : {raison}). Réponse du modèle :")
    print(texte)
    if raison != "STOP" or len(texte) < 20:
        print("\nATTENTION : réponse tronquée ou anormalement courte. Relancez le test ;"
              " si cela se répète, essayez un autre modèle avec --modele.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
