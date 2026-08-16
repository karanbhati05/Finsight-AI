# 🚀 FinSight AI — Production Deployment Guide

This guide details the simplest and most cost-effective ways to deploy **FinSight AI** live to the web.

---

## 🌟 Option 1: Free Cloud Deployment (Recommended)
Deploy the **Frontend on Vercel** (Free) and **Backend on Render** (Free).

### Step 1: Deploy Backend on Render
1. Push your repository to GitHub: `git push origin main`
2. Go to [Render Dashboard](https://dashboard.render.com/) and click **New + ➡️ Web Service**.
3. Connect your GitHub repository (`Finsight-AI`).
4. Set the following settings:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.api.main:app --host 0.0.0.0 --port $PORT`
5. Under **Environment Variables**, add:
   ```env
   GOOGLE_API_KEY=AIzaSyCctea-E7IEYRQDQqI028HBdA5V7EmS7EY
   FRED_API_KEY=eaba6c9f1737955026db537f642fa823
   ALPHA_VANTAGE_KEY=RZBN6DLS224DD7TR
   FMP_API_KEY=Oc1KRyXSStyXYQyizmkJT9dAc0YcuNqC
   FINNHUB_API_KEY=d806n9pr01qj3ct98l10d806n9pr01qj3ct98l1g
   COINGECKO_API_KEY=CG-RSwn3EXY6HxMZFNwaB8zPGeQ
   NEWS_API_KEY=13539a3c597845b19345f9a11724060f
   USE_TF=0
   USE_TORCH=1
   ```
6. Click **Create Web Service**. Your backend will be live at `https://finsight-backend.onrender.com`.

---

### Step 2: Deploy Frontend on Vercel
1. Go to [Vercel](https://vercel.com/) and click **Add New Project**.
2. Select your `Finsight-AI` repository.
3. Configure the project:
   - **Root Directory**: `frontend`
   - **Framework Preset**: `Vite`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Under **Environment Variables**, add:
   ```env
   VITE_API_URL=https://finsight-backend.onrender.com/api
   ```
5. Click **Deploy**! Your frontend will be live at `https://finsight-ai.vercel.app`.

---

## 🐳 Option 2: 1-Click Docker Compose (Any VPS / Server)

If you have a Linux VPS (DigitalOcean, AWS EC2, Linode, Hetzner):

1. Clone your repo:
   ```bash
   git clone https://github.com/karanbhati05/Finsight-AI.git
   cd Finsight-AI
   ```
2. Create your `.env` file with your API keys:
   ```bash
   cp .env.example .env
   # Add your API keys to .env
   ```
3. Start the entire institutional stack (Backend + Frontend + Redis):
   ```bash
   docker compose up -d --build
   ```
4. Access your live terminal:
   - **Frontend**: `http://<your-server-ip>:5173`
   - **Backend API Docs**: `http://<your-server-ip>:8000/docs`

---

## 🚂 Option 3: Railway 1-Click Deployment

1. Go to [Railway.app](https://railway.app/)
2. Click **New Project ➡️ Deploy from GitHub repo**.
3. Railway will automatically detect the `Procfile` and `requirements.txt`.
4. Add your API variables under **Variables**, and Railway will deploy your live API endpoint.
