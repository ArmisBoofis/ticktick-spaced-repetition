"""Main file of the app. This file contains the authentication process
and the main features."""

import json
import re
from datetime import *
from enum import Enum

import inquirer
from colorama import Fore, init

from StorageManager import StorageManager
from TickTickSchedulerClient import TickTickSchedulerClient

init(autoreset=True)  # Initialization for colorama

# -------------------------------------------------- CONSTANTS --------------------------------------------------

# App credentials
APP_ID = "YmQWg8OkoiEe63456Y"
APP_SECRET = "W(L#T@3Bv3O(D5ka!&cZ9ggS3&#B4!Pf"
APP_URI = "http://127.0.0.1:8080"

# ID of the group gathering all the interesting task lists
GINETTE_GROUP_ID = "62b4b7cdaa2a9e4c9aa9fdf5"

# Path to the configuration file (prompts displayed in the various menus)
CONFIG_FILE_PATH = "./config.json"

# Parsing configuration
with open(CONFIG_FILE_PATH, encoding="utf8") as file:
    config = json.load(file)

# ------------------------------------------------------ INITIALISATION -----------------------------------------

# We create a <TickTickSchedulerClient> instance and a <StorageManager> instance
api_client = TickTickSchedulerClient(APP_ID, APP_SECRET, APP_URI, GINETTE_GROUP_ID)
storage_manager = StorageManager()

# -------------------------------------------------- UTILITY FUNCTIONS --------------------------------------


def batch_create(title, project_id, priority, schema_id):
    """This function creates multiple tasks according to a rehearsal schema, and
    stores them both online and locally."""

    print(Fore.YELLOW + "Création de la tâche...")

    # First we retrieve the schema corresponding to the given ID
    schema_data = storage_manager.fetch_schema_data(schema_id)

    # We create the different tasks, first online and then we store the data locally
    tasks_ids = api_client.batch_create_tasks(
        title, project_id, priority, schema_data["schema"]
    )
    storage_manager.save_task(schema_data["id"], title, project_id, priority, tasks_ids)

    print(Fore.GREEN + "Tâche créée avec succès\n")


def batch_delete(task_local_id):
    """This function deletes a task that has been repeated
    following a rehearsal schema"""

    print(Fore.YELLOW + "Suppression de la tâche...")

    # First we retrieve the task corresponding to this local id
    task_data = storage_manager.fetch_task_data(task_local_id)

    # We delete the task on TickTick and then locally
    api_client.batch_delete_tasks(task_data["project_id"], task_data["rehearsal_ids"])
    storage_manager.delete_task(task_data["id"])

    print(Fore.GREEN + "Tâche supprimée avec succès\n")


# -------------------------------------------------- MENUS --------------------------------------------------

# Enumerations for the menus
MainMenuChoices = Enum("MainMenuChoices", ["TASK", "SCHEMA", "QUIT"])
TaskMenuChoices = Enum("TaskMenuChoices", ["CREATE", "EDIT", "DELETE", "QUIT"])
SchemaMenuChoices = Enum("SchemaMenuChoices", ["CREATE", "EDIT", "DELETE", "QUIT"])
Priority = Enum(
    "Priority", [("NO_PRIORITY", 0), ("LOW", 1), ("MEDIUM", 3), ("HIGH", 5)]
)


def prompt_task_data(title=None, project_id=None, schema_id=None, priority=None):
    """This function displays a menu prompting the user for all the information needed
    to create or edit a task. The arguments define default values."""

    return inquirer.prompt(
        [
            inquirer.Text(
                "title", config["task_creation_menu"]["title_message"], title
            ),
            inquirer.List(
                "project_id",
                config["task_creation_menu"]["project_message"],
                list(
                    map(
                        lambda project: (project["name"], project["id"]),
                        api_client.projects,
                    )
                ),
                project_id,
            ),
            inquirer.List(
                "schema_id",
                config["task_creation_menu"]["schema_message"],
                storage_manager.fetch_schemas_descriptors(),
                schema_id,
            ),
            inquirer.List(
                "priority",
                config["task_creation_menu"]["priority_message"],
                [
                    (
                        config["task_creation_menu"]["priority"]["high"],
                        Priority.HIGH.value,
                    ),
                    (
                        config["task_creation_menu"]["priority"]["medium"],
                        Priority.MEDIUM.value,
                    ),
                    (
                        config["task_creation_menu"]["priority"]["low"],
                        Priority.LOW.value,
                    ),
                    (
                        config["task_creation_menu"]["priority"]["none"],
                        Priority.NO_PRIORITY.value,
                    ),
                ],
                priority,
            ),
        ]
    )


def prompt_task_selection():
    """This function displays a menu prompting the user
    to select an existing task."""

    answer = inquirer.prompt(
        [
            inquirer.List(
                "selection",
                config["task_selection_menu"]["message"],
                choices=storage_manager.fetch_tasks_descriptors(),
            )
        ]
    )

    return answer["selection"] if answer is not None else None


def prompt_schema_data(name=None, schema_text=None):
    """This function displays a menu that prompts the user to
    enter the needed data to create a new rehearsal schema.
    The arguments correspond to default values for each field."""

    # We prompt the raw data first
    data = inquirer.prompt(
        [
            inquirer.Text("name", config["schema_creation_menu"]["name_message"], name),
            inquirer.Text(
                "schema",
                config["schema_creation_menu"]["schema_message"],
                schema_text,
                validate=lambda _, c: re.fullmatch("([0-9]+ ?)+", c) is not None,
            ),
        ]
    )

    # We then have to convert the schema to the appropriate format
    data["schema"] = [
        int(day_delta) for day_delta in list(filter(None, data["schema"].split(" ")))
    ]

    return data


