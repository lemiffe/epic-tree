import unittest
import app
import os
import json


class TreeTest(unittest.TestCase):

    TREE_ID = 201
    SEGMENT_ID = 202
    ROOT_ID = 203
    FIRST_DIR_ID = 204

    def setUp(self):
        self.app = app.app.test_client()
        app.init()
        # Create a tree
        post_data = json.dumps(dict(tree_id=self.TREE_ID))
        http_response = self.app.post('/tree', data=post_data, content_type='application/json')
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        # Create a segment
        post_data = json.dumps(dict(segment_id=self.SEGMENT_ID, root_node_id=self.ROOT_ID))
        post_url = '/tree/' + str(self.TREE_ID) + '/segment'
        http_response = self.app.post(post_url, data=post_data, content_type='application/json')
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        # Get the root node ID of the segment
        post_url = '/tree/' + str(self.TREE_ID) + '/segment/' + str(self.SEGMENT_ID) + '/root'
        http_response = self.app.get(post_url, follow_redirects=True)
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        self.assertEqual(result['response'], self.ROOT_ID)
        # Create a directory (position 500 => 1)
        post_url = '/tree/' + str(self.TREE_ID) + '/segment/' + str(self.SEGMENT_ID) + '/directory'
        post_data = json.dumps(dict(parent_node_id=self.ROOT_ID, node_id=self.FIRST_DIR_ID, position=500))
        http_response = self.app.post(post_url, data=post_data, content_type='application/json')
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)

    # region Trees

    def test_trees(self):
        """
        Endpoint: /tree
        Methods: ['POST', 'DELETE']
        Params: tree_id
        Responses: 200, 400, 404, 409
        """
        # Create new Parent tree
        http_response = self.app.post('/tree', data=json.dumps(dict(tree_id=1)), content_type='application/json')
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        # Expect conflict if we try to re-initialise
        http_response = self.app.post('/tree', data=json.dumps(dict(tree_id=1)), content_type='application/json')
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 409)

    def test_trees_get(self):
        """
        Endpoint: /trees
        Methods: ['GET']
        Responses: 200, 500
        """
        # Clear the tree
        self.app.post('/clear', data=(), content_type='application/json')
        # Create a couple of trees
        http_response = self.app.post('/tree', data=json.dumps(dict(tree_id=101)), content_type='application/json')
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        http_response = self.app.post('/tree', data=json.dumps(dict(tree_id=102)), content_type='application/json')
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        # Get the trees
        http_response = self.app.get('/trees', follow_redirects=True)
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        self.assertEqual(result['response'], [101, 102])

    # endregion

    # region Segments

    def test_segments_get(self):
        """
        Endpoint: /tree/{ID}/segments
        Methods: ['GET']
        Responses: 200, 400, 404, 409, 500
        """
        # Clear the tree
        self.app.post('/clear', data=(), content_type='application/json')
        # Create a tree
        post_data = json.dumps(dict(tree_id=self.TREE_ID))
        http_response = self.app.post('/tree', data=post_data, content_type='application/json')
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        # Verify we have no segments
        get_url = '/tree/' + str(self.TREE_ID) + '/segments'
        http_response = self.app.get(get_url, follow_redirects=True)
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        self.assertEqual(result['response'], [])

    def test_segment_create(self):
        """
        Endpoint: /tree/{ID}/segment
        Methods: ['POST']
        Params: segment_id
        Responses: 200, 400, 404, 409, 500
        """
        # Clear the tree
        self.app.post('/clear', data=(), content_type='application/json')
        # Create a tree
        post_data = json.dumps(dict(tree_id=self.TREE_ID))
        http_response = self.app.post('/tree', data=post_data, content_type='application/json')
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        # Create a segment
        post_data = json.dumps(dict(segment_id=self.SEGMENT_ID, root_node_id=self.ROOT_ID))
        post_url = '/tree/' + str(self.TREE_ID) + '/segment'
        http_response = self.app.post(post_url, data=post_data, content_type='application/json')
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        # Verify segment exists
        get_url = '/tree/' + str(self.TREE_ID) + '/segments'
        http_response = self.app.get(get_url, follow_redirects=True)
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        self.assertEqual(result['response'], [self.SEGMENT_ID])

    def test_segment_remove(self):
        """
        Endpoint: /tree/{ID}/segment/{ID}
        Methods: ['DELETE']
        Responses: 200, 400, 404, 409, 500
        """
        # Verify segment exists
        tree_url = '/tree/' + str(self.TREE_ID) + '/'
        http_response = self.app.get(tree_url + 'segments', follow_redirects=True)
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        self.assertEqual(result['response'], [202])
        # Remove segment
        http_response = self.app.delete(tree_url + 'segment/' + str(self.SEGMENT_ID), follow_redirects=True)
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        self.assertEqual(result['response'], True)
        # Verify segment has been removed
        http_response = self.app.get(tree_url + 'segments', follow_redirects=True)
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        self.assertEqual(result['response'], [])
        # Verify remove segment errors (405) - Status code check!
        http_response = self.app.delete(tree_url + 'segment', follow_redirects=True)
        self.assertEqual(http_response.status_code, 405)
        # Verify remove segment errors (404) - Status code check!
        http_response = self.app.delete(tree_url + 'segment/203', follow_redirects=True)
        self.assertEqual(http_response.status_code, 404)

    def test_segment_duplication(self):
        """
        Endpoint: /tree/{ID}/segment/{ID}/duplicate
        Methods: ['POST', 'PUT']
        Params: target_segment_id, nested_node_ids
        Responses: 200, 400, 404, 409, 500
        """
        # TODO
        return

    def test_segment_root(self):
        """
        Endpoint: /tree/{ID}/segment/{ID}/root
        Methods: ['GET']
        Responses: 200, 400, 404, 500
        """
        # Get the root
        get_url = '/tree/' + str(self.TREE_ID) + '/segment/' + str(self.SEGMENT_ID) + '/root'
        http_response = self.app.get(get_url, follow_redirects=True)
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        self.assertEqual(result['response'], 203)

    # endregion

    # region Retrieval + Traversal

    def test_level_get(self):
        """
        Endpoint: /tree/{ID}/segment/{ID}/level/{PARENT_NODE_ID}
        Methods: ['GET']
        Params: parent_node_id, node_id, position?
        Responses: 200, 400, 404, 500
        """
        # Get level
        get_url = '/tree/' + str(self.TREE_ID) + '/segment/' + str(self.SEGMENT_ID) + '/level/' + str(self.ROOT_ID)
        http_response = self.app.get(get_url, follow_redirects=True)
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        self.assertEqual(len(result['response']), 1)  # 1 directory

    def test_breadcrumbs(self):
        """
        Endpoint: /tree/{ID}/segment/{ID}/breadcrumbs/{NODE_ID}
        Methods: ['GET']
        Responses: 200, 400, 404, 500
        """
        subdir = 210
        # Create a subdirectory
        post_data = json.dumps(dict(parent_node_id=self.FIRST_DIR_ID, node_id=subdir))
        post_url = '/tree/' + str(self.TREE_ID) + '/segment/' + str(self.SEGMENT_ID) + '/directory'
        http_response = self.app.post(post_url, data=post_data, content_type='application/json')
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        # Get breadcrumbs for directory
        get_url = '/tree/' + str(self.TREE_ID) + '/segment/' + str(self.SEGMENT_ID) + '/breadcrumbs/' + str(subdir)
        http_response = self.app.get(get_url, follow_redirects=True)
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        self.assertEqual(len(result['response']), 3)
        self.assertEqual(result['response'], [self.ROOT_ID, self.FIRST_DIR_ID, subdir])

    def test_tree_segment_get(self):
        """
        Endpoint: /tree/{ID}/segment/{ID}
        Methods: ['GET']
        Responses: 200, 400, 404, 500
        """
        # TODO
        self.assertEqual(1, 1)

    def test_tree_get(self):
        """
        Endpoint: /tree/{ID}
        Methods: ['GET']
        Responses: 200, 400, 404, 500
        """
        # TODO
        self.assertEqual(1, 1)

    def test_everything_get(self):
        """
        Endpoint: /tree
        Methods: ['GET']
        Responses: 200, 500
        """
        # TODO
        self.assertEqual(1, 1)

    # endregion

    # region Directories

    def test_directories(self):
        """
        Endpoint: /tree/{ID}/segment/{ID}/directory
        Methods: ['POST']
        Params: parent_node_id, node_id, position?
        Responses: 200, 400, 404, 409, 500
        """
        # Create a directory (position 2)
        post_data = json.dumps(dict(parent_node_id=self.ROOT_ID, node_id=205, position=2))
        post_url = '/tree/' + str(self.TREE_ID) + '/segment/' + str(self.SEGMENT_ID) + '/directory'
        http_response = self.app.post(post_url, data=post_data, content_type='application/json')
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        # Create a directory (no position = end)
        post_data = json.dumps(dict(parent_node_id=self.ROOT_ID, node_id=206))
        http_response = self.app.post(post_url, data=post_data, content_type='application/json')
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        # Create a bad directory (parent is not right)
        post_data = json.dumps(dict(parent_node_id=210, node_id=207))
        http_response = self.app.post(post_url, data=post_data, content_type='application/json')
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 404)
        # Send incomplete data
        post_data = json.dumps(dict())
        http_response = self.app.post(post_url, data=post_data, content_type='application/json')
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 400)
        # Get level
        get_url = '/tree/' + str(self.TREE_ID) + '/segment/' + str(self.SEGMENT_ID) + '/level/' + str(self.ROOT_ID)
        http_response = self.app.get(get_url, follow_redirects=True)
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        self.assertEqual(len(result['response']), 3)
        items_found = 0
        expected_position = 1
        for item in result['response']:
            if item['id'] in [204, 205, 206] and item['type'] == 'dir' and item['sort'] == expected_position:
                items_found += 1
                expected_position += 1
        self.assertEqual(items_found, 3)
        # Remove first 2 directories
        post_url = '/tree/' + str(self.TREE_ID) + '/segment/' + str(self.SEGMENT_ID) + '/directory/' + str(self.FIRST_DIR_ID)
        http_response = self.app.delete(post_url, follow_redirects=True)
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        self.assertEqual(result['response'], True)
        post_url = '/tree/' + str(self.TREE_ID) + '/segment/' + str(self.SEGMENT_ID) + '/directory/205'
        http_response = self.app.delete(post_url, follow_redirects=True)
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        self.assertEqual(result['response'], True)
        # Verify remaining directory exists and has sort set to 1 now
        get_url = '/tree/' + str(self.TREE_ID) + '/segment/' + str(self.SEGMENT_ID) + '/level/' + str(self.ROOT_ID)
        http_response = self.app.get(get_url, follow_redirects=True)
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        self.assertEqual(len(result['response']), 1)
        items_found = 0
        for item in result['response']:
            if item['id'] == 206 and item['type'] == 'dir' and item['sort'] == 1:
                items_found += 1
        self.assertEqual(items_found, 1)

    def test_directory_duplication(self):
        """
        Endpoint: /tree/{ID}/segment/{ID}/directory/{ID}/duplicate
        Methods: ['POST', 'PUT']
        Params: target_segment_id, target_parent_id, new_node_id, nested_node_ids
        Responses: 200, 400, 404, 409
        """
        # TODO
        return

    def test_directory_move(self):
        """
        Endpoint: /tree/{ID}/segment/{ID}/directory/{ID}/move
        Methods: ['POST', 'PUT']
        Params: target_segment_id, target_parent_id, new_node_id, nested_node_ids
        Responses: 200, 400, 404, 409
        """
        # TODO
        return

    # endregion

    # region Nodes

    '''
    /tree/<int:tree_id>/segment/<int:segment_id>/node, methods=['POST', 'DELETE']
        # epicTree.add_node (100, 1000, 2000, 2001, 1, None, 'asset', 12348)
    /tree/<int:tree_id>/segment/<int:segment_id>/node/<int:node_id>/move, methods=['POST', 'PUT']
    /tree/<int:tree_id>/segment/<int:segment_id>/level/<int:parent_node_id>, methods=['POST']
    '''

    # endregion

    # region Clear Tree

    def test_clear(self):
        """
        Endpoint: /clear
        Methods: ['POST']
        Responses: 200, 500
        """
        # Clear tree
        http_response = self.app.post('/clear', data=dict(), follow_redirects=True)
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        self.assertEqual(bool(result['response']), True)
        # Get tree
        http_response = self.app.get('/tree', follow_redirects=True)
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        self.assertEqual(result['response'], {})

    # endregion

    # region Persist + Load

    def test_persist_and_reload(self):
        """
        Endpoint: /persist
        Methods: ['POST']
        Params: filename (optional, otherwise uses main file specified in config)
        Responses: 200, 500
        """
        test_file = "test.data"
        # Clear the tree
        self.app.post('/clear', data=(), content_type='application/json')
        # Persist empty tree
        post_data = json.dumps(dict(filename=test_file))
        http_response = self.app.post('/persist', data=post_data, content_type='application/json')
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        self.assertEqual(bool(result['response']), True)
        # Load from filesystem
        app.init_from_filesystem(test_file)
        # Verify we have an empty tree
        http_response = self.app.get('/tree', follow_redirects=True)
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        self.assertEqual(result['response'], {})
        # Persist example tree
        app.load_example_tree()
        post_data = json.dumps(dict(filename=test_file))
        http_response = self.app.post('/persist', data=post_data, content_type='application/json')
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        self.assertEqual(bool(result['response']), True)
        # Load from filesystem
        app.init_from_filesystem(test_file)
        # Verify we have a non-empty tree
        http_response = self.app.get('/tree', follow_redirects=True)
        result = json.loads(http_response.data)
        self.assertEqual(int(result['meta']['code']), 200)
        self.assertNotEqual(result['response'], {})
        # Remove temporary file
        os.remove(test_file)

    # endregion

if __name__ == '__main__':
    unittest.main()