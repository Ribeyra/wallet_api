# Wallet API (Test Assignment)

FastAPI service for wallet operations with PostgreSQL.  

## Features  
- ✅ Balance management (`DEPOSIT`/`WITHDRAW`)  
- ✅ Concurrent transaction safety  
- ✅ Dockerized (App + PostgreSQL)    

## Quick Start  
```bash
docker compose up -d --build
```

## Testing
```bash 
docker compose exec web pytest /app/tests -v
```
