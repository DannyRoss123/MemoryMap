# MemoryMap

MVP for MemoryMap, a web/mobile app for memory timelines, caregiver alerts and wellness tracking.

## Running the project

### Backend

```bash
uvicorn app.main:app --reload
```

### React front-end

```bash
cd frontend
npm install
npm run dev
```

The dev server proxies API calls to the FastAPI backend. Open the URL that Vite prints (defaults to `http://127.0.0.1:5173/`).
