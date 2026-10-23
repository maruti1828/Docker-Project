# ShopPulse — Cloud-Native Order Management Platform

ShopPulse is a containerized order management application built to demonstrate practical DevOps engineering skills, including automated CI/CD, Docker image publishing, Kubernetes deployments, persistent database storage, application health checks, and secrets management.

The project uses FastAPI for the application API and PostgreSQL for persistent data storage. GitHub Actions automates testing and image publishing, while Kubernetes runs the application and database locally using Kind.

## Architecture

```text
Developer
    |
    v
GitHub Repository
    |
    v
GitHub Actions CI/CD
    |
    +--> Automated Tests
    |
    +--> Build and Publish Docker Image
    |        |
    |        v
    |      GitHub Container Registry
    |
    +--> Published Image Verification

Local Kubernetes (Kind)
    |
    +--> ShopPulse API
    |      |
    |      +--> 2 Replicas
    |      +--> Readiness and Liveness Probes
    |      +--> Kubernetes Service
    |
    +--> PostgreSQL
           |
           +--> Kubernetes Secret
           +--> PersistentVolumeClaim
           +--> Persistent Data Storage
```

## Technology Stack

| Technology | Purpose |
|---|---|
| Python and FastAPI | REST API development |
| PostgreSQL 16 | Relational database |
| Docker | Application containerization |
| Docker Compose | Local application development |
| Kubernetes | Application orchestration |
| Kind | Local Kubernetes cluster |
| GitHub Actions | Automated CI/CD pipeline |
| GitHub Container Registry | Docker image storage |
| Linux / WSL Ubuntu | Development environment |
| Git and GitHub | Version control and source management |

## Features

- **REST API:** Create, list, and retrieve customer orders.
- **Database integration:** Store order information in PostgreSQL.
- **Containerization:** Package the application into a Docker image.
- **Automated CI/CD:** Run tests and publish container images through GitHub Actions.
- **Image verification:** Verify that the published container image starts and passes its health check.
- **Kubernetes deployment:** Run the API with two replicas behind a Service.
- **Persistent storage:** Preserve PostgreSQL data using a PersistentVolumeClaim.
- **Health monitoring:** Configure Kubernetes readiness and liveness probes.
- **Secrets management:** Supply database credentials through a Kubernetes Secret.
- **Resource controls:** Configure CPU and memory requests and limits for application containers.

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check application and database health |
| GET | `/version` | Return application version |
| POST | `/orders` | Create an order |
| GET | `/orders` | List orders |
| GET | `/orders/{order_id}` | Retrieve a specific order |
| GET | `/docs` | Interactive API documentation |

### Example: Create an Order

```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Demo Customer",
    "item": "Keyboard",
    "quantity": 2,
    "unit_price": 1500
  }'
```

The API calculates the order total and stores the order in PostgreSQL.

### Example: Check Application Health

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "database": "connected"
}
```

## Run Locally with Docker Compose

### Prerequisites

- Docker Engine
- Docker Compose
- Git

Clone the repository:

```bash
git clone https://github.com/maruti1828/Docker-Project.git
cd Docker-Project
```

Start the application:

```bash
docker compose up -d
```

Check container status:

```bash
docker compose ps
```

Verify the application:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/version
```

Open the interactive API documentation:

`http://localhost:8000/docs`

Stop the application:

```bash
docker compose down
```

The PostgreSQL data volume is retained when using this command. Do not use `docker compose down -v` unless you intentionally want to delete the local database volume.

## Deploy to Kubernetes Using Kind

### Prerequisites

- Docker
- kubectl
- Kind
- Access to the ShopPulse container image

Create a local Kubernetes cluster if you do not already have one:

```bash
kind create cluster --name shoppulse
```

If you already have a working Kind cluster, use that cluster instead of creating another one.

Create the application namespace:

```bash
kubectl create namespace shoppulse
```

Create the database Secret:

```bash
kubectl create secret generic shoppulse-db-secret \
  --namespace shoppulse \
  --from-literal=POSTGRES_DB=shoppulse \
  --from-literal=POSTGRES_USER=shoppulse \
  --from-literal=POSTGRES_PASSWORD='REPLACE_WITH_A_STRONG_LOCAL_PASSWORD'
```

