"""This file contains the definition of the <TickTickSchedulerClient> class,
which allows the script to properly interact with TickTick's API for task
creation, edition and deletion"""

import json
import sys
from datetime import *

import requests
from colorama import Fore

from TickTickOAuth2 import TickTickOAuth2

# TickTick's API URLs
BASE_URL = "https://api.ticktick.com"
CREATE_TASK_URL = f"{BASE_URL}/open/v1/task"
DELETE_TASK_URL = (
    lambda projectId, taskId: f"{BASE_URL}/open/v1/project/{projectId}/task/{taskId}"
)
GET_PROJECTS_URL = f"{BASE_URL}/open/v1/project"


class TickTickSchedulerClient:
    def __init__(self, client_id, client_secret, redirect_uri, task_group_id, tasks_tag="révision"):
        """Initialises the attributes, the OAuth2 client and fetches the projects
        associated with the specified group of tasks"""

        self.tasks_tag = tasks_tag

        # Initialisation of the OAuth client
        self.oauth_client = TickTickOAuth2(client_id, client_secret, redirect_uri)

        # We retrieve the projects of the user
        print(Fore.YELLOW + "Récupération des projets...")

        projects_response = requests.get(
            GET_PROJECTS_URL, headers=self.oauth_client.auth_header
        )

        if projects_response.status_code != requests.codes.ok:
            print(Fore.RED + "Impossible de récupérer les projets")
            sys.exit(1)

        # We only keep the projects belonging to the specified group
        self._client_projects = list(
            filter(
                lambda project: "groupId" in project
                and project["groupId"] == task_group_id,
                projects_response.json(),
            )
        )
        print(Fore.GREEN + "Projets récupérés avec succès\n")

    @property
    def projects(self):
        """Accessor method for the client projects"""
        return self._client_projects

    def batch_create_tasks(self, title, project_ID, priority, schema):
        """Creates multiple tasks according to a rehearsal schema"""

        # We need to save the IDs of the tasks we create here for later modifications
        tasks_ids = []

        # We iterate through the schema and create a task for each rehearsal
        for day_delta in schema:
            task_date = datetime.combine(date.today(), time()) + timedelta(days=day_delta)

            # Payload to be sent with the request
            task_data = {
                "title": title,
                "projectId": project_ID,
                "startDate": f"{task_date.strftime("%Y-%m-%dT%H:%M:%S")}+0000",
                "priority": priority,
                "isAllDay": True,
                "tags": [self.tasks_tag],
            }

            response = requests.post(CREATE_TASK_URL, data=json.dumps(task_data), headers=self.oauth_client.auth_header)

            if response.status_code != requests.codes.ok:
                print(Fore.RED + "Impossible de créer les tâches")
                sys.exit(1)
            
            tasks_ids.append(response.json()['id'])

        return tasks_ids
            
    def batch_delete_tasks(self, project_ID, tasks_ids):
        """Deletes the tasks associated with the given IDs"""

        for id in tasks_ids:
            response = requests.delete(
                DELETE_TASK_URL(project_ID, id),
                headers=self.oauth_client.auth_header,
            )

            if response.status_code != requests.codes.ok:
                print(Fore.RED + "Erreur : impossible de supprimer la tâche")
                sys.exit(1)
