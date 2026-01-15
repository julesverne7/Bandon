# Docker Deployment Guide

## Local Development with Docker Compose

### Prerequisites
- Docker Desktop installed
- Docker Compose installed

### Quick Start

1. **Build and start all services:**
   ```bash
   docker-compose up --build
   ```

2. **Run migrations:**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

3. **Create superuser:**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

4. **Access the application:**
   - Web: http://localhost:8000

### Individual Services

- **Start services in background:**
  ```bash
  docker-compose up -d
  ```

- **View logs:**
  ```bash
  docker-compose logs -f web
  docker-compose logs -f celery
  ```

- **Stop services:**
  ```bash
  docker-compose down
  ```

- **Stop and remove volumes:**
  ```bash
  docker-compose down -v
  ```

## Azure Deployment

### Option 1: Azure App Service with Azure Database for PostgreSQL

1. **Create Azure Resources:**
   ```bash
   # Create resource group
   az group create --name gym-web-rg --location eastus
   
   # Create PostgreSQL server
   az postgres flexible-server create \
     --name gym-web-postgres \
     --resource-group gym-web-rg \
     --location eastus \
     --admin-user adminuser \
     --admin-password YourPassword123! \
     --version 15 \
     --sku-name Standard_B1ms
   
   # Create database
   az postgres flexible-server db create \
     --resource-group gym-web-rg \
     --server-name gym-web-postgres \
     --database-name gymwebdb
   
   # Create Azure Cache for Redis
   az redis create \
     --name gym-web-redis \
     --resource-group gym-web-rg \
     --location eastus \
     --sku Basic \
     --vm-size c0
   ```

2. **Build and push Docker image:**
   ```bash
   # Login to Azure Container Registry (or use Docker Hub)
   az acr create --name gymwebacr --resource-group gym-web-rg --sku Basic
   az acr login --name gymwebacr
   
   # Build and push
   docker build -t gymwebacr.azurecr.io/gym-web:latest .
   docker push gymwebacr.azurecr.io/gym-web:latest
   ```

3. **Create App Service:**
   ```bash
   # Create App Service Plan
   az appservice plan create \
     --name gym-web-plan \
     --resource-group gym-web-rg \
     --is-linux \
     --sku B1
   
   # Create Web App
   az webapp create \
     --resource-group gym-web-rg \
     --plan gym-web-plan \
     --name gym-web-app \
     --deployment-container-image-name gymwebacr.azurecr.io/gym-web:latest
   ```
   

4. **Configure Environment Variables:**
   ```bash
   az webapp config appsettings set \
     --resource-group gym-web-rg \
     --name gym-web-app \
     --settings \
       DEBUG=False \
       SECRET_KEY="your-secret-key" \
       DATABASE_URL="postgresql://adminuser:YourPassword123!@gym-web-postgres.postgres.database.azure.com:5432/gymweb" \
       REDIS_URL="redis://gym-web-redis.redis.cache.windows.net:6380?ssl=True" \
       ALLOWED_HOSTS="gym-web-app.azurewebsites.net"
   ```

5. **Run migrations:**
   ```bash
   az webapp ssh --resource-group gym-web-rg --name gym-web-app
   python manage.py migrate
   python manage.py createsuperuser
   ```

### Option 2: Azure Container Instances

```bash
# Create container instance
az container create \
  --resource-group gym-web-rg \
  --name gym-web-container \
  --image gymwebacr.azurecr.io/gym-web:latest \
  --dns-name-label gym-web-unique \
  --ports 8000 \
  --environment-variables \
    DEBUG=False \
    SECRET_KEY="your-secret-key" \
    DATABASE_URL="postgresql://..." \
    REDIS_URL="redis://..." \
  --cpu 1 \
  --memory 1.5
```

### Option 3: Azure Kubernetes Service (AKS)

For production deployments with auto-scaling and high availability, consider using AKS with Kubernetes manifests.

## Production Checklist

- [ ] Set `DEBUG=False` in environment variables
- [ ] Generate and use a strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Use Azure Database for PostgreSQL
- [ ] Use Azure Cache for Redis
- [ ] Configure Azure Blob Storage for media files
- [ ] Set up SSL/HTTPS
- [ ] Configure logging and monitoring
- [ ] Set up backup strategy for database
- [ ] Configure CORS if needed
- [ ] Review and update security settings
- [ ] Set up CI/CD pipeline

## Troubleshooting

### Check container logs:
```bash
docker-compose logs web
```

### Access container shell:
```bash
docker-compose exec web bash
```

### Rebuild without cache:
```bash
docker-compose build --no-cache
```

### Check database connection:
```bash
docker-compose exec web python manage.py dbshell
```


# Local testing
docker-compose up --build
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# Azure deployment
az acr create --name yourregistry --resource-group your-rg --sku Basic
docker build -t yourregistry.azurecr.io/gym-web:latest .
docker push yourregistry.azurecr.io/gym-web:latest