import boto3
import json
import base64
from PIL import Image
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import os
from datetime import datetime
import concurrent.futures

from botocore.config import Config

config = Config(
   retries = {
      'max_attempts': 10,
      'mode': 'adaptive'
   }
)
# Create a Boto3 STS client
sts_client = boto3.client('sts')

#Starts the Session with the assumed role
session = boto3.Session()


#Set variables for the locations of each data_set
model_1_folder = '/home/appuser/app/model_1'
model_2_folder = '/home/appuser/app/model_2' 
model_3_folder = '/home/appuser/app/model_3' 


#Get SSM Parameter values for OpenSearch Domain and
ssm = session.client('ssm')
parameters = ['/car-repair/collection-domain-name', '/car-repair/s3-bucket'] 
response = ssm.get_parameters(
    Names=parameters,
    WithDecryption=True
)
#Set OpenSearch Details
parameter1_value = response['Parameters'][0]['Value']
coll_domain_name = parameter1_value[8:]
os_host = coll_domain_name #collection host name from the cloudformation template. DO NOT ADD https://
os_index_name = 'repair-cost-data' #os index name that will be created

#Set S3 Details where images will be stored
parameter2_value = response['Parameters'][1]['Value']
s3_bucket = parameter2_value #bucket name from the cloudformation template
s3_folder = 'repair-data/'

#Initialize OpenSearch Client
credentials = session.get_credentials()
client = session.client('opensearchserverless')
service = 'aoss'
region = session.region_name
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key,
                   region, service, session_token=credentials.token)

#Set MultiModal Embeddings, bedrock client and S3 client
model_name = "amazon.titan-embed-image-v1"
bedrock = session.client("bedrock-runtime", config=config)
s3 = session.client('s3')

#Define the JSON Creation metadata instruction for each car Make/Model
instruction_model_1 = 'Instruction: You are a damage repair cost estimator and based on the image you need to create a json output as close as possible to the <model>, \
you need to estimate the repair cost to populate within the output and you need to provide the damage_severity according to the <criteria>, \
you also need to provide a damage_description which is short and less than 10 words. Just provide the json output in the response, do not explain the reasoning. \
For testing purposes assume the image is from a fictitious car brand "Make_1" and a ficticious model "Model_1" in the state of Florida.'

instruction_model_2 = 'Instruction: You are a damage repair cost estimator and based on the image you need to create a json output as close as possible to the <model>, \
you need to estimate the repair cost to populate within the output and you need to provide the damage_severity according to the <criteria>, \
you also need to provide a damage_description which is short and less than 10 words. Just provide the json output in the response, do not explain the reasoning. \
For testing purposes assume the image is from a fictitious car brand "Make_2" and a ficticious model "Model_2" in the state of Florida.'

instruction_model_3 = 'Instruction: You are a damage repair cost estimator and based on the image you need to create a json output as close as possible to the <model>, \
you need to estimate the repair cost to populate within the output and you need to provide the damage_severity according to the <criteria>, \
you also need to provide a damage_description which is short and less than 10 words. Just provide the json output in the response, do not explain the reasoning. \
For testing purposes assume the image is from a fictitious car brand "Make_3" and a ficticious model "Model_3" in the state of Florida.'

bedrock_client = session.client('bedrock-runtime', config=config)


#Define function that will Create the JSON Metadata for the given damage image
def create_json_metadata(encoded_image, instruction):
    print('Sending JSON Creation Request to Bedrock Claude')
    model = '<model>\
    { \
        "make": "XXXX",\
        "model": "XXXX", \
        "year": XXXX, \
        "state": "XX",\
        "damage": "Right Front",\
        "repair_cost": XXXXX,\
        "damage_severity": "moderate",\
        "damage_description": "Dent and scratches on the right fender",\
        "parts_for_repair": "add a list of parts that need to be replaced/repaired",\
        "labor_hours": XX,\
        "parts_cost": XXXX,\
        "labor_cost" \
      }\
    </model>'
    criteria_cost = '<criteria> \
    repair_cost < 500 = light \
    repair_cost > 500 AND < 1000 = moderate \
    repair_cost > 1000 AND < 2000 = severe \
    repair_cost > 2000 = major \
    </criteria>'
    prompt = criteria_cost + model + instruction 
    invoke_body = {
    'anthropic_version': 'bedrock-2023-05-31',
    'max_tokens': 2000,
    'temperature': 1,
    'top_p': 1,
    'top_k': 250,
    'messages': [
        {
        'role': 'user',
        'content': [
            {
            "type": "image",
            "source": {
              "type": "base64",
              "media_type": "image/png",
              "data": encoded_image
            }
          },
          {
            "type": "text",
            "text": prompt
          }
            ]
        }   
    ]
    }
    invoke_body = json.dumps(invoke_body).encode('utf-8')
    response = bedrock_client.invoke_model(
        body=invoke_body,
        contentType='application/json',
        accept='application/json',
        modelId='anthropic.claude-3-haiku-20240307-v1:0'
    )
    response_body = response['body'].read()
    data = json.loads(response_body)

    text = data['content'][0]['text']
    print('JSON output Created by Claude', text)
    return text 