def prompt_schema_selection():
    """This function displays a menu prompting the user
    to select an existing rehearsal schema."""

    answer = inquirer.prompt(
        [
            inquirer.List(
                "selection",
                config["schema_selection_menu"]["message"],
                choices=storage_manager.fetch_schemas_descriptors(),
            )
        ]
    )

    return answer["selection"] if answer is not None else None


# -------------------------------------------------- MAIN APP -----------------------------------------------

continue_app = True  # Variable indicating whether we should stop the app or not

while continue_app:
    # Main menu
    main_menu_answer = inquirer.list_input(
        config["main_menu"]["message"],
        choices=[
            (config["main_menu"]["task_message"], MainMenuChoices.TASK),
            (config["main_menu"]["schema_message"], MainMenuChoices.SCHEMA),
            (config["main_menu"]["quit_message"], MainMenuChoices.QUIT),
        ],
    )

    # Task menu
    if main_menu_answer == MainMenuChoices.TASK:
        task_menu_answer = inquirer.list_input(
            config["task_menu"]["message"],
            choices=[
                (config["task_menu"]["creation_message"], TaskMenuChoices.CREATE),
                (config["task_menu"]["edition_message"], TaskMenuChoices.EDIT),
                (config["task_menu"]["deletion_message"], TaskMenuChoices.DELETE),
                (config["task_menu"]["quit_message"], TaskMenuChoices.QUIT),
            ],
        )

        # Task creation menu
        if task_menu_answer == TaskMenuChoices.CREATE:
            # Menu configuration and displaying
            task_data = prompt_task_data(priority=Priority.MEDIUM.value)

            # <None> means the user has skipped the prompt
            if task_data is not None:
                batch_create(
                    task_data["title"],
                    task_data["project_id"],
                    task_data["priority"],
                    task_data["schema_id"],
                )

        elif task_menu_answer == TaskMenuChoices.EDIT:
            if len(storage_manager.fetch_tasks_descriptors()) > 0:
                edited_task_rank = prompt_task_selection()  # Selection of the task

                if edited_task_rank is not None:
                    former_task_data = storage_manager.fetch_task_data(
                        edited_task_rank
                    )  # Current task

                    # We prompt the user for the updated information
                    new_task_data = prompt_task_data(
                        title=former_task_data["title"],
                        project_id=former_task_data["project_id"],
                        schema_id=former_task_data["schema_id"],
                        priority=former_task_data["priority"],
                    )

                    if new_task_data is not None:
                        # First, we have to delete the former tasks
                        batch_delete(edited_task_rank)

                        # Then we recreate the tasks
                        batch_create(
                            new_task_data["title"],
                            new_task_data["project_id"],
                            new_task_data["priority"],
                            new_task_data["schema_id"],
                        )

            else:
                print(Fore.RED + "Aucune tâche à éditer")

        elif task_menu_answer == TaskMenuChoices.DELETE:
            if len(storage_manager.fetch_tasks_descriptors()) > 0:
                # We prompt the user to select an existing task
                deleted_task_rank = prompt_task_selection()

                # We delete the task if the process has not been cancelled by the user
                if deleted_task_rank is not None and inquirer.confirm(
                    config["task_deletion_message"]
                ):
                    batch_delete(deleted_task_rank)

            else:
                print(Fore.RED + "Aucune tâche à supprimer")

    # Rehearsal schemas menu
    elif main_menu_answer == MainMenuChoices.SCHEMA:
        # Schema menu
        schema_menu_answer = inquirer.list_input(
            config["schema_menu"]["message"],
            choices=[
                (
                    config["schema_menu"]["creation_message"],
                    SchemaMenuChoices.CREATE,
                ),
                (
                    config["schema_menu"]["edition_message"],
                    SchemaMenuChoices.EDIT,
                ),
                (
                    config["schema_menu"]["deletion_message"],
                    SchemaMenuChoices.DELETE,
                ),
                (
                    config["schema_menu"]["quit_message"],
                    SchemaMenuChoices.QUIT,
                ),
            ],
        )

        if schema_menu_answer == SchemaMenuChoices.CREATE:
            # Schema creation menu
            new_schema_data = prompt_schema_data()

            if new_schema_data is not None:
                # We add the schema to the local database
                storage_manager.save_schema(
                    new_schema_data["name"], new_schema_data["schema"]
                )

                print(Fore.GREEN + "\nSchéma créé avec succès\n")

        elif schema_menu_answer == SchemaMenuChoices.EDIT:
            schema_rank = prompt_schema_selection()  # Schema selection menu

            if schema_rank is not None:
                former_schema_data = storage_manager.fetch_schema_data(schema_rank)

                # We prompt the user to type in the new data
                new_schema_data = prompt_schema_data(
                    former_schema_data["name"],
                    " ".join(
                        [str(day_delta) for day_delta in former_schema_data["schema"]]
                    ),
                )

                if new_schema_data is not None:
                    # We change the data stored in the local database
                    storage_manager.edit_schema(
                        schema_rank, new_schema_data["name"], new_schema_data["schema"]
                    )

                    print(Fore.GREEN + "\nSchéma édité avec succès\n")

        elif schema_menu_answer == SchemaMenuChoices.DELETE:
            # We prompt the user to select the schema he wants to delete
            deleted_schema_rank = prompt_schema_selection()

            # We delete the schema in the local database
            if deleted_schema_rank is not None and inquirer.confirm(
                config["schema_deletion_message"]
            ):
                storage_manager.delete_schema(deleted_schema_rank)

                print(Fore.GREEN + "\nSchéma édité avec succès\n")

    else:
        continue_app = False
