import base64
2	import json
3	import boto3
4	from opensearchpy import OpenSearch, RequestsHttpConnection
5	from requests_aws4auth import AWS4Auth
6	
7	
8	def get_keywords(search_qry):
9	    # Lex calls will go here
10	    client = boto3.client('lex-runtime')
11	    data = search_qry
12	    
13	    response = client.post_text(botName="GetQueryKeywords", botAlias="Prod", userId="userId", inputText= data)
14	    print(f"Chatbot response: {response}")
15	    
16	    keywords = list()
17	    k1 = str(response["slots"]["keyword_a"])
18	    k2 = str(response["slots"]["keyword_b"])
19	    print(f"keyword1 extracted from chatbot response: {k1}")
20	    print(f"keyword2 extracted from chatbot response: {k2}")
21	    
22	    if k1 not in ["", "None"]:
23	        keywords.append(k1)
24	        
25	    if k2 not in ["", "None"]:
26	        keywords.append(k2)
27	    
28	    print(f"keywords: {keywords}")
29	    return keywords
30	    
31	    
32	def search_photos(keywords):
33	    host = "search-photos-ewzhu7znetxr4icz2fancqezci.us-east-1.es.amazonaws.com"
34	    region = "us-east-1"
35	    
36	    service = 'es'
37	    credentials = boto3.Session().get_credentials()
38	    awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)
39	    index_name = "index-img"
40	    
41	    search = OpenSearch(
42	        hosts = [{'host': host, 'port': 443}],
43	        http_auth = awsauth,
44	        use_ssl = True,
45	        verify_certs = True,
46	        connection_class = RequestsHttpConnection
47	    )
48	    
49	    results = dict()
50	    for keyword in keywords:
51	        query = {
52	                  'query': {
53	                    'match': {
54	                      "labels": keyword
55	                    }
56	                  }
57	                }
58	    
59	        response = search.search(
60	            body = query,
61	            index = index_name
62	        )
63	        print(f"Opensearch search response: {response}")
64	        
65	        for hit in response["hits"]["hits"]:
66	            results[hit["_id"]] = hit["_source"]
67	    
68	    print(f"OpenSearch final search results for {keywords}: {results}")
69	    return results
70	    
71	    
72	def get_images(img_data):
73	    s3 = boto3.client("s3")
74	    
75	    img_paths = list()
76	    imgs = list()
77	    for data in img_data.values():
78	        path = f"http://{data['bucket']}.s3.amazonaws.com/{data['objectKey']}"
79	        response = s3.get_object(Bucket=data["bucket"], Key=data["objectKey"])
80	        image = response['Body'].read()
81	        imgs.append(base64.b64encode(image).decode('utf-8'))
82	        img_paths.append(path)
83	    print(f"images data: {imgs}")
84	    print(f"images paths: {img_paths}")
85	    
86	    if imgs:
87	        # return {
88	        #         'headers': {
89	        #             'Content-Type': 'image/png',
90	        #             'Access-Control-Allow-Origin': 'http://assignment2-b1.s3-website-us-east-1.amazonaws.com',
91	        #             'Access-Control-Allow-Methods': 'GET'
92	        #         },
93	        #         # 'headers': { "Content-Type": "image/png" },
94	        #         'statusCode': 200,
95	        #         'body': imgs[0],
96	        #         'isBase64Encoded': True
97	        #       }
98	        return {
99	                'headers': {
100	                    'Access-Control-Allow-Headers': 'Content-Type',
101	                    'Access-Control-Allow-Origin': 'http://assignment2-b1.s3-website-us-east-1.amazonaws.com',
102	                    'Access-Control-Allow-Methods': 'GET'
103	                },
104	                # 'headers': { "Content-Type": "image/png" },
105	                'statusCode': 200,
106	                'body': json.dumps(img_paths),
107	                # 'isBase64Encoded': True
108	              }
109	    else:
110	        return {
111	            'headers': { "Content-type": "text/html" },
112	            'statusCode': 200,
113	            'body': "<h1>SOrry, NO images found for this!</h1>",
114	        }
115	
116	
117	def lambda_handler(event, context):
118	    # TODO implement
119	    print(f"event: {event}")
120	    
121	    # srchq = ". ".join([msg_struct["unstructured"]["text"] for msg_struct in event["messages"]])
122	    srchq = event["queryStringParameters"]["q"]
123	    print(f"user search query: {srchq}")
124	    
125	    keywords = get_keywords(srchq)
126	    search_results = search_photos(keywords)
127	    
128	    ret_imgs = get_images(search_results)
129	    
130	    return ret_imgs
131	    
132	    # return {
133	    #     'statusCode': 200,
134	    #     'body': json.dumps('Hello from Lambda!')
135	    # }
136	
