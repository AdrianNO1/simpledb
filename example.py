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