"""This file contains the definition of the <StorageManager> class,
which manages the local database"""

import json
import sqlite3


class StorageManager:
    DATABASE_PATH = "./data.db"

    def __init__(self):
        """Creates the connection to the local database and the various tables
        (those are created only if they are missing)"""

        # Those lines establish the connection to the database
        self.db_connection = sqlite3.connect(StorageManager.DATABASE_PATH)
        self.db_cursor = self.db_connection.cursor()

        # Here we create the two tables we need : <tasks> and <schemas>
        self.db_cursor.execute(
            """CREATE TABLE IF NOT EXISTS schemas(
                               id INTEGER PRIMARY KEY AUTOINCREMENT,
                               name TEXT NOT NULL UNIQUE,
                               schema TEXT NOT NULL
        )"""
        )

        self.db_cursor.execute(
            """CREATE TABLE IF NOT EXISTS tasks(
                               id INTEGER PRIMARY KEY AUTOINCREMENT,
                               schema_id INTEGER,
                               title TEXT NOT NULL,
                               project_id TEXT NOT NULL,
                               priority INTEGER NOT NULL,
                               rehearsals_ids TEXT NOT NULL,
                               FOREIGN KEY (schema_id)
                                    REFERENCES schema (id)
                                        ON DELETE CASCADE
                                        ON UPDATE NO ACTION
        )"""
        )

    def fetch_schemas_descriptors(self):
        """Returns a list of tuples of the form (name, id), each one
        corresponding to an existing rehearsal schema"""
        return self.db_cursor.execute(
            "SELECT name, id FROM schemas ORDER BY id"
        ).fetchall()

    def fetch_schema_data(self, schema_id):
        """Returns the data associated with a single schema, its ID being given"""

        # We first retrieve the raw data from the local database
        raw_data = self.db_cursor.execute(
            "SELECT * FROM schemas WHERE id = ?", (schema_id,)
        ).fetchone()

        # We return the data under the form of a dictionary
        return {
            "id": raw_data[0],
            "name": raw_data[1],
            "schema": json.loads(raw_data[2]),
        }

    def save_schema(self, name, schema):
        """Inserts a rehearsal schema into the local database"""

        # We create and commit the appropriate transaction
        self.db_cursor.execute(
            """INSERT INTO schemas (name, schema) VALUES (?, ?)""",
            (name, json.dumps(schema)),
        )

        self.db_connection.commit()

    def edit_schema(self, schema_id, name, schema):
        """Edits an existing rehearsal schema in the local database"""

        # We create and commit the appropriate transaction
        self.db_cursor.execute(
            """UPDATE schemas SET name = ?, schema = ? WHERE id = ?""",
            (name, json.dumps(schema), schema_id),
        )

        self.db_connection.commit()

    def delete_schema(self, schema_id):
        """Deletes an existing rehearsal schema from the local database"""

        # We create and commit the appropriate transaction
        self.db_cursor.execute("""DELETE FROM schemas WHERE id = ?""", (schema_id,))

        self.db_connection.commit()

    def fetch_tasks_descriptors(self):
        """Returns a list of tuples of the form (title, id), each one
        corresponding to an existing task"""
        return self.db_cursor.execute(
            "SELECT title, id FROM tasks ORDER BY id DESC"
        ).fetchall()

    def fetch_task_data(self, task_local_id):
        """Returns the data of a single task, its local ID being given"""

        # We first retrieve the raw data from the local database
        raw_data = self.db_cursor.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_local_id,)
        ).fetchone()

        # We return the data under the form of a dictionary
        return {
            "id": raw_data[0],
            "schema_id": raw_data[1],
            "title": raw_data[2],
            "project_id": raw_data[3],
            "priority": raw_data[4],
            "rehearsal_ids": json.loads(raw_data[5]),
        }

    def save_task(self, schema_id, title, project_ID, priority, rehearsal_IDs):
        """Inserts a single task into the local database"""

        # We create and commit the appropriate transaction
        self.db_cursor.execute(
            """INSERT INTO tasks (schema_id, title, project_id, priority, rehearsals_ids) VALUES (?, ?, ?, ?, ?)""",
            (schema_id, title, project_ID, priority, json.dumps(rehearsal_IDs)),
        )

        self.db_connection.commit()

    def delete_task(self, task_local_id):
        """Deletes a single task from local database"""

        # We create and commit the appropriate transaction
        self.db_cursor.execute("""DELETE FROM tasks WHERE id = ?""", (task_local_id,))

        self.db_connection.commit()

    def __del__(self):
        """Cancels the connection to the local database"""
        self.db_connection.close()
