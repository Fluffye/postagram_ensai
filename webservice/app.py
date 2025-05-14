#################################################################################################
##                                                                                             ##
##                                 NE PAS TOUCHER CETTE PARTIE                                 ##
##                                                                                             ##
## 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 ##
import boto3
from botocore.config import Config
import os
import uuid
from dotenv import load_dotenv
from typing import Union
import logging
from fastapi import FastAPI, Request, status, Header
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from getSignedUrl import getSignedUrl

load_dotenv()

app = FastAPI()
logger = logging.getLogger("uvicorn")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
	exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
	logger.error(f"{request}: {exc_str}")
	content = {'status_code': 10422, 'message': exc_str, 'data': None}
	return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)


class Post(BaseModel):
    title: str
    body: str

my_config = Config(
    region_name='us-east-1',
    signature_version='v4',
)

dynamodb = boto3.resource('dynamodb', config=my_config)
table = dynamodb.Table(os.getenv("DYNAMO_TABLE"))
s3_client = boto3.client('s3', config=boto3.session.Config(signature_version='s3v4'))
bucket = os.getenv("BUCKET")

## ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ##
##                                                                                                ##
####################################################################################################

from createPresignedUrl import create_presigned_url


@app.post("/posts")
async def post_a_post(post: Post, authorization: str | None = Header(default=None)):
    """
    Poste un post ! Les informations du poste sont dans post.title, post.body et le user dans authorization
    """
    logger.info(f"title : {post.title}")
    logger.info(f"body : {post.body}")
    logger.info(f"user : {authorization}")

    post_id = str(uuid.uuid4())
    object_name = f"{authorization}/{post_id}/image.png" 
    url = create_presigned_url(bucket, object_name)
    data = table.put_item(
                Item={
                    'user': f"#USER{authorization}",
                    'id': f"#POST{post_id}",
                    'title': post.title,
                    'body': post.body,
                    'image': url,
                    'label': []
                }
            )
    # Doit retourner le résultat de la requête la table dynamodb
    return data


# def get_all_posts():
#     logger.info("Récupération de tous les postes")
#     res = table.scan()
#     return res.get("Items", [])

# def get_posts_by_user(id_user: str):
#     logger.info(f"Récupération des postes de : {id_user}")
#     res = table.query(
#         Select='ALL_ATTRIBUTES',
#         KeyConditionExpression="user = :user",
#         ExpressionAttributeValues={
#             ":user": f"USER#{id_user}",
#         },
#     )
#     return res.get("Items", [])

# Fonction pour récupérer tous les posts
def get_all_posts():
    logger.info("Récupération de tous les postes")
    res = table.scan()
    posts = res.get("Items", [])
    
    # Pour chaque post, ajouter l'URL pré-signée de l'image
    for post in posts:
        object_name = f"{post['user']}/{post['id']}/image.png"  # Chemin de l'image dans S3
        url = create_presigned_url(bucket, object_name)
        post['image'] = url  # Ajouter l'URL pré-signée

    return posts

# Fonction pour récupérer les posts d'un utilisateur
def get_posts_by_user(id_user: str):
    logger.info(f"Récupération des postes de : {id_user}")
    res = table.query(
        Select='ALL_ATTRIBUTES',
        KeyConditionExpression="#u = :user",
        ExpressionAttributeNames={
            "#u": "user"
        },
        ExpressionAttributeValues={
            ":user": f"#USER{id_user}",
        },
    )
    posts = res.get("Items", [])

    # Pour chaque post, ajouter l'URL pré-signée de l'image
    for post in posts:
        object_name = f"{post['user']}/{post['id']}/image.png"  # Chemin de l'image dans S3
        url = create_presigned_url(bucket, object_name)
        post['image'] = url  # Ajouter l'URL pré-signée

    return posts

@app.get("/posts")
async def get_posts(user: Union[str, None] = None):
    """
    Récupère tout les postes. 
    - Si un user est présent dans le requête, récupère uniquement les siens
    - Si aucun user n'est présent, récupère TOUS les postes de la table !!
    """
    id_user = user
    if id_user:
        return get_posts_by_user(id_user)
    else:
        return get_all_posts()



    
@app.delete("/posts/{post_id}")
async def delete_post(post_id: str, authorization: str | None = Header(default=None)):
    # Doit retourner le résultat de la requête la table dynamodb
    logger.info(f"post id : {post_id}")
    logger.info(f"user: {authorization}")
    # Récupération des infos du poste

    # S'il y a une image on la supprime de S3
    object_name = f"{authorization}/{post_id}/image.png" 
    try :
         s3_client.delete_object(Bucket=bucket, Key=object_name)
    finally:
        
    # Suppression de la ligne dans la base dynamodb

    # Retourne le résultat de la requête de suppression

        response = table.delete_item(
            Key={
                'user': f"#USER{authorization}",
                'id': f"#{post_id}"
            }
        )
    return response
    
    


#################################################################################################
##                                                                                             ##
##                                 NE PAS TOUCHER CETTE PARTIE                                 ##
##                                                                                             ##
## 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 👇 ##
@app.get("/signedUrlPut")
async def get_signed_url_put(filename: str,filetype: str, postId: str,authorization: str | None = Header(default=None)):
    return getSignedUrl(filename, filetype, postId, authorization)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="debug")

## ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ☝️ ##
##                                                                                                ##
####################################################################################################