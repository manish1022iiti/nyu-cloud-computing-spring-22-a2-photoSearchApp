import json
2	import boto3
3	from opensearchpy import OpenSearch, RequestsHttpConnection
4	from requests_aws4auth import AWS4Auth
5	
6	        
7	def detect_labels_from_rekognition(bucket_name, key):
8	    client=boto3.client('rekognition')
9	    response = client.detect_labels(Image={'S3Object':{'Bucket':bucket_name,'Name':key}}, MaxLabels=10)
10	    print(f"rekognition response: {response}")
11	    labels = [label_data["Name"] for label_data in response["Labels"]]
12	    return labels        
13	
14	def detect_labels_from_s3_metadata(bucket_name, key):
15	    response = boto3.client("s3").head_object(Bucket=bucket_name, Key=key)
16	    print(f"s3 head object response: {response}")
17	    labels_hobj = response["ResponseMetadata"]["HTTPHeaders"].get("x-amz-meta-customLabels", list())
18	    return labels_hobj
19	    
20	def put_photo_metadata_in_opensearch(row):
21	    host = "search-photos-ewzhu7znetxr4icz2fancqezci.us-east-1.es.amazonaws.com"
22	    region = "us-east-1"
23	    
24	    service = 'es'
25	    credentials = boto3.Session().get_credentials()
26	    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
27	    index_name = "index-img"
28	    
29	    search = OpenSearch(
30	        hosts = [{'host': host, 'port': 443}],
31	        http_auth = awsauth,
32	        use_ssl = True,
33	        verify_certs = True,
34	        connection_class = RequestsHttpConnection
35	    )
36	    response = search.index(
37	                    index = index_name,
38	                    body = row,
39	                    id = row["objectKey"],
40	                    refresh = True
41	                )
42	    print(f"response from opensearch.index: {response}")    
43	
44	def lambda_handler(event, context):
45	    # TODO implement
46	    print(event)
47	    
48	    record=event['Records'][0]
49	    bucket_name = record["s3"]["bucket"]["name"]
50	    key = record["s3"]["object"]["key"]  # image name
51	    evt_time = record["eventTime"]
52	    
53	    # calling rekognition to detect labels
54	    labels = detect_labels_from_rekognition(bucket_name, key)
55	    print(f"labels for {key} (from rekognition): {labels}")
56	    
57	    # calling s3 to get image metadata
58	    labels_hobj = detect_labels_from_s3_metadata(bucket_name, key)
59	    print(f"labels for {key} (from s3 head object metadata): {labels_hobj}")
60	    
61	    labels+=labels_hobj
62	    print(f"labels for {key} (final): {labels}")
63	    
64	    # preparing object to be stored in opensearch
65	    data = {
66	            "objectKey": key,
67	            "bucket": bucket_name,
68	            "createdTimestamp": evt_time,
69	            "labels": labels
70	        }
71	    # storing above object in OpenSearch
72	    put_photo_metadata_in_opensearch(row=data)    
73	
74	    # return {
75	    #     'statusCode': 200,
76	    #     'body': json.dumps('Hello from Lambda!')
77	        
78	    # }
79	
