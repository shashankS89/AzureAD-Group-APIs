from settings.config import azure_client_id, azure_client_secret, azure_tenant_id
import json
import logging
import random
import requests
from static.constants import application_name

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


def get_access_token():
    # to get access token which will be used for fetching other information.

    # Construct the token endpoint URL
    token_endpoint = (
        f"https://login.microsoftonline.com/{azure_tenant_id}/oauth2/v2.0/token"
    )

    # Obtain an access token using client credentials flow
    payload = {
        "grant_type": "client_credentials",
        "client_id": azure_client_id,
        "client_secret": azure_client_secret,
        "scope": "https://graph.microsoft.com/.default",
    }

    response = requests.post(token_endpoint, data=payload)
    access_token = response.json()["access_token"]
    return access_token


def get_azure_ad_group(search_query):
    # to get azure ad group matching given search text

    # Set the API endpoint for retrieving groups
    groups_endpoint = "https://graph.microsoft.com/v1.0/groups"

    # Construct the request URL with the search query
    request_url = f"{groups_endpoint}?$filter=startswith(displayName, '{search_query}')"
    access_token = get_access_token()

    # Set the headers with the access token
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # Send the GET request to retrieve groups with search
    response = requests.get(request_url, headers=headers)
    groups = response.json()
    response = []
    for group in groups["value"]:
        group_id = group["id"]
        group_display_name = group["displayName"]
        group_object = {"group_id": group_id, "group_name": group_display_name}
        response.append(group_object)

    return response


def getUniqueGroupName(app_name, access_token):
    # to get unique group name

    display_name = None
    while True:
        seven_digit_number = random.randint(1000000, 9999999)
        display_name = f"{application_name}_{app_name}_{seven_digit_number}"

        url = f"https://graph.microsoft.com/v1.0/groups?$filter=displayName eq '{display_name}'"
        headers = {"Authorization": f"Bearer {access_token}"}

        response = requests.get(url, headers=headers)

        logging.info(response.json)
        groups = response.json().get("value", [])

        if not groups:
            break
    return display_name


def addMemeberInGroup(group_id, access_token, users_list):
    # to add member in specific group

    logger.info(f"user need to add in azure users_list::{users_list}")
    data = {"members@odata.bind": []}
    for users in users_list:
        data["members@odata.bind"].append(
            f"https://graph.microsoft.com/v1.0/users/{users}"
        )
    payload = json.dumps(data)

    url = f"https://graph.microsoft.com/v1.0/groups/{group_id}"

    response = requests.request(
        "PATCH",
        url,
        headers={
            "Authorization": "Bearer " + access_token,
            "Content-type": "application/json",
        },
        data=payload,
    )
    if response.status_code == 204:
        logging.info("User or owner added successfully.")
    else:
        logging.info(f"Failed to add user or owner. Error: {response.text}")
    return "Done"


def createAzureADGroup(app_name, group_desc, access_token):
    # to create azure ad group
    graph_url = "https://graph.microsoft.com/v1.0"

    azure_group_owner = "YOUR_EMAIL"
    azure_ad_group_name = getUniqueGroupName(app_name, access_token)
    # Group properties
    group_properties = {
        "displayName": azure_ad_group_name,
        "description": group_desc,
        "mailEnabled": False,
        "mailNickname": "Nickname",
        "securityEnabled": True,
        "owners@odata.bind": [
            f"https://graph.microsoft.com/v1.0/users/{azure_group_owner}"
        ],
    }

    # Request URL for creating a group
    request_url = f"{graph_url}/groups"

    # Set headers with the access token
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    # Make the request to create the group
    response = requests.post(
        request_url, headers=headers, data=json.dumps(group_properties)
    )
    new_group = response.json()
    logging.info("new_group", new_group)

    # Access the created group information
    group_id = new_group["id"]
    group_name = new_group["displayName"]

    # Print the created group information
    logging.info(f"Group ID: {group_id}")
    logging.info(f"Group Name: {group_name}")

    response = {"group_id": group_id, "group_name": group_name}
    return response


