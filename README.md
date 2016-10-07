## What is this?
- In-memory tree manager (tree-as-a-service)
- Supports multiple trees
- Supports standard CRUD operations
- Uses materialised path for faster lookups
- Runs as a dockerised service with a basic API
- Can run in managed (node IDs are provided by the caller) or unmanaged mode (node IDs are auto-generated)
- Tree structure is similar to doubly-linked lists, which allows us to use one level for all nodes (faster lookups!)

## How does it work?
- Program init loads tree from disk and does tree corruption analysis
- Where is the tree file? It is mounted as a volume (see docker-compose.yml)
- Everything runs in memory, we keep the whole tree for everything in memory at all times
- Internal cron saves tree to disk every N minutes
- Backups should be taken care of in the host environment

## What about atomicity issues?
- If you hold the whole structure in this app, there should be no problems
- If you use a "managed" mode, where you supply the node IDs (based on a parent application) you may have issues
- We use event sourcing (with client UTC timestamps) to rollback, and apply prior actions that were received later

## Getting started
- Clone this repository
- Make sure you have Docker (and docker-compose) installed
- Create an empty data file (touch datafile)
- Create an empty log file (touch log)
- Copy config.ini.dist (cp config.ini.dist config.ini)
- Fill in the variables (e.g. 'datafile' and 'log')
- Make sure docker-compose.yml mounts the three files as volumes (config, datafile and log)
- Run this to start in local debugging mode: ./restart-dev.sh (debugging)

## Running the tests
- Get the hash of the container (docker ps -a)
- Run: docker exec -it {hash} bash
- Run: cd /app && python app/test.py

## Todos
- Sorting using array and not a separate "sort"
- Several tree operations (marked as TODO below)

## Data Structure
- {tree_id: {segment_id: {node_id: (parent_node_id, type, payload (e.g. fileId), sort, [children_node_ids])}}}

## What structure will the API return?
```
{
    tree_id: 
    {
        segment_id: 
        {
            "id": node_id (or root node_id),
            "type": type,
            "data": payload_link_id,
            "sort": 1,
            "children": [
                {
                    "id": node_id,
                    "type": type,
                    ...
                },
                {item},
                {item},...
            ]
        }
    }
}
```

## What is tree_id and segment_id?
- These allow us to host multiple trees under one roof
- Imagine you have an application for multiple users, and each user can have multiple hierarchical structures
- The tree_id might be the user_id (or client_id) from your parent application
- The segment_id would be each tree container for the user, so the user could have multiple trees
- Imagine you are building a Dropbox clone, where users can have multiple directories in different parts of the FS
- In that case, tree_id would be the user's ID, and each independent "dropbox" would be a different segment_id
- Inside the segment you will have a full tree structure

## Help! I just want one tree!
- curl -X POST localhost:8080/tree -d '{"tree_id": 1}'
- curl -X POST localhost:8080/tree/1/segment -d '{"segment_id": 1, "root_node_id": 1}'
- If you are running in unmanaged mode, you don't have to supply segment_id nor root_node_id (result = ID)
- Don't forget to use application/json for those calls! (-H "Content-Type: application/json")
- Now you can start adding nodes (see sample operations below)

## What types of nodes exist?
- root
- dir
- asset|file|anything

## Sample operations (using CURL)

### Generic operations
- Clear the tree: curl -X POST localhost:8080/clear -H "Content-Type: application/json"
- Persist the tree to the filesystem: curl -X POST localhost:8080/persist

### Trees
- Create a tree: curl -X POST localhost:8080/tree -H "Content-Type: application/json" -d '{"tree_id": 1}'
- Delete a tree: curl -X DELETE localhost:8080/tree -H "Content-Type: application/json" -d '{"tree_id": 1}'
- Get a list of trees: curl -X GET localhost:8080/trees

### Segments
- Get a list of segments for a tree: curl "localhost:8080/tree/{ID}/segments"
- Create a segment: curl -X POST localhost:8080/tree/{ID}/segment -H "Content-Type: application/json" -d '{"segment_id": 1, "root_node_id": 1}'
- Delete a segment: curl -X DELETE localhost:8080/tree/{ID}/segment/{ID}
- Get the root node of a segment: curl "localhost:8080/tree/{ID}/segment/{ID}/root"
- Duplicate a whole segment: (TODO)

### Retrieval
- Get a level: curl -X GET localhost:8080/tree/{ID}/segment/{ID}/level/{PARENT_NODE_ID}
- Whole tree: curl -X GET localhost:8080/tree (TODO)

### Directory operations
- Create a directory: curl -X POST localhost:8080/tree/{ID}/segment/{ID}/directory -H "Content-Type: application/json" -d '{"parent_node_id": 1, "node_id": 1, "position": 5}' # Optional: position
- Delete a directory: curl -X DELETE localhost:8080/tree/{ID}/segment/{ID}/directory/{ID}
- Duplicate a directory: (TODO)
- Move a directory: (TODO)

### Node Operations