**Important:** Use a password that matches your local deployment configuration. Do not commit real credentials to Git.

Apply the PostgreSQL persistent storage claim:

```bash
kubectl apply -f k8s/postgres-pvc.yaml
```

Deploy PostgreSQL and its internal Service:

```bash
kubectl apply -f k8s/postgres.yaml
```

Wait for PostgreSQL to become ready:

```bash
kubectl rollout status deployment/shoppulse-postgres \
  -n shoppulse --timeout=180s
```

Deploy the API and its Service:

```bash
kubectl apply -f k8s/api.yaml
```

Wait for the API deployment:

```bash
kubectl rollout status deployment/shoppulse-api \
  -n shoppulse --timeout=180s
```

Inspect the deployment:

```bash
kubectl get pods,pvc,svc -n shoppulse
```

### Access the API

Forward the API Service to your local machine:

```bash
kubectl port-forward -n shoppulse svc/shoppulse-api 8000:8000
```

Keep this terminal open. In another terminal, run:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/version
curl http://localhost:8000/orders
```

The interactive documentation is available at:

`http://localhost:8000/docs`

## Verify Persistent Storage

The PostgreSQL database uses a PersistentVolumeClaim to store its data.

Check the claim:

```bash
kubectl get pvc -n shoppulse
```

Restart PostgreSQL:

```bash
kubectl rollout restart deployment/shoppulse-postgres \
  -n shoppulse
```

Wait for the restart:

```bash
kubectl rollout status deployment/shoppulse-postgres \
  -n shoppulse --timeout=180s
```

Verify the API health and confirm that previously created orders remain available.

This demonstrates persistence across a database Pod restart. It does not, by itself, demonstrate backup recovery or disaster recovery.

## CI/CD Workflow

The GitHub Actions workflow in `.github/workflows/ci.yml` automates the container delivery process.

1. Run automated application tests.
2. Build the ShopPulse Docker image.
3. Publish the image to GitHub Container Registry when the configured branch and conditions match.
4. Tag images for traceability, including the commit SHA.
5. Start the published image with a test database and verify its health.

The workflow uses GitHub-provided credentials for registry authentication. Repository and package permissions must be configured correctly for image publishing.

## Kubernetes Manifests

```text
k8s/
├── api.yaml
├── postgres.yaml
└── postgres-pvc.yaml
```

- `api.yaml` — API Deployment, environment configuration, health probes, resource settings, and Service.
- `postgres.yaml` — PostgreSQL Deployment and internal Service.
- `postgres-pvc.yaml` — persistent storage claim for PostgreSQL.

## Security and Cost Considerations

- Database credentials are supplied through a Kubernetes Secret rather than directly in the API Deployment's environment configuration.
- Kubernetes Secrets are not automatically equivalent to encrypted secret storage. Production environments should use encryption at rest, restrictive RBAC, and a dedicated secrets-management solution.
- The current local Kind environment is intended for learning and development, not as a production hosting environment.
- The application is not automatically publicly accessible on the internet just because its Kubernetes Service uses NodePort.
- No AWS infrastructure is required for the local deployment described here.

## Current Scope and Future Improvements

Potential next steps include:

- Deploying to a cloud-hosted Kubernetes environment.
- Managing infrastructure with Terraform.
- Adding structured application logging and centralized monitoring.
- Implementing automated rollback and deployment strategies.
- Adding database backups and tested recovery procedures.
- Introducing image scanning and Kubernetes security policies.
- Replacing local development credentials with production-grade secrets management.
- Adding integration and load tests.

These are future improvements, not features claimed as completed.

## Learning Outcomes

This project provides hands-on experience with:

- Containerizing a Python application.
- Connecting application services to PostgreSQL.
- Building an automated CI/CD pipeline.
- Publishing and verifying Docker images.
- Deploying replicated workloads on Kubernetes.
- Managing persistent storage and application configuration.
- Using health probes to monitor application readiness.
- Troubleshooting container and Kubernetes deployment issues.

## Repository

GitHub: https://github.com/maruti1828/Docker-Project

**Project focus:** Practical DevOps, container orchestration, CI/CD automation, database persistence, and cloud-native application delivery.
# Docker-Project
