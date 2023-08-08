"""Main file of the app. This file contains the authentication process
and the main features."""

from __future__ import print_function, unicode_literals

import json
from datetime import *

from PyInquirer import prompt
from ticktick.api import TickTickClient
from ticktick.oauth2 import OAuth2

# -------------------------------------------------- INITIALIZATION --------------------------------------------------

# App credentials
APP_ID = "YmQWg8OkoiEe63456Y"
APP_SECRET = "W(L#T@3Bv3O(D5ka!&cZ9ggS3&#B4!Pf"
APP_URI = "http://127.0.0.1:8080"

# Account credentials
USERNAME = "armand.malinvaud@icloud.com"
PASSWORD = "2DB2y\eW~@8QHY>F"

# ID of the group gathering all the interesting task lists
GINETTE_GROUP_ID = '62b4b7cdaa2a9e4c9aa9fdf5'

# Authentication process
auth_client = OAuth2(
    client_id=APP_ID, client_secret=APP_SECRET, redirect_uri=APP_URI)
client = TickTickClient(USERNAME, PASSWORD, auth_client)

# Parsing local data
with open('data.json') as file:
    local_data = json.load(file)

# -------------------------------------------------- MAIN APP --------------------------------------------------

continue_app = True  # Variable indicating whether we should stop the app or not

while continue_app:
    # Main menu
    SCHEMA_MSG = 'Ajouter / modifier / supprimer un schéma de répétition'
    TASK_MSG = 'Ajouter / modifier / supprimer un cours'
    QUIT_MSG = 'Quitter le programme'

    main_menu = [
        {
            'type': 'list',
            'name': 'main_menu',
            'message': 'Que voulez-vous faire ?',
            'choices': [TASK_MSG, SCHEMA_MSG, QUIT_MSG]
        }
    ]

    main_menu_answer = prompt(main_menu)['main_menu']

    # Task menu
    if main_menu_answer == TASK_MSG:
        # Options shown to the user
        CREATE_TASK_MSG = 'Créer un cours'
        EDIT_TASK_MSG = 'Éditer un cours existant'
        DELETE_TASK_MSG = 'Supprimer un cours existant'
        BACK_TO_MAIN_MSG = 'Revenir au menu principal'

        # Configuration dict for the menu
        task_menu = [
            {
                'type': 'list',
                'name': 'task_menu',
                'message': 'Quelle opération voulez-vous effectuer sur vos cours ?',
                'choices': [CREATE_TASK_MSG, EDIT_TASK_MSG, DELETE_TASK_MSG, BACK_TO_MAIN_MSG]
            }
        ]

        task_menu_answer = prompt(task_menu)['task_menu'] # Displays the menu

        # Task creation menu
        if task_menu_answer == CREATE_TASK_MSG:
            # Options for priority
            PRIORITY_NONE = 'Pas de priorité'
            PRIORITY_LOW = 'Basse'
            PRIORITY_MEDIUM = 'Moyenne'
            PRIORITY_HIGH = 'Élevée'

            # Utility functions
            def projectName2ID(projectName):
                for project in client.state['projects']:
                    if projectName == project['name']:
                        return project['id']
            
            def schemaName2List(schemaName):
                for schema in local_data['rehearsal_schemas']:
                    if schema['name'] == schemaName:
                        return schema['schema']
            
            def priority2Int(priorityName):
                converter = {PRIORITY_NONE: 0, PRIORITY_LOW: 1, PRIORITY_MEDIUM: 3, PRIORITY_HIGH: 5}
                return converter[priorityName]

            # Menu configuration
            task_creation_menu = [
                {
                    'type': 'input',
                    'name': 'title',
                    'message': 'Titre du cours à réviser :'
                },
                {
                    'type': 'list',
                    'name': 'projectId',
                    'message': 'Matière :',
                    'choices': list(map(lambda project: project['name'], filter(lambda project: project['groupId'] == GINETTE_GROUP_ID, client.state['projects']))),
                    'filter': projectName2ID 
                },
                {
                    'type': 'list',
                    'name': 'rehearsalSchema',
                    'message': 'Schéma de répétition :',
                    'choices': list(map(lambda schema: schema['name'], local_data['rehearsal_schemas'])),
                    'filter': schemaName2List
                },
                {
                    'type': 'list',
                    'name': 'priority',
                    'message': 'Priorité :',
                    'choices': [PRIORITY_MEDIUM, PRIORITY_LOW, PRIORITY_HIGH, PRIORITY_NONE],
                    'filter': priority2Int
                }
            ]

            task_data = prompt(task_creation_menu) # Displays the menu and retrieves the answers

            # We create the different tasks, store their dict in JSON file
            created_tasks = []

            for day_delta in task_data['rehearsalSchema']:
                # We create the task corresponding to this time interval
                created_tasks.append(
                    client.task.create(
                        client.task.builder(
                            title=task_data['title'],
                            projectId=task_data['projectId'],
                            startDate=datetime.combine(date.today(), time()) + timedelta(days=day_delta),
                            priority=task_data['priority'],
                            allDay=True
                        )
                    )
                )
            
            local_data['tasks'].append({
                'title': task_data['title'],
                'tasks_dicts': created_tasks
            })

            # We dump current data into the file
            with open('data.json', 'w') as file:
                json.dump(local_data, file)

        elif task_menu_answer == EDIT_TASK_MSG:
            pass

        elif task_menu_answer == DELETE_TASK_MSG:
            pass
    
    # Menu handling rehearsal schemas
    elif main_menu_answer == SCHEMA_MSG:
        pass

    else:
        continue_app = False
