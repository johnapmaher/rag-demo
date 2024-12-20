import os
import boto3
import json
import base64
import uuid
from datetime import datetime, timezone
from aws_lambda_powertools import Logger
from requests_toolbelt.multipart import decoder

logger = Logger()
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
        logger.debug(f"Event: {event}")

        # Extract headers and body from the event
        headers = {k.lower(): v for k, v in event['headers'].items()}
        content_type = headers.get('content-type')
        logger.debug(f"Content-Type: {content_type}")

        body = event.get('body', '')
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(body)
        else:
            body = body.encode('utf-8')

        # Use MultipartDecoder to parse the multipart/form-data
        multipart_data = decoder.MultipartDecoder(body, content_type)

        # Initialize file variables
        file_name = None
        file_content = None

        # Extract the file from multipart data
        for part in multipart_data.parts:
            content_disposition = part.headers.get(b'Content-Disposition', b'').decode()
            if 'filename=' in content_disposition:
                # Extract the file name
                filename_index = content_disposition.find('filename=')
                file_name = content_disposition[filename_index + 9:].strip('"; ')
                file_content = part.content
                break

        if not file_name or not file_content:
            logger.error("No file found in the uploaded data")
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'No file uploaded'})
            }

        # Upload the file to S3
        logger.info(f"Uploading file {file_name} to S3 bucket {s3_bucket_name}")
        s3_client.put_object(Bucket=s3_bucket_name, Key=file_name, Body=file_content)
        logger.info(f"File {file_name} uploaded successfully to S3 bucket {s3_bucket_name}")

        # Store session data in DynamoDB
        table = dynamodb.Table(os.environ['DYNAMODB_TABLE_NAME'])
        logger.info(f"DynamoDB table: {table.name}")

        session_id = headers.get('session-id')
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
            # Create a new session record
            session_id = str(uuid.uuid4())
            logger.info(f"Creating new session with ID {session_id}")
            table.put_item(
                Item={
                    'sessionId': session_id,
                    'files': [file_name],
                    'uploadedAt': datetime.utcnow().isoformat(),
                    'expiresAt': int(datetime.now(tz=timezone.utc).timestamp() + 3600)  # Expires in 1 hour
                }
            )

        return {
            'statusCode': 200,
            'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type, file-name, session-id',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
        },
            'body': json.dumps({'message': 'File uploaded successfully', 'sessionId': session_id})
        }

    except Exception as e:
        logger.exception("Error processing the upload")
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Error uploading file', 'error': str(e)})
        }