def deleteMemeberInGroup(group_id, access_token, users_list):
    # to delete users from specific group
    users_id = []
    url_to_get_users = f"https://graph.microsoft.com/v1.0/groups/{group_id}/members"

    if len(users_list) != 0:
        response_for_users = requests.request(
            "GET", url_to_get_users, headers={"Authorization": "Bearer " + access_token}
        ).json()

        for users in response_for_users["value"]:
            if users["mail"] in users_list:
                users_id.append(users["id"])

        for members in users_id:
            response = requests.request(
                "DELETE",
                f"https://graph.microsoft.com/v1.0/groups/{group_id}/members/{members}/$ref",
                headers={"Authorization": "Bearer " + access_token},
            )
            logging.info("users_deleted", members)


def addAzureADInExistingAzureADGroup(access_token, group_id, member_group_ids):
    # to add specific groups to parent group

    # Set your Azure AD group details
    group_id = group_id

    # Set your access token (required permissions: Group.ReadWrite.All)
    access_token = access_token

    # Construct the URL
    url = f"https://graph.microsoft.com/v1.0/groups/{group_id}/members/$ref"

    # Set the request headers
    headers = {
        "Authorization": "Bearer " + access_token,
        "Content-Type": "application/json",
    }

    # Set the request body

    for member_id in member_group_ids:
        data = {"@odata.id": f"https://graph.microsoft.com/v1.0/groups/{member_id}"}

        # Send the POST request
        response = requests.post(url, headers=headers, data=json.dumps(data))

        # Check the response status code
        if response.status_code == 204:
            logging.info("Azure AD group added successfully.")
        else:
            logging.info(
                "Failed to add Azure AD group. Status code:", response.status_code
            )


def deleteAzureADFromExistingAzureADGroup(
    access_token, parent_group_id, member_group_ids
):
    # to delete specific group from parent group

    # Set your access token (required permissions: Group.ReadWrite.All)
    access_token = access_token

    # Set the headers
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    for member_id in member_group_ids:
        url = f"https://graph.microsoft.com/v1.0/groups/{parent_group_id}/members/{member_id}/$ref"

        # Send the DELETE request to remove the child group from the parent group
        response = requests.delete(url, headers=headers)

        # Check the response status code
        if response.status_code == 204:
            logging.info(
                "Child group successfully removed from the parent group.")
        else:
            logging.info(
                f"Failed to remove child group. Status code: {response.status_code}, Error: {response.text}"
            )


def getAzureUserMembers(group_id, access_token, number_of_users=990):
    # to get list of users present in specific group

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    azure_user_list = []
    # Adjust $top as needed
    transitive_members_url = f"https://graph.microsoft.com/v1.0/groups/{group_id}/transitiveMembers?$top={number_of_users}"
    response = requests.get(transitive_members_url, headers=headers)

    if response.status_code == 200:
        members = response.json().get("value", [])
        for member in members:
            azure_user_list.append(member.get("userPrincipalName"))

    return azure_user_list


def get_number_of_user_from_azure_AD_group(group_id, access_token):
    # to get total number of users in specific group

    members_url = (
        f"https://graph.microsoft.com/v1.0/groups/{group_id}/transitiveMembers/$count"
    )
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "ConsistencyLevel": "eventual",
    }
    members_response = requests.get(members_url, headers=headers)
    no_of_users = 0
    no_of_users = json.loads(members_response.text)
    logger.info(f"number of users::{no_of_users}")
    return int(no_of_users)


def check_specific_user_present_in_group(group_id, access_token, user_email):
    # to get user list matching given user email in specific group

    search_url = f"https://graph.microsoft.com/v1.0/groups/{group_id}/transitiveMembers?$count=true&$filter=startswith(userPrincipalName,{user_email})"

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json',
        "ConsistencyLevel": "eventual"
    }
    response = requests.get(search_url, headers=headers)
    searched_users = response.json()

    return searched_users
