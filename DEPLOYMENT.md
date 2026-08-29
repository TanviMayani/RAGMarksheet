# Free Deployment Guide 🚀

You can deploy this Marksheet RAG application **100% freely** using any of the following methods.

---

## Option 1: Streamlit Community Cloud (Easiest & Fastest ⭐)

Streamlit Community Cloud is **completely free** and directly connects to your GitHub repository. Since we have configured the frontend to auto-start the FastAPI backend in the background if hosted together, you only need one single deployment!

### Step 1: Push Code to GitHub
1. Create a new repository on [GitHub](https://github.com/new).
2. Initialize git and push your project code:
   ```bash
   git init
   git add .
   git commit -m "Initial commit for deployment"
   git branch -M main
   git remote add origin https://github.com/<your-username>/<your-repo-name>.git
   git push -u origin main
   ```

### Step 2: Deploy on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io/) and sign in with your GitHub account.
2. Click **"New app"**.
3. Fill in the deployment details:
   - **Repository**: `<your-username>/<your-repo-name>`
   - **Branch**: `main`
   - **Main file path**: `frontend/app.py`
4. Click **"Advanced settings..."** -> **"Secrets"**, and paste your API key:
   ```toml
   OPENROUTER_API_KEY = "your-openrouter-api-key-here"
   OPENROUTER_LLM_MODEL = "nvidia/nemotron-3.5-lightning:free"
   OPENROUTER_EMBEDDING_MODEL = "liquid/lfm2.5-embedding-350m"
   ```
5. Click **"Deploy!"**
6. Your application will be live at `https://<your-app-name>.streamlit.app` in 1-2 minutes!

---

## Option 2: Hugging Face Spaces (Best Performance: 16 GB RAM + 2 vCPU ⭐)

Hugging Face Spaces provides a **free 16 GB RAM container** with no credit card required.

### Step 1: Create a Space
1. Sign up or log in at [Hugging Face](https://huggingface.co/).
2. Go to [huggingface.co/new-space](https://huggingface.co/new-space).
3. Name your space (e.g., `marksheet-rag`).
4. Select **Space SDK**: **Docker** (Blank).
5. Set Space hardware to **Free (2 vCPU, 16 GB RAM)**.
6. Click **"Create Space"**.

### Step 2: Configure Environment Secret
1. In your newly created Space, go to **Settings** -> **Variables and secrets**.
2. Under **Secrets**, click **"New secret"**:
   - **Name**: `OPENROUTER_API_KEY`
   - **Value**: `your-openrouter-api-key-here`

### Step 3: Push Your Code
Follow the instructions shown on Hugging Face to push your repo:
```bash
git remote add space https://huggingface.co/spaces/<your-hf-username>/marksheet-rag
git push space main
```
Hugging Face will automatically build the `Dockerfile`, start the backend + Streamlit frontend, and give you a public URL!

---

## Option 3: Render (FastAPI Backend) + Streamlit Cloud (Frontend)

If you prefer separating backend and frontend services on free tiers:

### 1. Deploy Backend on Render (Free Web Service)
1. Sign up on [Render.com](https://render.com/).
2. Click **"New +"** -> **"Web Service"** and connect your GitHub repository.
3. Settings:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Add Environment Variables:
   - `OPENROUTER_API_KEY`: `your_key_here`
   - `OPENROUTER_LLM_MODEL`: `nvidia/nemotron-3.5-lightning:free`
   - `OPENROUTER_EMBEDDING_MODEL`: `liquid/lfm2.5-embedding-350m`
5. Click **"Create Web Service"**. Copy your Render backend URL (e.g. `https://marksheet-backend.onrender.com`).

### 2. Deploy Frontend on Streamlit Cloud
1. Deploy `frontend/app.py` on [share.streamlit.io](https://share.streamlit.io/).
2. In **Secrets**, add:
   ```toml
   API_URL = "https://marksheet-backend.onrender.com"
   ```

---

## Summary Comparison

| Platform | Cost | Setup Time | RAM / Resources | Best For |
| :--- | :--- | :--- | :--- | :--- |
| **Streamlit Community Cloud** | Free | ~2 mins | ~1 GB | Quickest 1-click deploy |
| **Hugging Face Spaces (Docker)** | Free | ~3 mins | 16 GB RAM, 2 vCPU | Heavy OCR & PDF loads |
| **Render + Streamlit Cloud** | Free | ~5 mins | 512 MB (Render) | Split microservices |
