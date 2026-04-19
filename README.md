# Healthcare ML Pipeline

Production-ready healthcare prediction API deployed on Render with Supabase PostgreSQL.

## Architecture

- **FastAPI**: High-performance async web framework
- **Supabase**: PostgreSQL database with real-time capabilities
- **Render**: Cloud platform for web services and cron jobs
- **XGBoost + Random Forest**: ML models with automatic selection
- **APScheduler**: Weekly model retraining (Saturdays at 12:00 PM)

## Setup

### 1. Supabase Setup

1. Create project at [supabase.com](https://supabase.com)
2. Run SQL migrations in `migrations/001_initial_schema.sql`
3. Copy Project URL and Service Role Key

### 2. Local Development

```bash
# Install UV
pip install uv

# Install dependencies
uv pip install -e .

# Set environment variables
cp .env.example .env
# Edit .env with your Supabase credentials

# Train initial model
python train_initial_model.py

# Run server
uvicorn app.main:app --reload