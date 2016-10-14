# Standard libraries
import time
import logging
import ConfigParser
import sys
import os
import os.path
import json
import pickle
import ConfigParser

# Libraries
from epictree import *

# External libraries
from flask import Flask, jsonify, request
from flask.ext.cors import CORS
from flask_limiter import Limiter
import tornado.web
import tornado.autoreload
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.log import enable_pretty_logging

# Set up Flask/Tornado
app = Flask(__name__)
app.debug = True
CORS(app)
limiter = Limiter(app)
epicTree = None

# Read configuration file
config = ConfigParser.ConfigParser()
config.read('config.ini')
environment = config.get('Server', 'Environment')
if environment is None or environment == '':
    environment = 'production'

# Set up logging
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
if environment == 'production':
    logger.setLevel(logging.ERROR)

# region Trees

@app.route('/tree', methods=['POST', 'DELETE'])
@limiter.limit("1000/hour")
def tree():
    # Get variables
    content = request.json
    if content is None:
        return make_error('JSON body not sent', 400)
    # TODO: Use <int:tree_id> as url param for delete + update README.md
    if 'tree_id' not in content:
        return make_error('Tree ID (tree_id) not sent (or incorrect format)', 400)
    tree_id = int(content['tree_id'])
    # Execute tree operation
    try:
        if request.method == 'POST':
            epicTree.add_tree(tree_id)
            return success(True)
        elif request.method == 'DELETE':
            epicTree.remove_tree(tree_id)
            return success(True)
    except KeyError as inst:
        if request.method == 'DELETE':
            return error_not_found(inst)
        return make_error(inst, 409)
    except Exception as inst:
        return make_error(inst, 409)

@app.route('/trees', methods=['GET'])
@limiter.limit("10000/hour")
def trees():
    try:
        return success(epicTree.get_trees())
    except Exception as inst:
        return make_error(inst, 500)

# endregion

# region Segments

@app.route('/tree/<int:tree_id>/segments', methods=['GET'])
@limiter.limit("50000/hour")
def segments(tree_id):
    # Get variables
    if tree_id is None:
        return make_error('Tree Id not sent (or incorrect format)', 400)
    try:
        return success(epicTree.get_segments(int(tree_id)))
    except KeyError as inst:
        return error_not_found(inst)
    except Exception as inst:
        return make_error(inst, 500)

@app.route('/tree/<int:tree_id>/segment', methods=['POST'])
@limiter.limit("20000/hour")
def segment_create(tree_id):
    # Validate
    if tree_id is None:
        return make_error('Tree Id not sent (or incorrect format)', 400)
    # Get variables
    content = request.json
    if content is None:
        return make_error('JSON body not sent', 400)
    if 'segment_id' not in content:
        return make_error('Segment Id (segment_id) not sent (or incorrect format)', 400)
    segment_id = int(content['segment_id'])
    # Validate tree exists
    if tree_id not in epicTree.tree:
        return error_not_found('Tree ' + str(tree_id) + ' not found')
    # Execute tree operation
    try:
        if 'root_node_id' not in content or not str(content['root_node_id']).isdigit():
            return make_error('Root Node Id (root_node_id) not sent (or incorrect format)', 400)
        elif segment_id in epicTree.tree[tree_id]:
            return make_error('Segment ' + str(segment_id) + ' already exists for tree ' + str(tree_id), 409)
        root_node_id = content['root_node_id']
        epicTree.add_segment(tree_id, segment_id, root_node_id)
        return success(True)
    except KeyError as inst:
        return make_error(inst, 409)
    except Exception as inst:
        return make_error(inst, 500)

@app.route('/tree/<int:tree_id>/segment/<int:segment_id>', methods=['DELETE'])
@limiter.limit("20000/hour")
def segment_remove(tree_id, segment_id):
    # Validate
    if tree_id is None:
        return make_error('Tree Id not sent (or incorrect format)', 400)
    if segment_id is None:
        return make_error('Segment Id not sent (or incorrect format)', 400)
    # Validate tree exists
    if tree_id not in epicTree.tree:
        return error_not_found('Tree ' + str(tree_id) + ' not found')
    # Validate segment exists
    if segment_id not in epicTree.tree[tree_id]:
        return error_not_found('Segment ' + str(segment_id) + ' not found')
    # Execute tree operation
    try:
        epicTree.remove_segment(tree_id, segment_id)
        return success(True)
    except KeyError as inst:
        return error_not_found(inst)
    except Exception as inst:
        return make_error(inst, 500)

