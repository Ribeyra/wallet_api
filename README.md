# Wallet API (Test Assignment)

FastAPI service for wallet operations with PostgreSQL.  

## Features  
- ✅ Balance management (`DEPOSIT`/`WITHDRAW`)  
- ✅ Concurrent transaction safety  
- ✅ Dockerized (App + PostgreSQL)    

API Documentation: http://localhost:8000/docs

## Quick Start  
```bash
docker compose up -d --build
```

## Testing
```bash 
docker compose exec web pytest /app/tests -v
```

## Configuration
Copy `.env.example` to `.env` and adjust:
