# Simplifying Automotive Damage Processing with Amazon Bedrock and Vector Databases

Assessing the costs related to repairing damages on assets is a challenge that all industries have, in particular automotive companies have had this challenge for a long time. 

There are multiple market solution that leverage Machine Learning processes targeted on addressing this challenge. 

The proposal of this solution is to offer a new method levearging GenAI and MultiModal Vector Databases.


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