@app.route('/tree<int:tree_id>/segment/<int:segment_id>/duplicate', methods=['POST', 'PUT'])
@limiter.limit("10000/hour")
def profile_duplicate(tree_id, segment_id):
    # epicTree.duplicate_segment(tree_id, from_segment_id, to_segment_id, segment_structure):
    # to_segment_id and segment_struture should be POST input, segment_structure = dict/tree
    return make_error('not implemented', 400)

@app.route('/tree/<int:tree_id>/segment/<int:segment_id>/root', methods=['GET'])
@limiter.limit("10000/hour")
def nodes_root(tree_id, segment_id):
    # Get variables
    if tree_id is None:
        return make_error('Tree Id not sent (or incorrect format)', 400)
    if segment_id is None:
        return make_error('Segment Id not sent (or incorrect format)', 400)
    # Validate tree exists
    if tree_id not in epicTree.tree:
        return error_not_found('Tree ' + str(tree_id) + ' not found')
    # Validate segment exists
    if segment_id not in epicTree.tree[tree_id]:
        return error_not_found('Segment ' + str(segment_id) + ' not found')
    try:
        root_node_id = epicTree.get_segment_root_node(tree_id, segment_id)
        return success(root_node_id)
    except KeyError as inst:
        return error_not_found(inst)
    except Exception as inst:
        return make_error(inst, 500)

# endregion

# region Retrieval and Search

@app.route('/tree/<int:tree_id>/segment/<int:segment_id>/level/<int:parent_node_id>', methods=['GET'])
@limiter.limit("100000/hour")
def get_level(tree_id, segment_id, parent_node_id):
    # Get variables
    if tree_id is None:
        return make_error('Tree Id not sent (or incorrect format)', 400)
    if segment_id is None:
        return make_error('Segment Id not sent (or incorrect format)', 400)
    # Validate tree exists
    if tree_id not in epicTree.tree:
        return error_not_found('Tree ' + str(tree_id) + ' not found')
    # Validate segment exists
    if segment_id not in epicTree.tree[tree_id]:
        return error_not_found('Segment ' + str(segment_id) + ' not found')
    # Validate parent node exists
    if parent_node_id not in epicTree.tree[tree_id][segment_id]:
        return error_not_found('Parent node ' + str(parent_node_id) + ' not found')
    try:
        children = epicTree.get_level(tree_id, segment_id, parent_node_id)
        results = []
        for child_dict in children:
            child_id = child_dict['id']
            child = child_dict['child']
            result = make_simple_node(child_id, child)
            results.append(result)
        return success(results)
    except KeyError as inst:
        return error_not_found(inst)
    except Exception as inst:
        return make_error(inst, 500)

@app.route('/tree/<int:tree_id>/segment/<int:segment_id>/breadcrumbs/<int:node_id>', methods=['GET'])
@limiter.limit("100000/hour")
def breadcrumbs(tree_id, segment_id, node_id):
    # Get variables
    if tree_id is None:
        return make_error('Tree Id not sent (or incorrect format)', 400)
    if segment_id is None:
        return make_error('Segment Id not sent (or incorrect format)', 400)
    if node_id is None:
        return make_error('Node Id not sent (or incorrect format)', 400)
    # Validate tree exists
    if tree_id not in epicTree.tree:
        return error_not_found('Tree ' + str(tree_id) + ' not found')
    # Validate segment exists
    if segment_id not in epicTree.tree[tree_id]:
        return error_not_found('Segment ' + str(segment_id) + ' not found')
    # Validate node exists
    if node_id not in epicTree.tree[tree_id][segment_id]:
        return error_not_found('Node ' + str(node_id) + ' not found')
    try:
        crumbs = epicTree.get_breadcrumbs(tree_id, segment_id, node_id)
        return success(crumbs)
    except KeyError as inst:
        return error_not_found(inst)
    except Exception as inst:
        return make_error(inst, 500)

@app.route('/tree/<int:tree_id>/segment/<int:segment_id>', methods=['GET'])
@limiter.limit("50000/hour")
def segment_get(tree_id, segment_id):
    # GET TREE (for a segment)
    # TODO
    return make_error('not implemented ' + str(segment_id), 400)

