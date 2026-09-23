# Deploying QueueFlow for free

Total cost: ₹0. Three services:

| Piece | Service | Free tier |
|---|---|---|
| Database | MongoDB Atlas | M0 cluster, 512 MB, free forever |
| Backend | Render | Web service, sleeps after inactivity |
| Frontend | Vercel | Hobby plan, generous free limits |

> Render's free backend sleeps after ~15 min of inactivity — the first request
> after sleep takes ~30–60s to wake up. Fine for an MVP/demo.

## 0. Push the code to GitHub

Create a repo (e.g. `queueflow-mvp`) and push both `backend/` and `frontend/` folders.

## 1. Database — MongoDB Atlas

1. Sign up at https://www.mongodb.com/cloud/atlas → create a **free M0** cluster.
2. Database Access → add a database user (username + password). Save them.
3. Network Access → **Add IP Address** → "Allow access from anywhere" (`0.0.0.0/0`).
   (OK for an MVP; tighten later.)
4. Connect → Drivers → copy the connection string. It looks like:
   `mongodb+srv://<user>:<password>@cluster0.xxxxx.mongodb.net/`
   Replace `<user>` / `<password>` with your database user. Append the db name:
   `...mongodb.net/queueflow`

## 2. Backend — Render

1. Sign up at https://render.com (use your GitHub account).
2. **New → Web Service** → connect your repo.
3. Settings:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **Environment variables:**
   - `MONGO_URL` = your Atlas connection string from step 1
   - `DB_NAME` = `queueflow`
   - `JWT_SECRET` = a long random string (generate: `openssl rand -hex 32`)
5. Deploy. When it's live, note your URL, e.g. `https://queueflow-api.onrender.com`.
6. Test: open `https://<your-api>/api/health` → should show `{"ok":true}`.

## 3. Frontend — Vercel

1. Sign up at https://vercel.com (use your GitHub account).
2. **Add New → Project** → import your repo.
3. Settings:
   - **Root Directory:** `frontend`
   - **Environment variable:** `VITE_API_URL` = your Render URL, e.g.
     `https://queueflow-api.onrender.com` (no trailing slash)
4. Deploy. You get a public URL like `https://queueflow-mvp.vercel.app`.

## 4. Try it end to end

1. Open your Vercel URL → Register a business account.
2. Create a queue → open the Manage page → show the QR.
3. Scan the QR with your phone → join with your name → watch the live status.
4. From Manage, hit **Call Next** → phone shows "It's your turn!".

## Before sharing publicly

- [ ] `JWT_SECRET` is a strong random value (not the dev default)
- [ ] No demo/seed accounts with known passwords in the database
- [ ] Atlas network access restricted if you outgrow "allow anywhere"

## Updating later

Just `git push` — Render and Vercel redeploy automatically.
