import json
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth


def detect_labels_from_rekognition(bucket_name, key):
    client = boto3.client('rekognition')
    response = client.detect_labels(Image={'S3Object': {'Bucket': bucket_name, 'Name': key}}, MaxLabels=10)
    print(f"rekognition response: {response}")
    labels = [label_data["Name"] for label_data in response["Labels"]]
    return labels


def detect_labels_from_s3_metadata(bucket_name, key):
    response = boto3.client("s3").head_object(Bucket=bucket_name, Key=key)
    print(f"s3 head object response: {response}")
    labels_hobj = response["ResponseMetadata"]["HTTPHeaders"].get("x-amz-meta-customlabels", "")
    if labels_hobj:
        print(f"actual labels from s3: {labels_hobj}")
        labels_hobj = labels_hobj.split(",")
    else:
        labels_hobj = list()
    return labels_hobj


def put_photo_metadata_in_opensearch(row):
    host = "search-photos-ewzhu7znetxr4icz2fancqezci.us-east-1.es.amazonaws.com"
    region = "us-east-1"

    service = 'es'
    credentials = boto3.Session().get_credentials()
    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
    index_name = "index-img"

    search = OpenSearch(
        hosts=[{'host': host, 'port': 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )
    response = search.index(
        index=index_name,
        body=row,
        id=row["objectKey"],
        refresh=True
    )
    print(f"response from opensearch.index: {response}")


def lambda_handler(event, context):
    # TODO implement
    print(event)

    record = event['Records'][0]
    bucket_name = record["s3"]["bucket"]["name"]
    key = record["s3"]["object"]["key"]  # image name
    evt_time = record["eventTime"]

    # calling rekognition to detect labels
    labels = detect_labels_from_rekognition(bucket_name, key)
    print(f"labels for {key} (from rekognition): {labels}")

    # calling s3 to get image metadata
    labels_hobj = detect_labels_from_s3_metadata(bucket_name, key)
    print(f"labels for {key} (from s3 head object metadata): {labels_hobj}")

    labels += labels_hobj
    print(f"labels for {key} (final): {labels}")

    # preparing object to be stored in opensearch
    data = {
        "objectKey": key,
        "bucket": bucket_name,
        "createdTimestamp": evt_time,
        "labels": labels
    }
    # storing above object in OpenSearch
    put_photo_metadata_in_opensearch(row=data)

    # return {
    #     'statusCode': 200,
    #     'body': json.dumps('Hello from Lambda!')

    # }
