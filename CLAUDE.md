# Contexte du projet – Service IA Fish Farm

> **Référence : le manuel de stage** (`manuel_stage/Manuel_eBIHAR_etu_001644.docx`, sections
> « Intégration des LLM », « Architecture logicielle », « Service IA et modèle de langage »).
> C'est le document lu par le jury : en cas de doute, le manuel prime sur ce fichier
> et sur `AI/AI_architecture.md` (plan Sprint 1, antérieur au manuel).

## 1. Présentation

Fish Farm est une plateforme de gestion piscicole (Fish Farm Anosy) : API Django, frontend
Next.js, base PostgreSQL. On y intègre un service IA qui **explique en langage naturel**
les indicateurs et les alertes produits par la plateforme et propose des actions.

L'IA est un **outil d'aide à la décision** : elle ne prend aucune décision métier, et
**la plateforme doit rester utilisable sans elle** (coupure, coût, indisponibilité du LLM).

## 2. Architecture générale

Trois logiciels indépendants, qui ne communiquent que par des **API REST en JSON** :

**Django – Backend principal (source de vérité)**
- Utilisateurs, authentification JWT, matrice de permissions (`PermissionMatrice`).
- Données métier, règles de gestion, PostgreSQL.
- **Calcule les indicateurs** (poids moyen, gain de poids, GMQ, biomasse, ICA, survie).
- **Produit les alertes à seuils** (ex. `PESEE_EN_RETARD`, `POIDS_VENTE_ATTEINT`).
- Historise les données et les indicateurs (`IndicateurLot`).

**FastAPI – Service IA (ce dépôt)**
- **Ne fait aucun calcul et aucune détection** : il interprète ce que Django a produit.
- Reçoit de Django l'identifiant d'un lot **et l'alerte à expliquer**.
- **Récupère lui-même** auprès de l'API Django les indicateurs du lot, ses alertes et son
  contexte d'élevage.
- Orchestre l'analyse avec un workflow LangGraph.
- Appelle le LLM via un **client isolé** : **Google Gemini pour les tests**,
  **GPT-6.2 Sol en production** ; changer de modèle ne doit pas modifier le workflow.
- Valide la réponse avec Pydantic avant de la renvoyer.

## 3. Principe de fonctionnement

1. L'utilisateur demande l'explication d'une alerte depuis le frontend.
2. Django vérifie ses droits.
3. Django appelle la route d'analyse du service IA avec `lot_id` + l'alerte à expliquer.
4. Le service IA récupère auprès de Django les indicateurs, alertes et contexte du lot.
5. Le workflow LangGraph prépare le contexte, appelle le LLM, vérifie la réponse.
6. Pydantic valide la structure.
7. FastAPI renvoie le résultat à Django, qui le transmet au frontend.

## 4. Organisation du service (4 couches)

| Couche | Rôle | Dossier |
|---|---|---|
| API | Route d'analyse (lot + alerte), `/health` | `app/api/`, `app/main.py` |
| Services | Client HTTP vers l'API Django (indicateurs, alertes, contexte) | `app/services/` |
| Workflow | Graphe LangGraph | `app/workflows/` |
| Client LLM | Abstraction du fournisseur (Gemini / GPT-6.2 Sol) | `app/ai/` |

Schémas Pydantic : `app/schemas/`. Configuration : `app/core/config.py`.

## 5. Workflow LangGraph (3 étapes contrôlées)

1. `prepare_context` : construit le contexte (indicateurs, alerte, contexte d'élevage) et
   les **consignes métier propres au type d'alerte**.
2. `call_llm` : appelle le modèle via le client LLM.
3. `validate_response` : vérifie et met en forme la réponse.

## 6. Format de la réponse (3 parties)

- **Constat** : ce que montrent les indicateurs et l'alerte (faits uniquement).
- **Explication** : causes possibles, formulées comme des hypothèses.
- **Action proposée** : recommandation cohérente avec les données et les règles métier.

## 7. Règles d'architecture

- Django est l'unique source de vérité ; le service IA ne recalcule pas les indicateurs et
  n'accède jamais directement à la base (lecture via l'API Django uniquement).
- Une alerte repose toujours sur un seuil ou une règle explicite **définis côté Django**.
- Le LLM n'invente ni valeurs, ni seuils, ni alertes, ni causes présentées comme certaines ;
  il ne recalcule pas et ne modifie pas les indicateurs fournis.
