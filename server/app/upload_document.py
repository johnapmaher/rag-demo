import boto3
import json
import os
import uuid
from botocore.exceptions import NoCredentialsError, ClientError
from aws_lambda_powertools import Logger
from dotenv import load_dotenv
from datetime import datetime, timedelta
from requests_toolbelt.multipart import decoder

load_dotenv()

logger = Logger(level="DEBUG")

s3_client = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

s3_bucket_name = os.environ.get("S3_BUCKET_NAME")
if not s3_bucket_name:
    logger.error("S3_BUCKET_NAME environment variable is not set")
    raise ValueError("S3_BUCKET_NAME environment variable is not set")
else:
    logger.info(f"S3_BUCKET_NAME is set to: {s3_bucket_name}")

@logger.inject_lambda_context
def handler(event, context):
    try:
        logger.info("Received upload request")
        # logger.debug(f"Event: {event}")

        # Extract file information from the event
        headers = {k.lower(): v for k, v in event['headers'].items()}
        logger.debug(f"Headers: {headers}")
        file_name = headers.get('file-name')
        file_content = decoder.MultipartDecoder.from_response(event['body'])
        session_id = headers.get('session-id')

        # Upload the file to S3
        logger.info(f"Uploading file {file_name} to S3 bucket {s3_bucket_name}")
        s3_client.put_object(Bucket=s3_bucket_name, Key=file_name, Body=file_content)

        logger.info(f"File {file_name} uploaded successfully to S3 bucket {s3_bucket_name}")
        
        # Store session data in DynamoDB
        table = dynamodb.Table(os.environ['DYNAMODB_TABLE_NAME'])
        logger.info(f"DynamoDB table: {table.name}")

        if session_id:
            # Update existing session record
            logger.info(f"Updating session {session_id} with new file reference")
            table.update_item(
                Key={'sessionId': session_id},
                UpdateExpression="SET files = list_append(if_not_exists(files, :empty_list), :new_file)",
                ExpressionAttributeValues={
                    ':new_file': [file_name],
                    ':empty_list': []
                }
            )
        else:
            # Generate a new session ID
            session_id = str(uuid.uuid4())
            expiration_time = int((datetime.utcnow() + timedelta(hours=1)).timestamp())
            logger.info(f"Creating new session {session_id}")

            table.put_item(
                Item={
                    'sessionId': session_id,
                    'files': [file_name],
                    'uploadedAt': datetime.utcnow().isoformat(),
                    'expiresAt': expiration_time
                }
            )

        response_body = {
            "message": f"File {file_name} uploaded successfully.",
            "sessionId": session_id
        }

        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, file-name"
            },
            "body": json.dumps(response_body)
        }

    except NoCredentialsError:
        logger.error("Credentials not available")
        return {
            "statusCode": 500,
            "body": "Credentials not available"
        }

    except ClientError as e:
        logger.error(f"Client error: {e}")
        return {
            "statusCode": 500,
            "body": f"Client error: {e}"
        }

    except Exception as e:
        logger.error(f"Error processing file upload: {e}")
        return {
            "statusCode": 500,
            "body": f"Error processing file upload: {e}"
        }