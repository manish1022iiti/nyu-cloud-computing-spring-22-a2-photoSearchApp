import base64
import json
import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth


def get_keywords(search_qry):
    # Lex calls will go here
    client = boto3.client('lex-runtime')
    data = search_qry

    response = client.post_text(botName="GetQueryKeywords", botAlias="Prod", userId="userId", inputText=data)
    print(f"Chatbot response: {response}")

    keywords = list()
    k1 = str(response["slots"]["keyword_a"])
    k2 = str(response["slots"]["keyword_b"])
    print(f"keyword1 extracted from chatbot response: {k1}")
    print(f"keyword2 extracted from chatbot response: {k2}")

    if k1 not in ["", "None"]:
        keywords.append(k1)

    if k2 not in ["", "None"]:
        keywords.append(k2)

    print(f"keywords: {keywords}")
    return keywords


def search_photos(keywords):
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

    results = dict()
    for keyword in keywords:
        query = {
            'query': {
                'match': {
                    "labels": keyword
                }
            }
        }

        response = search.search(
            body=query,
            index=index_name
        )
        print(f"Opensearch search response: {response}")

        for hit in response["hits"]["hits"]:
            results[hit["_id"]] = hit["_source"]

    print(f"OpenSearch final search results for {keywords}: {results}")
    return results


def get_images(img_data):
    s3 = boto3.client("s3")

    img_paths = list()
    imgs = list()
    for data in img_data.values():
        path = f"http://{data['bucket']}.s3.amazonaws.com/{data['objectKey']}"
        try:
            response = s3.get_object(Bucket=data["bucket"], Key=data["objectKey"])
            image = response['Body'].read()
            # print(f"image_name: {data['objectKey']}, content: {image}")
            imgs.append(base64.b64encode(image).decode('utf-8'))
            img_paths.append(path)
        except Exception as e:
            print(f"Seems like filename: {data['objectKey']} does NOT exist in S3. Ignoring it! : {e}.")

    print(f"images data: {imgs}")
    print(f"images paths: {img_paths}")

    if imgs:
        # return {
        #         'headers': {
        #             'Content-Type': 'image/png',
        #             'Access-Control-Allow-Origin': 'http://assignment2-b1.s3-website-us-east-1.amazonaws.com',
        #             'Access-Control-Allow-Methods': 'GET'
        #         },
        #         # 'headers': { "Content-Type": "image/png" },
        #         'statusCode': 200,
        #         'body': imgs[0],
        #         'isBase64Encoded': True
        #       }
        return {
            'headers': {
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': 'http://assignment2-b1.s3-website-us-east-1.amazonaws.com',
                'Access-Control-Allow-Methods': 'GET'
            },
            # 'headers': { "Content-Type": "image/png" },
            'statusCode': 200,
            'body': json.dumps(img_paths),
            # 'isBase64Encoded': True
        }
    else:
        return {
            'headers': {
                "Content-type": "text/html",
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Origin': 'http://assignment2-b1.s3-website-us-east-1.amazonaws.com',
                'Access-Control-Allow-Methods': 'GET'
            },
            'statusCode': 200,
            'body': json.dumps([]),
        }


def lambda_handler(event, context):
    # TODO implement
    print(f"event: {event}")

    # srchq = ". ".join([msg_struct["unstructured"]["text"] for msg_struct in event["messages"]])
    srchq = event["queryStringParameters"]["q"]
    print(f"user search query: {srchq}")

    keywords = get_keywords(srchq)
    search_results = search_photos(keywords)

    ret_imgs = get_images(search_results)

    return ret_imgs

    # return {
    #     'statusCode': 200,
    #     'body': json.dumps('Hello from Lambda!')
    # }