@app.route('/tree/<int:tree_id>', methods=['GET'])
@limiter.limit("40000/hour")
def tree_get(tree_id):
    # GET TREE (for a full tree ID)
    # TODO
    return make_error('not implemented ' + str(tree_id), 400)

@app.route('/tree', methods=['GET'])
@limiter.limit("200000/hour")
def get_tree():
    # Get full tree as a JSON representation (for debugging only)
    # TODO
    return success(epicTree.get_everything())

# endregion

# region Directories

@app.route('/tree/<int:tree_id>/segment/<int:segment_id>/directory', methods=['POST'])
@limiter.limit("100000/hour")
def directory_add(tree_id, segment_id):
    # Validate
    if tree_id is None:
        return make_error('Tree Id not sent (or incorrect format)', 400)
    if segment_id is None:
        return make_error('Segment Id not sent (or incorrect format)', 400)
    # Get variables
    content = request.json
    if content is None:
        return make_error('JSON body not sent', 400)
    if 'parent_node_id' not in content:
        return make_error('Parent Node Id (parent_node_id) not sent (or incorrect format)', 400)
    parent_node_id = int(content['parent_node_id'])
    if 'node_id' not in content:
        return make_error('Node Id (parent_node_id) not sent (or incorrect format)', 400)
    node_id = int(content['node_id'])
    position = None
    if 'position' in content:
        position = int(content['position'])
        if position < 1:
            return make_error('Position can\'t be less than 1', 400)
    # Validate tree exists
    if tree_id not in epicTree.tree:
        return error_not_found('Tree ' + str(tree_id) + ' not found')
    # Validate segment exists
    if segment_id not in epicTree.tree[tree_id]:
        return error_not_found('Segment ' + str(segment_id) + ' not found')
    # Validate parent exists
    if parent_node_id not in epicTree.tree[tree_id][segment_id]:
        return error_not_found('Parent Node ' + str(node_id) + ' not found')
    # Validate directory does not exist
    if node_id in epicTree.tree[tree_id][segment_id]:
        return error_not_found('An item with Node Id ' + str(node_id) + ' already exists')
    # Execute tree operation
    try:
        epicTree.add_directory(tree_id, segment_id, parent_node_id, node_id, position, None)
        return success(True)
    except KeyError as inst:
        return make_error(inst, 409)
    except Exception as inst:
        return make_error(inst, 500)

@app.route('/tree/<int:tree_id>/segment/<int:segment_id>/directory/<int:node_id>', methods=['DELETE'])
@limiter.limit("20000/hour")
def directory_remove(tree_id, segment_id, node_id):
    # Validate input
    if tree_id is None:
        return make_error('Tree Id not sent (or incorrect format)', 400)
    if segment_id is None:
        return make_error('Segment Id not sent (or incorrect format)', 400)
    if node_id is None:
        return make_error('Directory Id (node_id) not sent (or incorrect format)', 400)
    # Validate tree exists
    if tree_id not in epicTree.tree:
        return error_not_found('Tree ' + str(tree_id) + ' not found')
    # Validate segment exists
    if segment_id not in epicTree.tree[tree_id]:
        return error_not_found('Segment ' + str(segment_id) + ' not found')
    # Validate directory exists
    if node_id not in epicTree.tree[tree_id][segment_id]:
        return error_not_found('Directory ' + str(node_id) + ' not found')
    # Execute tree operation
    try:
        epicTree.remove_directory(tree_id, segment_id, node_id)
        return success(True)
    except KeyError as inst:
        return error_not_found(inst)
    except Exception as inst:
        return make_error(inst, 500)

@app.route('/tree/<int:tree_id>/segment/<int:segment_id>/directory/<int:directory_id>/duplicate', methods=['POST', 'PUT'])
@limiter.limit("2000/hour")
def directory_duplicate(tree_id, segment_id, directory_id):
    # TODO: Implement
    return make_error('not implemented', 400)

@app.route('/tree/<int:tree_id>/segment/<int:segment_id>/directory/<int:directory_id>/move', methods=['POST', 'PUT'])
@limiter.limit("10000/hour")
def directory_move(tree_id, segment_id, directory_id):
    # TODO: Implement
    return make_error('not implemented', 400)

# endregion

# region Nodes