- Les causes non confirmées par les données sont présentées comme des hypothèses.
- **Seuls des indicateurs agrégés quittent la plateforme**, jamais les données brutes.
- L'offre gratuite de Gemini autorise Google à réutiliser les données : **uniquement des
  données de test** avec Gemini.
- Les réponses du LLM sont structurées et validées avant usage.
- En cas d'échec du LLM, renvoyer une erreur propre : la plateforme fonctionne sans l'IA.
- Priorités : sécurité, validation des entrées, gestion des erreurs, séparation des
  responsabilités. Pas de RAG ni d'auto-hébergement du modèle à ce stade.

## 8. État actuel du code (à rattraper par rapport au manuel)

Réalisé : structure du projet, `/health`, configuration (`pydantic-settings`), tests pytest,
conteneur Docker.

Provisoire (remplacé par le client Django à l'étape 3) :
- `app/mock_data.py` : 5 lots-scénarios au format Django `suivi` (LOT001 normal, LOT002
  pesée en retard, LOT003 poids de vente atteint, LOT006 alertes simulées mortalité /
  oxygène / température, LOT009 données incomplètes).
- `app/services/source_simulee.py` : `SourceSimulee`, implémentation du contrat
  `SourceDonnees` (`app/services/source_donnees.py`).
- L'ancien calculateur de KPI (`kpi_calculator.py`), `data_loader.py` et
  `analysis_service.py` ont été supprimés (2026-11-25) : contraires au manuel.

Route Django déjà disponible pour l'intégration :
`GET /api/v1/grossissement/lots-grossissement/{id}/suivi/?date_reference=YYYY-MM-DD`
(renvoie `lot`, `dernieres_valeurs`, `alertes`…). Alertes produites aujourd'hui par Django :
`PESEE_EN_RETARD`, `POIDS_VENTE_ATTEINT` (`apps/grossissement/calculs.py::alertes_suivi`).

## 9. Décisions prises (2026-11-25)

1. **Authentification FastAPI → Django : compte de service.** Un utilisateur Django dédié,
   en lecture seule, dont les identifiants sont dans le `.env` du service IA (jamais versionnés).
   FastAPI obtient un JWT via `POST /api/auth/login/` et le renouvelle via
   `POST /api/auth/refresh/` (SimpleJWT).
2. **Alertes : d'abord simulées, puis mises en place proprement dans Django avant l'intégration.**
   - Les alertes simulées vivent dans les **données simulées au format de la réponse Django**
     (`suivi`), pas dans une logique de détection FastAPI : le service IA les lit, il ne les
     calcule pas. Le passage aux vraies données ne change donc que la source.
   - Les alertes de mortalité, d'oxygène et de température seront ensuite implémentées
     **dans Django**, avec des seuils explicites.
3. **Contexte d'élevage** : les routes Django à utiliser seront identifiées et, si besoin,
   créées pendant l'étape 2 (voir la feuille de route).

## 10. Feuille de route (implémentation progressive)

Chaque tâche est livrée avec ses tests et validée (`pytest` vert) avant la suivante.

**Étape 1 – Service IA complet sur données simulées (FastAPI)**
- [x] 1.1 Schémas Pydantic (`app/schemas/suivi.py`, `app/schemas/analyse.py`) : requête d'analyse (`lot_id`, code de l'alerte), données de suivi
      au format Django (`lot`, `dernieres_valeurs`, `alertes`), réponse
      (constat / explication / action proposée).
- [x] 1.2 Source de données abstraite + implémentation simulée : réécrire `mock_data.py` au
      format `suivi` de Django, avec des alertes réelles (`PESEE_EN_RETARD`,
      `POIDS_VENTE_ATTEINT`) et simulées (mortalité, oxygène, température), sur plusieurs
      lots-scénarios. Retirer `kpi_calculator.py` (contraire au manuel).
- [x] 1.3 Client LLM abstrait : un faux client déterministe pour les tests, puis Gemini
      (`app/ai/` : `client_llm.py`, `faux_client.py`, `client_langchain.py`, `fabrique.py`).
      Client générique (`init_chat_model`) : **changer de modèle = changer `LLM_MODEL`**
      (format `fournisseur:modele`, ex. `google_genai:gemini-2.5-flash`,
      `openai:gpt-6.2-sol`) et `LLM_API_KEY` dans `.env`. Pour un nouveau fournisseur,
      ajouter son connecteur LangChain à `requirements.txt` (ex. `langchain-openai`).
