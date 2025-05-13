import json
from urllib.parse import unquote_plus
import boto3
import os
import logging
print('Loading function')
logger = logging.getLogger()
logger.setLevel("INFO")
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
reckognition = boto3.client('rekognition')

table = dynamodb.Table(os.getenv("DYNAMO_TABLE"))

def lambda_handler(event, context):
    # logger.info(json.dumps(event, indent=2))
    # bucket = ""
    # key = unquote_plus(event) # <- A modifier !!!!

    # # Récupération de l'utilisateur et de l'UUID de la tâche
    

    # # Ajout des tags user et task_uuid

    # # Appel à reckognition
    # label_data = reckognition.detect_labels(

    # )
    # logger.info(f"Labels data : {label_data}")

    # # Récupération des résultats des labels


    # # Mise à jour de la table dynamodb
    # table.update_item(

    # )
    return None