# Here are your Instructions
# PANOPTES-ICU

Real-time ICU sepsis risk prediction system. Combines a GRU-D + VAE deep learning pipeline for time-series vitals with an LLM-powered clinical assistant to flag at-risk patients early.

## Overview

PANOPTES-ICU ingests ICU time-series vitals, handles missing data natively via GRU-D, and uses a VAE component for representation learning to predict sepsis risk. Predictions and alerts are surfaced through a web dashboard, with the Claude API layered in for clinical context and explanation of risk factors.

## Tech Stack

**ML / Backend**
- PyTorch (GRU-D, VAE)
- FastAPI
- MongoDB (alert persistence)
- Claude API (clinical reasoning / explanations)

**Frontend**
- React

**Deployment**
- Railway (separate backend and frontend services)
- Docker

## Architecture

```
Vitals stream → GRU-D (handles missingness) → VAE (latent representation)
            → Sepsis risk score → FastAPI → MongoDB (alerts)
            → React dashboard
            → Claude API (risk explanation / clinical context)
```

## Live Deployment

- Backend: https://panoptes-icu1-production.up.railway.app
- Frontend: https://frontend-production-320f.up.railway.app

Backend runs FastAPI on port 8001. MongoDB is connected internally within Railway for alert persistence.

## Key Engineering Challenges

- Resolved Dockerfile conflicts between backend and frontend services during deployment
- Handled React build-time environment variable baking so the frontend correctly points to the deployed backend
- Configured CORS between the Railway-hosted frontend and backend services

## Getting Started

### Prerequisites
- Python 3.x
- Node.js
- MongoDB instance

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001
```

### Frontend
```bash
cd frontend
npm install
npm run build
npm start
```

### Environment Variables
Set MongoDB connection string, Claude API key, and any React build-time variables required by the frontend before building.

## Model

- **GRU-D**: Gated Recurrent Unit with trainable decay, designed for irregularly sampled clinical time-series with missing values.
- **VAE**: Variational Autoencoder used for learning compact latent representations of patient state, feeding into the risk prediction head.

## License

Add your preferred license here.