- [ ] 1.4 Workflow LangGraph en 3 étapes (`prepare_context`, `call_llm`, `validate_response`),
      avec les consignes métier par type d'alerte.
- [ ] 1.5 Route `POST /api/v1/ai/analyze` + gestion d'erreurs (lot ou alerte inconnus, LLM
      indisponible → erreur propre, la plateforme reste utilisable).

**Étape 2 – Alertes et contexte d'élevage côté Django (avant l'intégration)**
- [ ] 2.1 Nettoyer les alertes existantes : catalogue unique (code, niveau, message, seuil,
      valeurs), même format partout.
- [ ] 2.2 Ajouter les alertes de mortalité, d'oxygène et de température avec des seuils
      explicites et configurables, et les tests Django correspondants.
- [ ] 2.3 Contexte d'élevage : identifier les routes existantes (`/api/v1/environnement/`,
      `/api/v1/provende/`, `/api/v1/effectifs/`), décider de ce qui est transmis (agrégats
      seulement) et créer, si besoin, une route agrégée dédiée au service IA.
- [ ] 2.4 Aligner les données simulées FastAPI sur le format final des alertes.

**Étape 3 – Intégration FastAPI ↔ Django**
- [ ] 3.1 Compte de service Django (rôle en lecture seule, accès limité aux routes utiles).
- [ ] 3.2 Client HTTP Django dans le service IA (login/refresh JWT, délais d'expiration,
      erreurs) : il remplace la source simulée sans changer le workflow.
- [ ] 3.3 Un seul `docker-compose` : frontend (3000), backend (8000), service IA (**pas 8000**,
      ex. 8001), PostgreSQL, sur un réseau commun.
- [ ] 3.4 Django appelle la route d'analyse du service IA.

**Étape 4 – Interface**
- [ ] 4.1 Bouton « Expliquer l'alerte » dans Next.js et affichage de la réponse en 3 parties.

## 11. Points encore ouverts

- **Rôle du compte de service** : les rôles actuels sont Administrateur, Directeur,
  Gestionnaire et Employé. Créer un rôle dédié en lecture seule (recommandé) ou en réutiliser un ?
- **Django → FastAPI** : comment le service IA authentifie-t-il les appels de Django sur
  `/api/v1/ai/analyze` (secret partagé, réseau interne uniquement) ?
- **Seuils** des alertes de mortalité, d'oxygène et de température : valeurs à valider avec
  l'exploitation (dépendent de l'espèce et du stade).
- Constaté dans `config/settings.py` de Django : `ACCESS_TOKEN_LIFETIME` (15 jours) est plus
  long que `REFRESH_TOKEN_LIFETIME` (7 jours). C'est inhabituel, à vérifier.

## 12. Consignes de développement

Agis comme un développeur Python/FastAPI expérimenté, spécialisé dans les services IA.

**Je suis encore apprenti** et je veux renforcer mes compétences en IA générative :
- Guide-moi de la manière la plus pédagogique et la plus simple possible.
- Avance par petites étapes, en expliquant chaque notion nouvelle (Pydantic, LangGraph,
  prompts, client LLM…) avec des mots simples et un exemple tiré du projet.
- Après chaque étape, explique clairement **quoi** (ce qui a été fait), **pourquoi** (le
  besoin, le lien avec le manuel) et **comment** (le fonctionnement du code, les fichiers).
- Montre-moi comment vérifier par moi-même (commandes, ce qu'on doit voir).

- Respecte l'architecture ci-dessus et la structure de fichiers existante.
- Réutilise les composants existants ; pas de dépendances inutiles ni de duplication.
- Signale toute ambiguïté métier susceptible de changer le comportement attendu.
- Pour chaque fonctionnalité : rôle en bref, code complet commenté sur les parties
  importantes, changements Docker / dépendances, tests automatisés, commandes de test.
- Avance par étapes mais efficacement, sans demander validation à chaque petite étape.
- Ne modifie pas arbitrairement l'architecture ni les règles métier.

## 13. Commandes

```powershell
docker compose build                                   # si requirements.txt change
docker compose run --rm ai-service python -m pytest -v # tests (47 passent, 1 ignoré, au 2026-11-25)
# Appel RÉEL au modèle de LLM_MODEL (réseau + quota ; données simulées uniquement) :
docker compose run --rm -e TEST_LLM_REEL=1 ai-service python -m pytest tests/test_client_llm_reel.py -v -s
```