#Function to get OpenSearch client
def get_OpenSearch_client(os_host, os_index_name):
    print("opening opensearch client")
    try:
        client = OpenSearch(
            hosts=[{'host': os_host, 'port': 443}],
            http_auth=awsauth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=300
        )

        print('Testing if an index already exists if not, create one.')

        exists = client.indices.exists(index=os_index_name)
        if not exists:
            # Create index
            response = client.indices.create(
                index=os_index_name,
                body={
                    "settings": {
                        "index": {
                        "knn": 'true',
                        "knn.algo_param.ef_search": 512
                        }
                    },
                    "mappings": {
                        "properties": {
                        "damage_vector": {
                            "type": "knn_vector",
                            "dimension": 1024,
                            "method": {
                            "name": "hnsw",
                            "space_type": "l2",
                            "engine": "nmslib",
                            "parameters": {
                                "ef_construction": 128,
                                "m": 24
                            }
                            }
                        }
                        }
                    }
                    }
            )
            print("Index created!")

        else:
            print("Index already exists, Proceeding with adding the Document")

    except Exception as e:
        print('Error opening Opensearch client: ', os_host)
        print(f"Error message: {e}")
        os.exit(1)

    return client


#Define Function that will add the vector document along with its metadata to OpenSearch
def indexData(client, image_vector, metadata, os_index_name, os_host):
    # Build the OpenSearch client

    print('Storing Document on OpenSearch')

    # Add a document to the index.
    response = client.index(
        index=os_index_name,
        body={
            'damage_vector': image_vector,
            'metadata': metadata
        }
    )
    print('\nDocument added:')
    print(response)

def ingest_image(client, filename, folder_path, os_index_name, os_host, instruction, counter):
        
    print(f"Current run: {counter}")
    response = "nothing done " + str(counter)

    try:
        base, ext = os.path.splitext(filename)
        if ext in ['.jpg', '.jpeg', '.png']:

            img_path = folder_path + '/' + filename
            print('-----------------------------')
            print('Document Ingestion Process Starting')
            print('Processing image file: ', img_path)
            print('-----------------------------')
            if os.path.exists(img_path):
                img = Image.open(img_path)
                with open(img_path, 'rb') as image_file:
                    file_name = os.path.basename(img_path)
                    image_bytes = image_file.read() 

                    image_base64_bytes = base64.b64encode(image_bytes)
                    encoded_image = image_base64_bytes.decode('utf-8')

                key = s3_folder + file_name
                print('Uploading file to S3: ', file_name)
                s3.upload_file(img_path, s3_bucket, key)
                # call that involved Bedrock
                json_text = create_json_metadata(encoded_image, instruction)

                json_string = json.dumps(json_text)
                data_2 = json.loads(json_string)
                json_bytes = data_2.encode('utf-8') 
                base64_bytes = base64.b64encode(json_bytes)
                encoded_json = base64_bytes.decode('utf-8')
                data = json.loads(json_text)
                body = json.dumps({
                        "inputText": encoded_json,
                        "inputImage": encoded_image,
                        "embeddingConfig": {
                            "outputEmbeddingLength": 1024
                        }
                    })
                print('Invoking model: ', model_name)
                response = bedrock.invoke_model(modelId=model_name, body=body)

                body = response['body']

                body_output = body.read()

                data['s3_location'] = key
                metadata = data

                body_string = body_output.decode('utf-8')
                data_embedded = json.loads(body_string)  
                image_vector = data_embedded['embedding']
                json_embedding = json.loads(body_string)
                
                indexData(client, image_vector, metadata, os_index_name, os_host)
                
                #create variable tha will concatenate the string OK with the current counter variable value
                response = "OK " + str(counter)

                print(response)
    except Exception as e:
        print(f"Counter {counter} Error message: {e}")
        response = "Error counter" + str(counter) + " - Error message: " + str(e)
    
    return response


#Controls the ingestion of all files in the provided folder. Execution is multi-threaded
def image_ingestion(folder_path, os_index_name, os_host, instruction):
    counter = 0
    client = get_OpenSearch_client(os_host, os_index_name)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = []

        for filename in os.listdir(folder_path):
            
            if counter == 0:
                total_loops = len(os.listdir(folder_path))
    
            print(f"This loop will run for a total of {total_loops} times")
    
            counter += 1

            futures.append(executor.submit(ingest_image, client, filename, folder_path, os_index_name, os_host, instruction, counter))

            # if counter == 4:
            #     break

    for future in concurrent.futures.as_completed(futures):
        result = future.result()
        print(result)
            


#store current date time
start_time = datetime.now()

#print the start date time
print("Start date and time: ")
print(start_time)
print('-----------------------------')

#Calls the function for ingestion of data
image_ingestion(model_1_folder, os_index_name, os_host, instruction_model_1)
image_ingestion(model_2_folder, os_index_name, os_host, instruction_model_2)
image_ingestion(model_3_folder, os_index_name, os_host, instruction_model_3)

#print the end date time
end_time = datetime.now()
print(f"Start time {start_time} - End date and time {end_time}") 
print('-----------------------------')
