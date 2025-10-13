# SAINTE Agent Core

## 🧠 Overview
**SAINTE Agent Core** is the backend emotional intelligence engine powering Siani’s Conversational Loop.  
It combines AWS Bedrock, Lambda, and DynamoDB to process user emotional states and respond with trauma-informed support.

---

## 🚀 Live Stack Overview

**Deployed Region:** `us-east-2`  
**Deployment Date:** 2025-10-13 09:08:19 UTC

### ✅ AWS Components
| Component | Purpose |
|------------|----------|
| **Amazon API Gateway** | Provides REST endpoints for communication between frontend and backend |
| **AWS Lambda (check_in_handler)** | Handles user check-ins, classifies emotional tier, stores data, generates response |
| **AWS Lambda (get_checkins)** | Retrieves all stored check-ins from DynamoDB |
| **Amazon DynamoDB (SainiCheckins)** | Stores emotional state logs with timestamps |
| **Amazon Bedrock** | Generates context-aware, trauma-informed responses |
| **CloudWatch** | Logs, metrics, and monitoring for all Lambda executions |

---

## 🧩 Architecture Diagram

```
Frontend (React / Flutter / Streamlit)
        ↓
  API Gateway
        ↓
 ┌────────────────────┐
 │ AWS Lambda         │
 │  - check_in_handler│  → DynamoDB (SainiCheckins)
 │  - get_checkins    │
 └────────────────────┘
        ↓
 Amazon Bedrock (Claude 3 / Titan)
        ↓
 CloudWatch Logs & Metrics
```

---

## 🔗 Live API Endpoints

| Method | Endpoint | Description |
|--------|-----------|-------------|
| **POST** | `https://b6wdy7b2w0.execute-api.us-east-2.amazonaws.com/prod/checkin` | Create a new emotional check-in |
| **GET** | `https://b6wdy7b2w0.execute-api.us-east-2.amazonaws.com/prod/checkins` | Retrieve all check-ins |

---

## 🧠 Example Usage

### POST (Log a Check-in)
```bash
curl -X POST https://b6wdy7b2w0.execute-api.us-east-2.amazonaws.com/prod/checkin -H "Content-Type: application/json" -d '{"user_id": "user123", "message": "Feeling hopeful today!"}'
```

**Response:**
```json
{
  "statusCode": 200,
  "body": "{\"tier\": \"Stable\", \"response\": \"You're doing steady work—want to stay in this rhythm or stretch a bit today?\"}"
}
```

---

### GET (Retrieve All Check-ins)
```bash
curl https://b6wdy7b2w0.execute-api.us-east-2.amazonaws.com/prod/checkins
```

**Response:**
```json
[
  {
    "user_id": "user123",
    "message": "Feeling hopeful today!",
    "tier": "Stable",
    "response": "You're doing steady work—want to stay in this rhythm or stretch a bit today?",
    "timestamp": "2025-10-13T08:22:56.071392"
  }
]
```

---

## 🧰 Local Development Setup

```bash
# Clone the repo
git clone https://github.com/Total-Reentry-Solution/sainte-agent-core.git
cd sainte-agent-core

# Install dependencies
pip install -r requirements.txt

# Setup DynamoDB locally (optional)
python infra/dynamodb_setup.py

# Test locally
python lambda/check_in_handler.py
```

---

## 🛠 Future Enhancements

| Feature | Description |
|----------|--------------|
| 🔐 Authentication | Add API Key or Cognito for secure access |
| 🧠 EventBridge Automation | Scheduled daily summaries / reflection nudges |
| 📊 Dashboard | React or Streamlit dashboard pulling `/checkins` data |
| 🪄 Step Functions | Workflow chaining for multi-stage emotional intelligence |

---

## 👩‍💻 Maintainers
**SAINTE Core AI Team**  
AWS Bedrock Hackathon 2025 — Emotional Intelligence Engine  

