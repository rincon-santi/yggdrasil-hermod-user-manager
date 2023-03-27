import os
import logging
logging.basicConfig(level=logging.INFO)
import json
import firebase_admin
from firebase_admin import firestore
import functions_framework
from typing import Dict
import base64
from gcsfs import GCSFileSystem

PROJECT_ID = os.environ.get('PROJECT_ID')
EVENT_BUS = os.environ.get('EVENT_BUS')
ENTITY = "user"
APP = firebase_admin.initialize_app()

def _create_user(user_id:str, payload:Dict):
    logging.info("Creating user {}".format(user_id))
    firestore_client = firestore.client()
    firestore_client.collection(u'users').document(user_id).set({
        u'activeConversations': [],
        u'ownedConversations': {},
        u'authorizedCommands': payload['authorizedCommands']
    })
    logging.info("Created")

def _delete_conversation(user_id:str, conversation_list:str, conversation_id: str):
    logging.info("Deleting conversation from {} for user {}".format(conversation_list, user_id))
    firestore_client = firestore.client()
    doc_ref = firestore_client.collection(u'users').document(user_id)
    doc = doc_ref.get().to_dict()
    if conversation_list=="ownedConversations":
        doc.update({conversation_list: [x for x in doc[conversation_list] if x!=conversation_id]})
    else:
        doc.update({conversation_list:{key: doc[conversation_list][key] for key in doc[conversation_list].keys() if doc[conversation_list][key]!=conversation_id}})
    doc_ref.set(doc)
    logging.info("Deleted")

def _assign_conversation(user_id:str, conversation_list:str, conversation_id: str, channel:str):
    logging.info("Assigning conversation to {} for user {}".format(conversation_list, user_id))
    firestore_client = firestore.client()
    doc_ref = firestore_client.collection(u'users').document(user_id)
    doc = doc_ref.get().to_dict()
    if conversation_list=="ownedConversations":
        try:
            previous_list = doc[conversation_list]
            previous_list.append(conversation_id)
        except:
            previous_list = [conversation_id,]
        doc.update({conversation_list: previous_list})
    else:
        doc.update({conversation_list:{channel: conversation_id}})
    doc_ref.set(doc)
    logging.info("Assigned")

def _retrieve_spoke(user_id:str, payload:Dict):
    spoke_id = payload["spokeId"]
    brain = payload["brain"]
    logging.info("Retrieving spoke {} for user {}".format(spoke_id, user_id))
    firestore_client = firestore.client()
    doc_ref = firestore_client.collection(u'users').document(user_id).collection(u'spokes').document(spoke_id)
    fs = GCSFileSystem(project=PROJECT_ID)
    with fs.open("gs://yggdrasil-ai-hermod-spokes/"+user_id+"/"+brain+"/"+spoke_id+".json", "r") as f:
        spoke = json.load(f)
    doc_ref.set(spoke)
    logging.info("Retrieved")

def _delete_spoke(user_id:str, payload:Dict):
    spoke_id = payload["spokeId"]
    logging.info("Deleting spoke {} for user {}".format(spoke_id, user_id))
    firestore_client = firestore.client()
    doc_ref = firestore_client.collection(u'users').document(user_id).collection(u'spokes').document(spoke_id)
    doc_ref.delete()
    logging.info("Deleted")

# Triggered from a message on a Cloud Pub/Sub topic.
@functions_framework.cloud_event
def user_manager(cloud_event):
    event = json.loads(base64.b64decode(cloud_event.data["message"]["data"]).decode())
    if event['entity']==ENTITY:
        payload = json.loads(event['payload'])
        if event['operation']=="deleteConversation":
            _delete_conversation(user_id=event['entityId'], conversation_list=payload['conversationList'], conversation_id=payload["conversationId"])
        elif event['operation']=="assignConversation":
            _assign_conversation(user_id=event['entityId'], conversation_list=payload['conversationList'], conversation_id=payload["conversationId"], channel=payload["channel"])
        elif event['operation']=="create":
            _create_user(user_id=event['entityId'], payload=json.loads(event["payload"]))
        elif event['operation']=="retrieveSpoke":
            _retrieve_spoke(user_id=event['entityId'], payload=json.loads(event["payload"]))
        elif event['operation']=="deleteSpoke":
            _delete_spoke(user_id=event['entityId'], payload=json.loads(event["payload"]))