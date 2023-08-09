"""Main file of the app. This file contains the authentication process
and the main features."""

import json
from datetime import *
from enum import Enum

import inquirer
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

# Enumerations for the menus
MainMenuChoices = Enum('MainMenuChoices', ['TASK', 'SCHEMA', 'QUIT'])
TaskMenuChoices = Enum('TaskMenuChoices', ['CREATE', 'EDIT', 'DELETE', 'QUIT'])
Priority = Enum('Priority', [('NO_PRIORITY', 0),
                ('LOW', 1), ('MEDIUM', 3), ('HIGH', 5)])

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
    main_menu_answer = inquirer.list_input(
        'Que voulez-vous faire ? ',
        choices=[
            ('Ajouter / modifier / supprimer un cours', MainMenuChoices.TASK),
            ('Ajouter / modifier / supprimer un schéma de répétition',
             MainMenuChoices.SCHEMA),
            ('Quitter le programme', MainMenuChoices.QUIT)
        ]
    )

    # Task menu
    if main_menu_answer == MainMenuChoices.TASK:
        # Task menu
        task_menu_answer = inquirer.list_input(
            'Quelle opération voulez-vous effectuer sur vos cours ? ',
            choices=[
                ('Créer un cours', TaskMenuChoices.CREATE),
                ('Éditer un cours existant', TaskMenuChoices.EDIT),
                ('Supprimer un cours existant', TaskMenuChoices.DELETE),
                ('Revenir au menu principal', TaskMenuChoices.QUIT)
            ]
        )

        # Task creation menu
        if task_menu_answer == TaskMenuChoices.CREATE:
            # Task menu configuration and displaying
            task_data = inquirer.prompt([
                inquirer.Text('title', 'Titre du cours à réviser'),
                inquirer.List('projectId', 'Matière', list(map(lambda project: (project['name'], project['id']), filter(
                    lambda project: project['groupId'] == GINETTE_GROUP_ID, client.state['projects'])))),
                inquirer.List('rehearsalSchema', 'Schéma de répétition', list(
                    map(lambda schema: (schema['name'], schema['schema']), local_data['rehearsal_schemas']))),
                inquirer.List('priority', 'Priorité', [('Élevée', Priority.HIGH.value), ('Moyenne', Priority.MEDIUM.value), (
                    'Basse', Priority.LOW.value), ('Pas de priorité', Priority.NO_PRIORITY.value)])
            ])

            if task_data is not None:
                # We create the different tasks, store their dict in JSON file
                created_tasks = []

                for day_delta in task_data['rehearsalSchema']:
                    # We create the task corresponding to this time interval
                    created_tasks.append(
                        client.task.create(
                            client.task.builder(
                                title=task_data['title'],
                                projectId=task_data['projectId'],
                                startDate=datetime.combine(
                                    date.today(), time()) + timedelta(days=day_delta),
                                priority=task_data['priority'],
                                allDay=True
                            )
                        )
                    )

                local_data['tasks'].append({
                    'title': task_data['title'],
                    'projectId': task_data['projectId'],
                    'rehearsalSchema': task_data['rehearsalSchema'],
                    'priority': task_data['priority'],
                    'tasks_dicts': created_tasks
                })

                # We dump current data into the file
                with open('data.json', 'w') as file:
                    json.dump(local_data, file)

        elif task_menu_answer == TaskMenuChoices.EDIT:
            if len(local_data['tasks']) > 0:
                edited_task_rank = inquirer.list_input('Tâche que vous souhaitez éditer', choices=[
                                                       (task['title'], k) for k, task in enumerate(local_data['tasks'])])

                # Data stored locally
                local_task_data = local_data['tasks'][edited_task_rank]

                # We prompt the user for new data, with the right default values
                new_task_data = inquirer.prompt([
                    inquirer.Text('title', 'Titre du cours à réviser',
                                  local_task_data['title']),
                    inquirer.List('projectId', 'Matière', list(map(lambda project: (project['name'], project['id']), filter(
                        lambda project: project['groupId'] == GINETTE_GROUP_ID, client.state['projects']))), local_task_data['projectId']),
                    inquirer.List('rehearsalSchema', 'Schéma de répétition', list(
                        map(lambda schema: (schema['name'], schema['schema']), local_data['rehearsal_schemas'])), local_task_data['rehearsalSchema']),
                    inquirer.List('priority', 'Priorité', [('Élevée', Priority.HIGH.value), ('Moyenne', Priority.MEDIUM.value), (
                        'Basse', Priority.LOW.value), ('Pas de priorité', Priority.NO_PRIORITY.value)], local_task_data['priority'])
                ])

                # First, we have to delete the former tasks
                client.task.delete(local_data['tasks'][edited_task_rank]['tasks_dicts'])
                local_data['tasks'].pop(edited_task_rank)

                with open('data.json', 'w') as file:
                    json.dump(local_data, file)

                # Then we recreate the task
                created_tasks = []

                for day_delta in new_task_data['rehearsalSchema']:
                    # We create the task corresponding to this time interval
                    created_tasks.append(
                        client.task.create(
                            client.task.builder(
                                title=new_task_data['title'],
                                projectId=new_task_data['projectId'],
                                startDate=datetime.combine(
                                    date.today(), time()) + timedelta(days=day_delta),
                                priority=new_task_data['priority'],
                                allDay=True
                            )
                        )
                    )

                local_data['tasks'].append({
                    'title': new_task_data['title'],
                    'projectId': new_task_data['projectId'],
                    'rehearsalSchema': new_task_data['rehearsalSchema'],
                    'priority': new_task_data['priority'],
                    'tasks_dicts': created_tasks
                })

                # We dump current data into the file
                with open('data.json', 'w') as file:
                    json.dump(local_data, file)

            else:
                print('Aucune tâche à éditer')

        elif task_menu_answer == TaskMenuChoices.DELETE:
            if len(local_data['tasks']) > 0:
                deleted_task_rank = inquirer.list_input('Tâche que vous souhaitez supprimer', choices=[
                                                        (task['title'], k) for k, task in enumerate(local_data['tasks'])])

                # Deletion of the task on TickTick
                client.task.delete(
                    local_data['tasks'][deleted_task_rank]['tasks_dicts'])
                # Deletion of the task stored locally
                local_data['tasks'].pop(deleted_task_rank)

                with open('data.json', 'w') as file:
                    json.dump(local_data, file)

            else:
                print('Aucune tâche à supprimer')

    # Menu handling rehearsal schemas
    elif main_menu_answer == MainMenuChoices.SCHEMA:
        pass

    else:
        continue_app = False

# TODO :
# - Menu des schémas
# - Refactoriser tout le code
# - Gérer l'interruption d'un menu par l'utilisateur
# - Afficher des messages d'attente (les colorer si possible)