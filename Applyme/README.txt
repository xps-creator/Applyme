Applyme (HTML/CSS + API + Postgres + n8n) - Local

1) Démarrer:
   docker compose up --build

2) Ouvrir:
   Web: http://localhost:8080
   API: http://localhost:8000/health
   n8n: http://localhost:5678

3) n8n:
   - Import workflow: infra/n8n/workflows/applyme_mvp.json
   - Active le workflow (toggle "Active")
   - Pour déclencher:
       POST http://localhost:5678/webhook/applyme-batch
     avec JSON:
       { "batchId": "<ton batchId>" }

4) Utilisation (web):
   - Ouvre http://localhost:8080
   - Signup ou Login
   - Create batch
   - Copie le batchId affiché
   - Déclenche le webhook n8n avec ce batchId
   - Refresh dashboard pour voir les applications