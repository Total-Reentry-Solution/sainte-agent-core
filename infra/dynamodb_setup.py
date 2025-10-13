import boto3 

TABLE_NAME= 'SainiCheckins'
dynamodb = boto3.resource('dynamodb')


def create_table():
    exisiting_tables = dynamodb.meta.client.list_tables()["TableNames"]
    if TABLE_NAME in exisiting_tables:
        print("*****")
        print(f"Table '{TABLE_NAME} already exits ")
        print("*****")
        return

    table = dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema= [
            {
                "AttributeName":"user_id" , "KeyType":"HASH"
            },
            {
                "AttributeName":"timestamp" , "KeyType":"RANGE"
            },
        ],
        AttributeDefinations=[
            {
                "AttributeName":"user_id" , "AttributeType":"S"
            },
            {
                "AttributeName":"timestamp" , "AttributeType":"S"
            }
        ],
        ProvisionedThroughput= {
            "ReadCapacityUnites": 5,
            "WriteCapacityUnits":5  
        }
    )
    table.wait_until_exists()
    print(f"Created Table: {TABLE_NAME}")



if __name__ == "__main__":
    create_table()