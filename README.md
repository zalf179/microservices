
---

#  Microservices Order Processor

event-driven system built with **Node.js** and **Python**, orchestrated by **Kubernetes (Minikube)**.

##  Architecture
* **Order Service (Node.js):** REST API for order creation. Saves raw data to **MongoDB**.
* **Message Broker (RabbitMQ):** Handles asynchronous communication between services.
* **Payment Worker (Python):** Processes payments, saves financial records to **PostgreSQL**, and updates order status in MongoDB.

##  Tech Stack
* **Languages:** Node.js, Python 3.9
* **Databases:** MongoDB (NoSQL), PostgreSQL (SQL)
* **Messaging:** RabbitMQ
* **Infrastructure:** Docker, Kubernetes (K8s)

## Quick Start

1.  **Set Environment:**
    ```bash
    eval $(minikube docker-env)
    ```

2.  **Build Images:**
    ```bash
    docker build -t order-service:latest ./order-service
    docker build -t payment-worker:latest ./payment-worker
    ```

3.  **Deploy:**
    ```bash
    kubectl apply -f k8s/infrastructure.yaml
    kubectl apply -f k8s/order-service.yaml
    kubectl apply -f k8s/payment-worker.yaml
    ```

4.  **Access Web UI:**
    ```bash
    minikube service order-service
    ```

## Key Features
* **Asynchronous Processing:** Decoupled services via RabbitMQ for high availability.
* **Self-Healing:** Managed by K8s Deployment controllers.
* **Data Synchronization:** Cross-database updates (SQL & NoSQL) triggered by background workers.

---

