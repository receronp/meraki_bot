import configparser
import json
import sys

import requests

from chatbot import *

from os import makedirs
import settings

# Store credentials in a separate file
def gather_credentials():
    cp = configparser.ConfigParser()
    try:
        cp.read('credentials.ini')
        org_key = cp.get('meraki', 'key1')
        cam_key = cp.get('meraki', 'key2')
        if cam_key == '':
            cam_key = org_key
        org_id = cp.get('meraki', 'organization')
        labels = cp.get('meraki', 'cameras')
        if labels != '':
            labels = labels.split(',')
            cameras = [label.strip() for label in labels]
        else:
            cameras = []
        chatbot_token = cp.get('chatbot', 'token')
        emails = cp.get('chatbot', 'email')
        if ',' in emails:
            emails = emails.split(',')
            user_emails = [mail.strip() for mail in emails]
        else:
            user_emails = [emails]
    except:
        print('Missing credentials or input file!')
        sys.exit(2)
    return org_key, cam_key, org_id, cameras, chatbot_token, user_emails


# Main Lambda function
def lambda_handler(event, context):
    settings.init()
    my_orgs = settings.dashboard.organizations.getOrganizations()
    org_id = my_orgs[0]["id"]

    my_networks = settings.dashboard.organizations.getOrganizationNetworks(org_id)
    for network in my_networks:
        if network["name"] == "Corpo-Texas52":
            corpo_network = network
            break
    
    # Import user credentials
    (org_key, cam_key, org_id, cameras, chatbot_token, user_emails) = gather_credentials()
    headers = {
        'content-type': 'application/json; charset=utf-8',
        'authorization': f'Bearer {chatbot_token}'
    }
    session = requests.Session()

    # Webhook event/metadata received, so now retrieve the actual message for the event
    webhook_event = json.loads(event['body'])
    print(webhook_event)

    # Continue to process message
    message = get_message(session, webhook_event, headers)

    # Webhook event data
    chatbot_id = get_chatbot_id(session, headers)
    user_id = webhook_event['actorId']
    sender_emails = get_emails(session, user_id, headers)
    payload = {'roomId': webhook_event['data']['roomId']}

    # Verifies that message was sent by an authorized user.
    for email in user_emails:
        if email in sender_emails:
            auth_email = True
    
    # Process standard messages
    # Stop if last message was bot's own, or else loop to infinite & beyond!
    if user_id == chatbot_id:
        return {'statusCode': 204}

    # Prevent unauthorized users from using bot
    elif not auth_email:
        post_message(session, headers, payload,
                    f'Hi **{get_name(session, user_id, headers)}**, I\'m not allowed to chat with you! ⛔️')
        return {'statusCode': 200}

    else:
        print(f'Message received: {message}')

        # Create & send response depending on input message
        if message_begins(message, ['hi', 'hello', 'hey', 'help', 'syn', 'test', 'meraki', '?']):
            post_message(session, headers, payload,
                        f'Hi **{get_name(session, user_id, headers)}**! _{message}_ ACKed. ✅')

        # Get org-wide device statuses
        elif message_contains(message, ['org', 'device', 'status', 'online']):
            try:
                # Yes, not PEP 8, but for the sake of modular components & CYOA...
                import status
                status.device_status(session, headers, payload, org_key)

            except ModuleNotFoundError:
                post_message(session, headers, payload, 'You need to include the **status** module first! 🙄')

        # Post camera snapshots
        elif message_contains(message, ['cam', 'photo', 'screen', 'snap', 'shot']):
            try:
                args = str(message).split(' ')

                if (webhook_event["data"]["roomType"] == "group" and len(args) > 2) or (webhook_event["data"]["roomType"] == "direct" and len(args) > 1):
                    # Yes, not PEP 8, but for the sake of modular components & CYOA...
                    import snapshot
                    snapshot.return_snapshots(session, headers, payload, cam_key, org_id, message, cameras)
                else:
                    post_message(session, headers, payload, 'You need to specify one of the following cameras: ' + ", ".join(cameras) + ", all, net")

            except ModuleNotFoundError:
                post_message(session, headers, payload, 'You need to include the **snapshot** module first! 🤦')

        elif message_contains():
            try:
                args = str(message).split(' ')

                # Yes, not PEP 8, but for the sake of modular components & CYOA...
                import cam_analytics
                my_cams = cam_analytics.get_camera(settings.dashboard, corpo_network["id"], "people")
                cam = my_cams["people"][0]
                if message_contains(message, ["live"]):
                    post_message(session, headers, payload, f'There are currently **{cam_analytics.get_people_live_count(cam)}** detected by _{cam["name"]}_.')
                else:
                    post_message(session, headers, payload, f'There are currently **{cam_analytics.get_people_timespan_count(cam)}** detected by _{cam["name"]}_ in the last hour.')

            except ModuleNotFoundError:
                post_message(session, headers, payload, 'You need to include the **snapshot** module first! 🤦')

        # Clear screen to reset demos
        elif message_begins(message, ['clear']):
            clear_screen(session, headers, payload)

        # Catch-all if bot doesn't understand the query!
        else:
            post_message(session, headers, payload, 'Make a wish! 🤪')

    # Let chat app know success
    return {
        'statusCode': 200,
        'body': json.dumps('message received')
    }
