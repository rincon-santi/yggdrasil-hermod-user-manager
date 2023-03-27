Yggdrasil Hermod User Manager
=============================

This repository contains the Yggdrasil Hermod User Manager application, which is responsible for managing and organizing user data in the Prompting as a Service application.

Getting Started
---------------

To run the Yggdrasil Hermod User Manager locally, you will need Python 3.10.

Clone the repository:

```bash
git clone https://github.com/<username>/yggdrasil-hermod-user-manager.git
cd yggdrasil-hermod-user-manager
```

Install the required Python packages using pip:

```bash
pip install -r user_commands/requirements.txt
pip install -r user_event_manager/requirements.txt
```

To run the user commands API, execute the following command:

```bash
functions-framework --target=user_commands
```

To run the user event manager API, execute the following command:

```bash
functions-framework --target=user_event_manager
```

Project Structure
-----------------

The repository contains the following directories and files:

- **user_commands/**: Contains the implementation for executing user commands.
  - **commands.json**: Defines the available commands for the application.
  - **main.py**: Implements the Flask server and Pub/Sub message publisher for user commands.
  - **requirements.txt**: Contains the required Python packages for running user commands.
- **user_event_manager/** */: Contains the implementation for managing user events.
  - **main.py**: Implements the Pub/Sub subscriber and Firestore/GCS data storage for user event management.
  - **operations.json**: Defines the required payload for user event management.
  - **requirements.txt**: Contains the required Python packages for running user event management.
- **.gitignore**: Specifies which files should be ignored by Git.
- **cloudbuild.yaml**: Provides the configuration for building and deploying the Yggdrasil Hermod User Manager to Google Cloud.
- **LICENSE**: Specifies the license for the project.
- **upload_commands.py**: Uploads the commands JSON file to Firestore.

Access Control
--------------

Access control for users is crucial for ensuring data privacy and security in the Prompting as a Service application. The Yggdrasil Hermod User Manager application implements the following access control measures:

- **User-Specific Access**: Each user can only access their own data stored in Firebase. This is achieved by using a unique identifier, such as the user's ID (user_id), to restrict access to the user data.

- **Firebase Security Rules**: Access control is enforced using Firebase Security Rules, which can be configured to grant or deny access to data stored in the Firebase database. These rules can be customized to allow or deny access based on a user's unique identifier (such as user_id) and their role or relationship to the data being accessed.

- **Authentication**: Users are required to authenticate themselves using a secure method (such as email/password or a third-party authentication provider) before they can access the application and its data. This authentication process ensures that only authorized users can access their own data.

License
-------

This project is licensed under the terms of the GPL-3 license. See the [LICENSE](./LICENSE) file for more information.
