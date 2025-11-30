# Resumflus 📝

**Resumflus — Aplikasi Reviewer CV Berbasis AI**  
Upload CV dalam format PDF, lalu dapatkan feedback otomatis: struktur, kata kunci, relevansi pengalaman, dan saran perbaikan — powered by Google Cloud & model Gemini.

## ✨ Fitur Utama

- ✅ Upload CV PDF via web  
- ✅ Analisis otomatis menggunakan backend + Gemini (via Ollama / Cloud)  
- ✅ Feedback naratif & terstruktur (struktur CV, kata kunci, pengalaman, saran)  
- ✅ UI front-end yang bersih & responsif (drag & drop / klik upload)  
- ✅ Tidak perlu setup kompleks — cukup clone, install, dan jalankan  

## 🧰 Teknologi / Stack

| Layer | Teknologi |
|-------|-----------|
| Frontend | Next.js / React + TypeScript + Tailwind CSS |
| Backend | FastAPI (Python) |
| AI / Model | Gemini (via Ollama / Cloud Run) |
| Deployment (opsional) | Google Cloud / Cloud Run / Docker |

## 🚀 Cara Memulai (Local Development)

```bash
# Clone repository
git clone https://github.com/ardwiinoo/Resumflus.git
cd Resumflus

# Frontend
cd fe
npm install
npm run dev       # Buka http://localhost:3000

# Backend
cd ../backend     # sesuaikan jika nama folder berbeda
pip install -r requirements.txt
uvicorn main:app --reload   # default: http://localhost:8000