@app.route('/tree/<int:tree_id>/segment/<int:segment_id>/node', methods=['POST'])
@limiter.limit("200000/hour")
def node_add(tree_id, segment_id):
    # Validate
    if tree_id is None:
        return make_error('Tree Id not sent (or incorrect format)', 400)
    if segment_id is None:
        return make_error('Segment Id not sent (or incorrect format)', 400)
    # Get variables
    content = request.json
    if content is None:
        return make_error('JSON body not sent', 400)
    if 'parent_node_id' not in content:
        return make_error('Parent Node Id (parent_node_id) not sent (or incorrect format)', 400)
    parent_node_id = int(content['parent_node_id'])
    if 'node_id' not in content:
        return make_error('Node Id (parent_node_id) not sent (or incorrect format)', 400)
    node_id = int(content['node_id'])
    position = None
    if 'position' in content:
        position = int(content['position'])
        if position < 1:
            return make_error('Position can\'t be less than 1', 400)
    if 'type' not in content:
        return make_error('Node Type (type) not sent (or incorrect format)', 400)
    node_type = content['type']
    if node_type == 'dir' or node_type == 'root':
        return make_error('Node Type can\'t be root or dir, use the other endpoints to create these types', 400)
    if 'payload' not in content:
        return make_error('Payload (payload) not sent (or incorrect format)', 400)
    payload = content['payload']
    # Validate tree exists
    if tree_id not in epicTree.tree:
        return error_not_found('Tree ' + str(tree_id) + ' not found')
    # Validate segment exists
    if segment_id not in epicTree.tree[tree_id]:
        return error_not_found('Segment ' + str(segment_id) + ' not found')
    # Validate parent exists
    if parent_node_id not in epicTree.tree[tree_id][segment_id]:
        return error_not_found('Parent Node ' + str(node_id) + ' not found')
    # Validate node does not exist
    if node_id in epicTree.tree[tree_id][segment_id]:
        return error_not_found('Node with Id ' + str(node_id) + ' already exists')
    # Execute tree operation
    try:
        epicTree.add_node(tree_id, segment_id, parent_node_id, node_id, position, None, node_type, payload)
        return success(True)
    except KeyError as inst:
        return make_error(inst, 409)
    except Exception as inst:
        return make_error(inst, 500)

@app.route('/tree/<int:tree_id>/segment/<int:segment_id>/node/<int:node_id>', methods=['DELETE'])
@limiter.limit("100000/hour")
def node_delete(tree_id, segment_id, node_id):
    # Validate input
    if tree_id is None:
        return make_error('Tree Id not sent (or incorrect format)', 400)
    if segment_id is None:
        return make_error('Segment Id not sent (or incorrect format)', 400)
    if node_id is None:
        return make_error('Node Id (node_id) not sent (or incorrect format)', 400)
    # Validate tree exists
    if tree_id not in epicTree.tree:
        return error_not_found('Tree ' + str(tree_id) + ' not found')
    # Validate segment exists
    if segment_id not in epicTree.tree[tree_id]:
        return error_not_found('Segment ' + str(segment_id) + ' not found')
    # Validate directory exists
    if node_id not in epicTree.tree[tree_id][segment_id]:
        return error_not_found('Node ' + str(node_id) + ' not found')
    # Execute tree operation
    try:
        epicTree.remove_node(tree_id, segment_id, node_id)
        return success(True)
    except KeyError as inst:
        return error_not_found(inst)
    except Exception as inst:
        return make_error(inst, 500)

@app.route('/tree/<int:tree_id>/segment/<int:segment_id>/node/<int:node_id>/move', methods=['POST', 'PUT'])
@limiter.limit("50000/hour")
def node_move(tree_id, segment_id, node_id):
    # TODO
    return make_error('not implemented', 400)

@app.route('/tree/<int:tree_id>/segment/<int:segment_id>/level/<int:parent_node_id>', methods=['POST'])
@limiter.limit("5000/hour")
def level_add(tree_id, segment_id, parent_node_id):
    # TODO
    return make_error('not implemented', 400)

# endregion

# region Generic, Persist and Cleanup

@app.route('/clear', methods=['POST'])
@limiter.limit("20/hour")
def clear_everything():
    try:
        epicTree.clear_everything()
        return success(True)
    except Exception as inst:
        return make_error(inst, 500)

