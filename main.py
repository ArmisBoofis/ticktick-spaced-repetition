"""Main file of the app. This file contains the authentication process
and the main features."""

import json
import re
from datetime import *
from enum import Enum

import inquirer
from colorama import Fore, init
from ticktick.api import TickTickClient
from ticktick.oauth2 import OAuth2

init(autoreset=True)  # Initialization for colorama

# -------------------------------------------------- CONSTANTS --------------------------------------------------

# App credentials
APP_ID = "YmQWg8OkoiEe63456Y"
APP_SECRET = "W(L#T@3Bv3O(D5ka!&cZ9ggS3&#B4!Pf"
APP_URI = "http://127.0.0.1:8080"

# Account credentials
USERNAME = "armand.malinvaud@icloud.com"
PASSWORD = "2DB2y\eW~@8QHY>F"

# ID of the group gathering all the interesting task lists
GINETTE_GROUP_ID = "62b4b7cdaa2a9e4c9aa9fdf5"

# Path to the JSON files used by the application
DATA_FILE_PATH = "./data.json"
CONFIG_FILE_PATH = "./config.json"

# Authentication process
auth_client = OAuth2(client_id=APP_ID, client_secret=APP_SECRET, redirect_uri=APP_URI)
client = TickTickClient(USERNAME, PASSWORD, auth_client)

# Parsing local data and configuration
with open(DATA_FILE_PATH, encoding="utf8") as file:
    local_data = json.load(file)

with open(CONFIG_FILE_PATH, encoding="utf8") as file:
    config = json.load(file)

# -------------------------------------------------- UTILITY FUNCTIONS --------------------------------------


def refresh_storage():
    """This function dumps the data object to the local storage file"""

    with open(DATA_FILE_PATH, "w", encoding="utf8") as file:
        json.dump(local_data, file, ensure_ascii=False)


def batch_create(title, project_ID, priority, schema):
    """This function creates multiple tasks according to a rehearsal schema, and
    stores them both online and locally."""

    print(Fore.YELLOW + "Création de la tâche...")

    # We create the different tasks, and we store their dicts in the JSON file
    created_tasks = []

    for day_delta in schema:
        # We create the task corresponding to this time interval
        created_tasks.append(
            client.task.create(
                client.task.builder(
                    title=title,
                    projectId=project_ID,
                    startDate=(
                        datetime.combine(date.today(), time())
                        + timedelta(days=day_delta)
                    ),
                    priority=priority,
                    allDay=True,
                )
            )
        )

    # We change the <local_data> object...
    local_data["tasks"].append(
        {
            "title": title,
            "project_ID": project_ID,
            "schema": schema,
            "priority": priority,
            "tasks_dicts": created_tasks,
        }
    )

    refresh_storage()  # ...and store it to the local JSON file

    print(Fore.GREEN + "Tâche créée avec succès\n")


def batch_delete(task_rank):
    """This function deletes a task that has been repeated
    following a rehearsal schema"""

    print(Fore.YELLOW + "Suppression de la tâche...")

    # Deletion on TickTick
    client.task.delete(local_data["tasks"][task_rank]["tasks_dicts"])

    # Local deletion
    local_data["tasks"].pop(task_rank)
    refresh_storage()

    print(Fore.GREEN + "Tâche supprimée avec succès\n")


# -------------------------------------------------- MENUS --------------------------------------------------

# Enumerations for the menus
MainMenuChoices = Enum("MainMenuChoices", ["TASK", "SCHEMA", "QUIT"])
TaskMenuChoices = Enum("TaskMenuChoices", ["CREATE", "EDIT", "DELETE", "QUIT"])
SchemaMenuChoices = Enum("SchemaMenuChoices", ["CREATE", "EDIT", "DELETE", "QUIT"])
Priority = Enum(
    "Priority", [("NO_PRIORITY", 0), ("LOW", 1), ("MEDIUM", 3), ("HIGH", 5)]
)


def prompt_task_data(title=None, project_ID=None, schema=None, priority=None):
    """This function displays a menu prompting the user for all the information needed
    to create or edit a task. The arguments define default values."""

    return inquirer.prompt(
        [
            inquirer.Text(
                "title", config["task_creation_menu"]["title_message"], title
            ),
            inquirer.List(
                "project_ID",
                config["task_creation_menu"]["project_message"],
                list(
                    map(
                        lambda project: (project["name"], project["id"]),
                        filter(
                            lambda project: project["groupId"] == GINETTE_GROUP_ID,
                            client.state["projects"],
                        ),
                    )
                ),
                project_ID,
            ),
            inquirer.List(
                "schema",
                config["task_creation_menu"]["schema_message"],
                list(
                    map(
                        lambda schema: (schema["name"], schema["schema"]),
                        local_data["schemas"],
                    )
                ),
                schema,
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
                choices=[
                    (task["title"], k) for k, task in enumerate(local_data["tasks"])
                ],
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
                choices=[
                    (schema["name"], k)
                    for k, schema in enumerate(local_data["schemas"])
                ],
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
                    task_data["project_ID"],
                    task_data["priority"],
                    task_data["schema"],
                )

        elif task_menu_answer == TaskMenuChoices.EDIT:
            if len(local_data["tasks"]) > 0:
                edited_task_rank = prompt_task_selection()  # Selection of the task

                if edited_task_rank is not None:
                    former_task_data = local_data["tasks"][
                        edited_task_rank
                    ]  # Current task

                    # We prompt the user for the updated information
                    new_task_data = prompt_task_data(
                        title=former_task_data["title"],
                        project_ID=former_task_data["project_ID"],
                        schema=former_task_data["schema"],
                        priority=former_task_data["priority"],
                    )

                    if new_task_data is not None:
                        # First, we have to delete the former tasks
                        batch_delete(edited_task_rank)

                        # Then we recreate the tasks
                        batch_create(
                            new_task_data["title"],
                            new_task_data["project_ID"],
                            new_task_data["priority"],
                            new_task_data["schema"],
                        )

            else:
                print(Fore.RED + "Aucune tâche à éditer")

        elif task_menu_answer == TaskMenuChoices.DELETE:
            if len(local_data["tasks"]) > 0:
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
                # We change the <local_data> object first and then refresh the file
                local_data["schemas"].append(new_schema_data)
                refresh_storage()

        elif schema_menu_answer == SchemaMenuChoices.EDIT:
            schema_rank = prompt_schema_selection()  # Schema selection menu

            if schema_rank is not None:
                former_schema_data = local_data["schemas"][schema_rank]

                # We prompt the user to type in the new data
                new_schema_data = prompt_schema_data(
                    former_schema_data["name"],
                    " ".join(
                        [str(day_delta) for day_delta in former_schema_data["schema"]]
                    ),
                )

                if new_schema_data is not None:
                    # We change the <local_data> object first and then refresh the file
                    local_data["schemas"][schema_rank] = new_schema_data
                    refresh_storage()

        elif schema_menu_answer == SchemaMenuChoices.DELETE:
            # We prompt the user to select the schema he wants to delete
            deleted_schema_rank = prompt_schema_selection()

            # We delete the schema in the <local_data> object and then refresh the file
            if deleted_schema_rank is not None and inquirer.confirm(
                config["schema_deletion_message"]
            ):
                local_data["schemas"].pop()
                refresh_storage()

    else:
        continue_app = False
