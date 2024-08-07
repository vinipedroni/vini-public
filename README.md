# Simplifying Automotive Damage Processing with Amazon Bedrock and Vector Databases

Assessing the costs related to repairing damages on assets is a challenge that all industries have, in particular automotive companies have had this challenge for a long time. 

There are multiple market solution that leverage Machine Learning processes targeted on addressing this challenge. 

The proposal of this solution is to offer a new method levearging GenAI and MultiModal Vector Databases.

# Solution Details:

The solution involves two important parts, the ingestion and the inference. 

Data Ingestion Flow Steps:

1. The Ingestion Processor will start by getting data from our current data set and it is going to run through Amazon Bedrock Anthropic Claude 3 Haiku. In this step the output is a standardized metadata which contains detailed information about the current damage, this includes make, model, year, location, labor cost, parts associated with the damage, labour hours required for repair, area of the damage and other details that are important.
2. The Ingestion Processor will send both the current damage image and the output of Step 1 to Amazon Bedrock Titan Multimodal Embeddings. In this step the output is a vector representation of the metadata and the image. 
3. The Ingestion Process will pick up the vector and store that vector in Amazon OpenSearch Vector Database, this data being stored on the Vector Database will also contain the plain text metadata from Step 1. 
4. The Ingestion Process will then store the raw image into S3, this will then be used by the inference flow to pull the images and show the matches to the user.

Inference Flow Steps:

1. The user will interact with the UI running on the Image Process, that interaction includes providing the image of a new car damage and some basic information about that damage. The Image Process will grab that information and send to Amazon Bedrock Anthropic Claude 3 Haiku and create a metadata from this new damage as close as possible in format to the metadata that was create on Step 1 as part of the ingestion process. This will make is so that when finding the closest matches the accuracy will be as high as possible.
2. The inference processor will send both the current damage image and the output of Step 5 to Amazon Bedrock Titan Multimodal Embeddings. In this step the output is a vector representation of the metadata and the image. 
3. The Inference Processor component will use the vector to do a similarity search on the Vector Database and find the closest 3 matches.
4. With the closest matches from the Vector Database, the inference processor will use the plain text data that was store with the vector to do a basic calculator of average cost from those closest 3 matches. 
5. The Front End will pull the images from S3 to show it in the UI. The UI will also show the accuracy, the image of each match and the metadata that was stored on each match. 

# Deployment steps:

## Step 1: Enable Bedrock Models

Go To the Bedrock console in one of the Bedrock supported regions and enable at least the following models:

- Amazon Titan Multimoal Embeddings
- Anthropic Claude 3 Haiku

## Step 2: Run CloudFormation template

In this repository, download and run the infra_template.yaml.
This is a Cloudformation template which will deploy all the resource required to run this solution.

## Step 3: Verification of Deployment

Once CloudFormation turns to Create_Complete status, it means all infrastructure was deployed, however the ingestion code might still be running, in order to verify that go to the ecs task for ingestion and check it's cpu/mem usage.

## Step 4: Access Inference Code.

Go to the CloudFormation stack and on the outputs tab, look for the "InferenceUIURL" key, you should see a cloudfront distribution link, click there should take you to the inference ui.