@app.route('/persist', methods=['POST'])
@limiter.limit("5000/hour")
def persist_tree():
    """Public method to persist the tree, can be made private if not called externally.
    The inspiration for this was to call this through cron or something to persist the tree"""
    # Get variables
    data_filename = config.get('Files', 'DataFile')
    content = request.json
    if content is not None and 'filename' in content:
        data_filename = content['filename']
    try:
        pickle.dump(epicTree.tree, open(data_filename, "wb"), pickle.HIGHEST_PROTOCOL)
        return success(True)
    except Exception as inst:
        return make_error(inst, 500)

def init_from_filesystem(filename=None):
    """Load and initialise the tree using a pickled data file for the tree"""
    global epicTree
    data_filename = config.get('Files', 'DataFile')
    if filename is not None:
        data_filename = filename
    # No file with this name? Die!
    if not os.path.isfile(data_filename):
        print 'Data file does not exist (new setup? create a blank file called ' + data_filename + ')'
        exit(1)
    # Empty file? Initialise it!
    if os.stat(data_filename).st_size == 0:
        print 'Data file is empty, initialising file with an empty tree'
        temp_tree = EpicTree()
        pickle.dump(temp_tree.tree, open(data_filename, "wb"), pickle.HIGHEST_PROTOCOL)
    # Load the file into a new tree object
    try:
        epicTree = EpicTree(data_filename)
        print 'Loaded tree from filesystem!'
    except Exception as inst:
        print 'Error loading initial state from data file:'
        print inst
        exit(1)
    return

def init():
    """Load an initialise an empty tree (for testing purposes, etc.)"""
    global epicTree
    epicTree = EpicTree()
    return

def load_example_tree():
    """Private method (called from tests) to load an example tree into memory"""
    global epicTree
    epicTree.tree = {
        154: {
            12: {
                0: (None, 'root', None, 1, [1251, 241, 4612]),
                1251: (0, 'file', 1512, 2, None),
                241: (0, 'dir', None, 1, [351]),
                351: (2, 'file', 15523, 1, None),
                4612: (0, 'dir', None, 3, [516]),
                516: (4, 'smartview', 18450, 1, None)
            },
            15: {
                0: (None, 'root', None, 1, None)
            }
        },
        165: {
            }
    }
    return

# endregion

# region HTTP Response Handler

def success(obj):
    response = {
        'meta': {
            'code': '200',
            'message': 'OK',
        },
        'response': obj
    }
    response = jsonify(response)
    response.status_code = 200
    return response

@app.errorhandler(404)
def error_not_found(error=None):
    output_error = 'Resource not found.'
    if error is not None:
        if isinstance(error, basestring):
            output_error = error
        else:
            try:
                output_error += ' ' + str(error.description)
            except Exception as inst:
                output_error += ' ' + str(inst)
    return make_error(output_error, 404)

@app.errorhandler(500)
def error_unknown(error=None):
    output_error = 'Internal server error. We have caught this and will work to fix this issue ASAP.'
    # TODO: If on production environment don't do the following
    if error is not None:
        if isinstance(error, basestring):
            output_error = error
        else:
            try:
                output_error += ' ' + str(error.description)
            except Exception as inst:
                output_error += ' ' + str(inst)
    return make_error(output_error, 500)

def make_error(msg, code):
    response = {
        'meta': {
            'code': int(code),
            'message': str(msg),
        },
        'response': None
    }
    response = jsonify(response)
    response.status_code = code
    return response

# endregion

# region Helper methods

def make_simple_node(node_id, node_data):
    return {
        "id": node_id,
        "type": node_data[1],
        "data": node_data[2],
        "sort": node_data[3]
    }

# endregion

# region Init

if __name__ == '__main__':
    # Load tree
    init_from_filesystem()
    # Get server config
    port = int(config.get('Server', 'Port'))
    if environment == 'production':
        # Tornado
        http_server = HTTPServer(WSGIContainer(app))
        http_server.listen(port)
        # Debug & autoreload (dev only. tornado is for prod... maybe separate 'server' from 'logging level'?)
        #def fn():
        #    print "Hooked before reloading..."
        #tornado.autoreload.add_reload_hook(fn)
        #tornado.autoreload.start()
        #enable_pretty_logging()
        # Run Tornado
        IOLoop.instance().start()
    else:
        # Run Flask
        app.run(debug=True, host='0.0.0.0', port=port)

# endregion
