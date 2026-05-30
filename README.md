# SNDE — Backend API (Flask + MongoDB)

## Installation locale

```bash
# 1. Cloner le projet
git clone https://github.com/TON_COMPTE/snde-backend.git
cd snde-backend

# 2. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
cp .env.example .env
# Ouvrir .env et remplir MONGO_URI et JWT_SECRET

# 5. Lancer le serveur
python app.py
# → API disponible sur http://localhost:5000
```

## Structure du projet

```
snde_backend/
├── app.py                  # Point d'entrée principal
├── requirements.txt        # Dépendances Python
├── Procfile                # Pour Railway/Render
├── .env.example            # Template des variables d'environnement
├── config/
│   └── database.py         # Connexion MongoDB
├── middleware/
│   └── auth.py             # JWT + vérification des rôles
└── routes/
    ├── auth.py             # Authentification et gestion users
    ├── incidents.py        # CRUD incidents
    ├── stats.py            # Statistiques et tableau de bord
    └── export.py           # Export Excel + import migration
```

## Routes API

### Authentification (`/api/auth`)

| Méthode | Route | Rôle requis | Description |
|---------|-------|-------------|-------------|
| POST | `/login` | Aucun | Connexion — retourne un token JWT |
| POST | `/register` | admin | Créer un utilisateur |
| GET | `/me` | Connecté | Infos de l'utilisateur connecté |
| PUT | `/change-password` | Connecté | Changer son mot de passe |
| GET | `/users` | admin | Lister tous les utilisateurs |
| PUT | `/users/:id` | admin | Modifier rôle/brigade d'un user |

### Incidents (`/api/incidents`)

| Méthode | Route | Rôle requis | Description |
|---------|-------|-------------|-------------|
| POST | `/` | Connecté | Signaler un nouvel incident |
| GET | `/` | Connecté | Lister les incidents (filtré par rôle) |
| GET | `/:id` | Connecté | Détail d'un incident |
| PUT | `/:id` | Connecté | Mettre à jour un incident |
| DELETE | `/:id` | admin | Supprimer un incident |
| GET | `/referentiels/sites` | Connecté | Liste des sites |
| GET | `/referentiels/brigades` | Connecté | Liste des brigades |

#### Paramètres de filtrage (GET `/api/incidents`)
- `statut` : En attente / En cours / Achevé / Abandonné
- `site` : nom du site (recherche partielle)
- `brigade` : nom de la brigade
- `impact` : Faible / Moyen / Majeur
- `search` : recherche texte dans description/site/localisation
- `date_debut` / `date_fin` : format ISO (2026-01-01)
- `page` : numéro de page (défaut: 1)
- `limit` : résultats par page (défaut: 50)

### Statistiques (`/api/stats`)

| Méthode | Route | Rôle requis | Description |
|---------|-------|-------------|-------------|
| GET | `/dashboard` | directeur, admin, chef_brigade | KPIs tableau de bord |
| GET | `/en-attente-critique` | Connecté | Incidents Majeur > 24h non traités |

#### Paramètres dashboard
- `brigade` : filtrer par brigade (directeur/admin)
- `site` : filtrer par site
- `annee` : filtrer par année (ex: 2026)

### Export (`/api/export`)

| Méthode | Route | Rôle requis | Description |
|---------|-------|-------------|-------------|
| GET | `/excel` | directeur, admin | Export Excel compatible fichier SNDE |
| POST | `/import-excel` | admin | Import migration données historiques |

## Rôles et permissions

| Rôle | Incidents vus | Peut modifier | Accès dashboard |
|------|--------------|---------------|-----------------|
| `employe` | Ses propres incidents | Ses incidents en attente | Non |
| `chef_brigade` | Incidents de sa brigade | Incidents de sa brigade | Oui (sa brigade) |
| `directeur` | Tous les incidents | Non | Oui (tout) |
| `admin` | Tous les incidents | Tout + supprimer | Oui (tout) |

## Compte admin initial

Au premier démarrage, un compte admin est créé automatiquement :
- Email : `admin@snde.mr`
- Mot de passe : `Admin1234!`
- **Changer ce mot de passe immédiatement après la première connexion.**

## Déploiement Railway

1. Créer un compte sur [railway.app](https://railway.app)
2. New Project → Deploy from GitHub → sélectionner ce dépôt
3. Dans Variables, ajouter :
   - `MONGO_URI` = ton URL MongoDB Atlas
   - `JWT_SECRET` = une clé secrète longue et aléatoire
4. Railway déploie automatiquement — URL fournie en quelques minutes

## Exemple d'appel API (avec curl)

```bash
# 1. Connexion
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@snde.mr","password":"Admin1234!"}'

# 2. Signaler un incident (remplacer TOKEN par le token reçu)
curl -X POST http://localhost:5000/api/incidents \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "site": "Idini",
    "localisation": "Wad Naga/Trarza",
    "description": "Arrêt du forage F24, pompe à la masse",
    "impact": "Majeur",
    "brigade": "Brigade d'\''Idini"
  }'

# 3. Tableau de bord directeur
curl http://localhost:5000/api/stats/dashboard \
  -H "Authorization: Bearer TOKEN"
```
