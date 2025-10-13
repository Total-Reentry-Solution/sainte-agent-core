# sainte-agent-core

AWS Bedrock + Lambda + DynamoDB emotional intelligence engine powering Siani conversational loop.

## Local setup
```bash
pip install -r requirements.txt
python infra/dynamodb_setup.py
```
## Deploy outline
Zip lambda/ folder → upload to AWS Lambda (handler: check_in_handler.lambda_handler)
Create API Gateway with POST /checkin route
Add environment variable: TABLE_NAME=SainiCheckins
Grant Lambda AmazonDynamoDBFullAccess + BedrockFullAccess

### ✅ What to Do Next
1. Copy all code above into your repo exactly (replace placeholders).  
2. Run locally just to ensure imports are fine:  
   ```bash
   python lambda/check_in_handler.py
   ```
   