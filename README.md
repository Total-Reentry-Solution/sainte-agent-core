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

# Phase 4

## 🧱 Step-by-Step Progress Summary

### ✅ Step 1 — **Set up AWS Lambda & DynamoDB**
- Created two tables:
  - `SainiCheckins` for check-ins (user_id, message, tier, response, timestamp).
  - `SainiVectors` for semantic memory (embedding + recall).
- Added required IAM permissions (`AmazonDynamoDBFullAccess`, `CloudWatchLogsFullAccess`).

---

### ✅ Step 2 — **Lambda: `check_in_handler.py`**
- Handles `/checkin` POST endpoint.
- Calls:
  - `classify_state.py` → classifies emotional state (Stable, Stirred, At-Risk, Critical).
  - `respond_nudge.py` → generates trauma-informed response.
- Saves check-in entry to DynamoDB.

**Example Output:**
```json
{
  "tier": "At-Risk",
  "response": "I noticed some strain—would it help to look at next steps or just pause?"
}
```

---

### ✅ Step 3 — **Lambda: `respond_nudge.py`**
- Uses **Bedrock Claude 3 Sonnet** for emotional reflection.  
- Includes deterministic fallback responses when Bedrock unavailable.
- Integrated `retrieve_recent_context()` for short-term context retrieval from `SainiVectors`.

---

### ✅ Step 4 — **Lambda: `update_memory.py`**
- Creates vector embeddings for check-in data.
- Uses **Amazon Titan Embed Text v2.0** via Bedrock.
- Stores combined context in `SainiVectors`.

**DynamoDB Entry Example:**
```json
{
  "user_id": "user123",
  "tier": "At-Risk",
  "message": "Feeling tired but okay",
  "response": "I noticed some strain—would it help to look at next steps or just pause?",
  "embedding": [0.021, -0.008, 0.015, ...],
  "timestamp": "2025-10-13T08:46:06Z"
}
```

---

### ⚙️ Step 5 — **Pending (Context Recall Integration)**
Once model access is enabled by the org admin (Sainte AWS account), next step will be to:
- Retrieve top 3 recent embeddings from `SainiVectors`.
- Send those to Bedrock Claude 3 Sonnet.
- Generate a **context-aware nudge** reflecting prior user states.

---

### 🪄 Step 6 — **End-to-End Flow**
After full enablement, user flow will be:

1. `/checkin` → `check_in_handler.py`
2. → Save message to DynamoDB (`SainiCheckins`)
3. → Trigger `update_memory` Lambda (semantic memory)
4. → `respond_nudge.py` recalls context and generates nuanced support response.

---

## 🔐 Environment Variables
Each Lambda requires the following:
```ini
TABLE_NAME = SainiCheckins
VECTOR_TABLE = SainiVectors
AWS_REGION = us-east-1
MEMORY_FUNCTION = update_memory
```

---

## 🧰 Required AWS Permissions
Each Lambda role must include:
- `AmazonDynamoDBFullAccess`
- `AmazonBedrockFullAccess`
- `CloudWatchLogsFullAccess`
- (Optional) `AWSLambdaBasicExecutionRole`

---

## 🌎 Current Status
| Function | Status | Notes |
|-----------|---------|-------|
| `check_in_handler` | ✅ Active | Working correctly with DynamoDB writes |
| `respond_nudge` | ✅ Functional | Using local fallback text; Bedrock call pending full access |
| `update_memory` | ⚠️ Testing | AccessDeniedException until Bedrock model access enabled (awaiting org setup) |

---

## 🧩 Next Steps
- [ ] Org Admin enables Bedrock model access:
  - `Amazon Titan Embed Text v2:0`
  - `Anthropic Claude 3 Sonnet 20240229 v1:0`
- [ ] Re-test `/checkin` → verify DynamoDB vector write.
- [ ] Implement Step 5: Context Recall in `respond_nudge.py`.
- [ ] Add Streamlit-based dashboard to visualize emotional progress.

---

## 🧭 Maintainer Notes
- **Account:** Sainte AWS (ID: `193884053925`)
- **Region:** us-east-1
- **Lambda Functions:**
  - `check_in_handler`
  - `respond_nudge`
  - `update_memory`
- **Frameworks:** AWS Lambda, Bedrock, DynamoDB, boto3 (Python)

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

