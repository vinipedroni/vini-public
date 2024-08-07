# Simplifying Automotive Damage Processing with Amazon Bedrock and Vector Databases

Assessing the costs related to repairing damages on assets is a challenge that all industries have, in particular automotive companies have had this challenge for a long time. 

There are multiple market solution that leverage Machine Learning processes targeted on addressing this challenge. 

The proposal of this solution is to offer a new method levearging GenAI and MultiModal Vector Databases.

# Solution Details:

The solution involves two important parts, the ingestion and the inference. Below is the architecture:

![Sol Arch](/static_assets/damage_repair_sol.png)  

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

Choose from one of the following deployment regions, right now this solution can only run on regions where bedrock is supported.

CloudFormation Deployments
| Region | CloudFormation Link |
| :---: | ---: |
| US-EAST-1 | [![Open In CloudFormation](/static_assets/view-template.png)](https://us-east-1.console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/quickcreate?templateURL=https://s3.us-east-1.amazonaws.com/pedroni-us-east-1/new_build_proj.yml)|
| US-EAST-2 | [![Open In CloudFormation](/static_assets/view-template.png)](https://us-east-2.console.aws.amazon.com/cloudformation/home?region=us-east-2#/stacks/quickcreate?templateURL=https://s3.us-east-1.amazonaws.com/pedroni-us-east-1/new_build_proj.yml)|
| US-WEST-2 | [![Open In CloudFormation](/static_assets/view-template.png)](https://us-west-2.console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/quickcreate?templateURL=https://s3.us-east-1.amazonaws.com/pedroni-us-east-1/new_build_proj.yml)|
| EU-CENTRAL-1 | [![Open In CloudFormation](/static_assets/view-template.png)](https://eu-central-1.console.aws.amazon.com/cloudformation/home?region=eu-central-1#/stacks/quickcreate?templateURL=https://s3.us-east-1.amazonaws.com/pedroni-us-east-1/new_build_proj.yml)|

## Step 3: Verification of Deployment

Once CloudFormation turns to Create_Complete status, it means all infrastructure was deployed, however the ingestion code might still be running, in order to verify that go to the ecs task for ingestion and check it's cpu/mem usage.

## Step 4: Access Inference Code.

Go to the CloudFormation stack and on the outputs tab, look for the "InferenceUIURL" key, you should see a cloudfront distribution link, click there should take you to the inference ui.

![CFN Outputs](/static_assets/cfn_output.png)

# Testing the Solution:

## Test 1: Images which have been vectorized and are stored in OpenSearch

1. In the UI, take the following actions and load the 'civic_test_1.jpeg' image:
- For Make and Model, select: Honda/Civic
- For Damage Area, select: Driver Side and Driver Side Door
- For Damage Type, select: Scratch
- For Damage Severity, select: moderate

![Test1_Param](Test1_Parameters.png)

2. This image is in the Vector DB, so there should be a match close to 100% accuracy.

![Test1_Results](Test1_Results.png)

In this example, we can see it found the closest 3 matches, and by order of accuracy, they are 0.99950504, 0.92682207, and 0.92027134.

3. The 0.99 is the closest match that we found in the DB, and the only difference is that the ingested image has a slightly different metadata from what we created when we ran the inference.

4. Now let's see how changing the options from the user changes the accuracy of the results. Let's modify the Make and Model to Toyota Corolla, as shown in the image below:

![Test1_Results](Test1_less_accurate.png)

5. Our results went from 0.9995 to 0.9978193. We still have a high match because it's the same image, but just changing a small parameter from the UI decreased the vector match. This means that the more accurate we can be on our metadata, the closest match we will find, and the more accurate the damage image will be that matches the make, model, and other parameters from the user.

6. Play around with the images in the 'test_dataset' folder, or even try some images from the data set we loaded into the Vector DB.

7. Under the image upload button, there will be the JSON metadata created by Claude for the current image as well as the metadata stored in OpenSearch alongside the vector. We can use that to compare how the images were ingested and how close the metadatas are.

## Test 2: Images which have NOT been vectorized and are stored in OpenSearch

1. In the UI, take the following actions and load the 'corolla_blue_1.png' image:
- For Make and Model, select: Toyota/Corolla
- For Damage Area, select: Rear Left and Hood
- For Damage Type, select: Broken
- For Damage Severity, select: severe

![Test2_Param](Test2_Parameters.png)

2. This image is not in the Vector DB, so we should be getting a high match, due to other similar damages in the DB, however, it will be around the 0.90 accuracy, as shown below:

![Test2_Results](Test2_Results.png)

3. The results we got are 0.928969, 0.92857015, 0.92395175, and the images in these results are quite close to the real damage we are assessing.

4. Now let's play around with the parameters. Refresh your page, choose the same make and model, and the following parameters:
- Damage Area: Front Right and Passenger Side
- Damage Type: Dent, Scratch and Fender Bender
- Damage Severity: severe

![Test2_Results](Test2_more_accurate.png)

5. The new results are 0.92993426, 0.92886454, 0.92356765. The accuracy increased on all 3 matches because the metadata using the new parameters is closest to the ones that were stored in the ingestion process, and therefore the vector is a closer match.

6. Under the image upload button, there will be the JSON metadata created by Claude for the current image as well as the metadata stored in OpenSearch alongside the vector. We can use that to compare how the images were ingested and how close the metadatas are.