# SimpleDB

SimpleDB is a very basic file-based key-value store accessible over HTTP. It allows storing, retrieving, and deleting simple data values organized hierarchically using paths. There's a client library `simpledb` for easy usage.

## Features

*   **Key-Value Storage:** Store JSON-serializable values associated with unique keys (paths).
*   **Hierarchical Keys:** Organize keys into a folder-like structure (e.g., `users/alice/profile`).
*   **HTTP API:** Interact with the database using simple HTTP requests (GET, PUT, DELETE).
*   **Python Client Library:** A convenient Python client (`simpledb`) for easy interaction.
*   **History Tracking:** Maintains a history of changes for each key.
*   **Request Logging:** Logs all incoming requests with timestamp and user information.

## Installation

1.  **Clone the repository (if applicable):**
    ```bash
    git clone <repository_url>
    cd simpledb
    ```
2.  **Install dependencies:**
    Make sure you have Python installed. Then, install the required packages using pip:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Running the Server

Navigate to the project directory and run the webserver script:

```bash
python webserver.pyw
```

The server will start listening on `0.0.0.0:6924` by default and a system tray icon will appear. You can interact with the server using the client library or tools like `curl`.

### Using the Python Client (`simpledb`)

The `simpledb` library provides functions to interact with the running server.

```python
import simpledb

# Write a value
path = "greetings/hello"
value = {"message": "Hello from SimpleDB!"}
write_result = simpledb.write(path, value)
print(f"Wrote: {write_result}") # Prints the value that was set

# Read a value
read_result = simpledb.read(path)
print(f"Read: {read_result}") # Prints the value: {'message': 'Hello from SimpleDB!'}

# Read with metadata
read_meta_result = simpledb.read(path, include_metadata=True)
print(f"Read with metadata: {read_meta_result}")
# Prints {'value': {'message': 'Hello from SimpleDB!'}, 'created_at': '...', 'created_by': '...', ...}

# Write another value in the same 'folder'
simpledb.write("greetings/howdy", "partner")

# Read the 'greetings' folder
folder_content = simpledb.read("greetings")
print(f"Folder content: {folder_content}")
# Prints {'hello': {'message': 'Hello from SimpleDB!'}, 'howdy': 'partner'}

# Delete a value
deleted_value = simpledb.delete_value(path)
print(f"Deleted value: {deleted_value}") # Prints the deleted value, along with metadata

# Delete the folder
deleted_folder = simpledb.delete_folder("greetings")
print(f"Deleted folder contents: {deleted_folder}") # Prints the content of the deleted folder

# Reading a non-existent or deleted key returns None
non_existent = simpledb.read("greetings")
print(f"Non-existent key: {non_existent}") # Prints None
```

If you store a folder and a value with the same path (e.g., `users/alice` and `users/alice/profile`).
If you try to read the value from `users/alice`, it will return the value from the file.
To get the value from the folder, add a `/` to the end of the path (`users/alice/`). This is not required if you don't have any duplicate names

### Data Storage

*   Values are stored as JSON files in the `data_storage/` directory, mirroring the key structure.
*   Write history is stored in the `history_storage/` directory.
*   Server requests are logged in `requests.log`.

## API Endpoints

*   `GET /read/<path:path>`: Reads the value or folder contents at the given path.
*   `PUT /write/<path:path>`: Writes a value to the given path. Expects JSON payload `{"value": ...}`.
*   `DELETE /delete_value/<path:path>`: Deletes the value (file) at the given path.
*   `DELETE /delete_folder/<path:path>`: Deletes the folder (and its contents) at the given path.

## Configuration

*   **Server Address:** The client library defaults to `http://192.168.1.168:6924`. You can change this using `simpledb.set_base_url("http://your_server_ip:6924")`.
*   **User Mapping:** The server (`webserver.pyw`) contains an `IP_TO_NAME` dictionary to map request IP addresses to usernames for logging purposes.
