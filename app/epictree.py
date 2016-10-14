from collections import deque
import pickle


class EpicTree:
    """Epic Tree module"""

    # Constructor
    def __init__(self, filename=''):
        self.tree = {}
        self.materialised_paths = []
        self.garbage = []
        # Load data file if provided
        if filename != '':
            self.tree = pickle.load(open(filename, "rb"))

    # region Trees

    def add_tree(self, tree_id):
        """Add Tree"""
        if tree_id in self.tree:
            raise KeyError('Tree ' + str(tree_id) + ' already exists')
        self.tree[tree_id] = {}
        return

    def remove_tree(self, tree_id):
        """Remove Tree"""
        # Non-atomic function, so we use try..except
        try:
            del self.tree[tree_id]
        except KeyError:
            raise KeyError('Tree ' + str(tree_id) + ' does not exist')
        # No GC as we killed the entire structure for the org
        # Materialise
        self.materialised_paths = [x for x in self.materialised_paths if not x.startswith(str(tree_id) + '/')]
        return

    def get_trees(self):
        """Get list of tree IDs"""
        return [a for a, data in iter(self.tree.items())]

    # endregion

    # region Segments

    def get_segments(self, tree_id):
        """Get the segments that belong to a tree"""
        if tree_id not in self.tree:
            raise KeyError('Tree ' + str(tree_id) + ' doesn\'t exist')
        return [a for a, data in iter(self.tree[tree_id].items())]

    def add_segment(self, tree_id, segment_id, root_node_id):
        """Segment adding"""
        if tree_id not in self.tree:
            raise KeyError('Tree ' + str(tree_id) + ' doesn\'t exist')
        if segment_id in self.tree[tree_id]:
            raise KeyError('Segment ' + str(segment_id) + ' already exists')
        self.tree[tree_id][segment_id] = {root_node_id: (None, 'root', None, 1, None)}
        self.materialised_paths.append(str(tree_id) + '/' + str(segment_id))
        self.materialised_paths.append(str(tree_id) + '/' + str(segment_id) + '/' + str(root_node_id))
        return

    def remove_segment(self, tree_id, segment_id):
        """Segment removal"""
        # Non-atomic function, so we use try..except
        try:
            root_node_id = self.get_segment_root_node(tree_id, segment_id)
            del self.tree[tree_id][segment_id]
            # GC (from root node)
            self.garbage.append((tree_id, segment_id, root_node_id))
        except KeyError:
            raise KeyError('Segment ' + str(segment_id) + ' does not exist')
        # Materialise
        self.materialised_paths = [
            x for x in self.materialised_paths
            if not x.startswith(str(tree_id) + '/' + str(segment_id) + '/')
            and x != str(tree_id) + '/' + str(segment_id)
        ]
        return

    def duplicate_segment(self, tree_id, from_segment_id, to_segment_id, segment_structure):
        """Segment duplication"""
        if from_segment_id not in self.tree[tree_id]:
            raise KeyError('Segment ' + from_segment_id + ' not found in tree when trying to duplicate it')
        old_segment = self.tree[tree_id][from_segment_id]
        self.tree[tree_id][to_segment_id] = old_segment
        # TODO: Copy children! (segment_structure is a dict with hierarchical tree of new node ids)
        # TODO: materialised path
        return

    def get_segment_root_node(self, tree_id, segment_id):
        """Find root node ID in segment"""
        # TODO: Search materialised path first
        # Does the segment exist?
        if tree_id not in self.tree:
            raise KeyError('Tree ' + str(tree_id) + ' doesn\'t exist')
        if segment_id not in self.tree[tree_id]:
            raise KeyError('Segment ' + str(segment_id) + ' not found')
        # Search for the root
        root_node_id = None
        nodes = self.tree[tree_id][segment_id]
        for node_id, node in iter(nodes.items()):
            if node[1] == 'root':
                root_node_id = node_id
                break
        return root_node_id

    # endregion

    # region Retrieval

    def get_level(self, tree_id, segment_id, parent_node_id):
        """Get Level (children of a parent node)"""
        # TODO: Search materialised path first
        # Does the segment exist?
        if tree_id not in self.tree:
            raise KeyError('Tree ' + str(tree_id) + ' doesn\'t exist')
        if segment_id not in self.tree[tree_id]:
            raise KeyError('Segment ' + str(segment_id) + ' doesn\'t exist')
        if parent_node_id not in self.tree[tree_id][segment_id]:
            raise KeyError('Parent node ' + str(parent_node_id) + ' doesn\'t exist')
        # Get the children IDs
        parent_node = self.tree[tree_id][segment_id][parent_node_id]
        children_ids = parent_node[4]
        # Iterate through the list and build a nice array
        results = []
        if children_ids is not None:
            for child_id in children_ids:
                results.append({'id': child_id, 'child': self.tree[tree_id][segment_id][child_id]})
        return results

    def get_breadcrumbs(self, tree_id, segment_id, node_id):
        """Get Breadcrumbs (find ancestors)"""
        # TODO: Search materialised path first
        # Does the segment exist?
        if tree_id not in self.tree:
            raise KeyError('Tree ' + str(tree_id) + ' doesn\'t exist')
        if segment_id not in self.tree[tree_id]:
            raise KeyError('Segment ' + str(segment_id) + ' doesn\'t exist')
        if node_id not in self.tree[tree_id][segment_id]:
            raise KeyError('Node ' + str(node_id) + ' doesn\'t exist')
        # Find node by backtracing
        node = self.tree[tree_id][segment_id][node_id]
        parent_node_id = node[0]
        path = deque([node_id])
        if parent_node_id is not None:
            path.extendleft(reversed(self.get_breadcrumbs(tree_id, segment_id, parent_node_id)))
        return list(path)

    def get_tree_from_node(self, tree_id, segment_id, parent_node_id):
        """
        Get tree (starting from a node) - sorted!
        :param tree_id: int
        :param segment_id: int
        :param parent_node_id: int
        :return: []
        """
        # TODO: A lot of pressure is on you my little friend :)  Too many functions depend on you!
        return

    def get_tree_from_segment(self, tree_id, segment_id):
        """
        Get tree (full segment) - sorted!
        :param tree_id: int
        :param segment_id: int
        :return: []
        """
        # Does the segment exist?
        if tree_id not in self.tree:
            raise KeyError('Tree ' + str(tree_id) + ' doesn\'t exist')
        if segment_id not in self.tree[tree_id]:
            raise KeyError('Segment ' + str(segment_id) + ' doesn\'t exist')
        root_node_id = self.get_segment_root_node(tree_id, segment_id)
        return self.get_tree_from_node(tree_id, segment_id, root_node_id)

    def get_tree_from_segments(self, tree_id, segment_ids):
        """Get tree (set of segments) - sorted!"""
        # Does the segment exist?
        if tree_id not in self.tree:
            raise KeyError('Tree ' + str(tree_id) + ' doesn\'t exist')
        for segment_id in segment_ids:
            if segment_id not in self.tree[tree_id]:
                raise KeyError('Segment ' + str(segment_id) + ' doesn\'t exist')
        # Build structure (array containing trees representing each segment)
        results = {}
        for segment_id in segment_ids:
            results[segment_id] = self.get_tree_from_segment(tree_id, segment_id)
        return results

    def get_tree(self, tree_id):
        """Get tree"""
        # Does the segment exist?
        if tree_id not in self.tree:
            raise KeyError('Tree ' + str(tree_id) + ' doesn\'t exist')
        segment_ids = self.get_segments(tree_id)
        return self.get_tree_from_segments(tree_id, segment_ids)

    def get_everything(self):
        """Get tree (everything)"""
        tree_ids = self.get_trees()
        results = {}
        for tree_id in tree_ids:
            results[tree_id] = self.get_tree(tree_id)
        return results

    # endregion

    # region Directories

    def add_directory(self, tree_id, segment_id, parent_node_id, node_id, sort, children):
        """Directory adding (optional sort which causes re-sorting, otherwise placed at end)"""
        self.add_node(tree_id, segment_id, parent_node_id, node_id, sort, children, 'dir', None)
        return

    def remove_directory(self, tree_id, segment_id, node_id):
        """Directory removal"""
        self.remove_node(tree_id, segment_id, node_id)
        return

    def duplicate_directory(self, tree_id, segment_id, node_id):
        """Directory duplication (re-sort only if duplicating in same level + materialise + copy all children)"""
        # TODO
        return

    def move_directory(self, tree_id, segment_id, node_id, target_parent_id, sort):
        """Move directory to child, or another segment (add existing folder in another)"""
        # Moving to another segment causes all children to be transported (with new ids)
        # TODO
        return

    # endregion

    # region Nodes

    def add_node(self, tree_id, segment_id, parent_node_id, node_id, sort, children, node_type, payload):
        """Node adding (optional sort which causes re-sorting, otherwise placed at end)"""
        # Does the segment exist?
        if tree_id not in self.tree:
            raise KeyError('Tree ' + str(tree_id) + ' doesn\'t exist')
        if segment_id not in self.tree[tree_id]:
            raise KeyError('Segment ' + str(tree_id) + ' doesn\'t exist')
        # Get parent and level
        re_sort = True
        parent_node = self.tree[tree_id][segment_id][parent_node_id]
        level_nodes = parent_node[4]
        # If parent is not dir or root, don't allow addition
        if parent_node[1] != 'root' and parent_node[1] != 'dir':
            raise Exception('Can\'t add child node to non-directory or non-root node')
        # If sort is set, but this is the first child in level, always use 1
        if sort is not None:
            if level_nodes is None or len(level_nodes) == 0:
                sort = 1
                re_sort = False
        # If sort is set, but exceeds maximum current sort in level by more than 1 (or is equal), set to max + 1
        if sort is not None:
            if level_nodes is not None and len(level_nodes) > 1:
                max_sort = self._get_max_sort_at_level(tree_id, segment_id, level_nodes)
                if sort > (max_sort + 1) or sort == max_sort:
                    sort = max_sort + 1
                    re_sort = False
            elif level_nodes is not None and len(level_nodes) == 1:
                # New node is about to be added, we can assume first one has sort of 1
                sort = 2
                re_sort = False
        # If sort is None, find greatest sort so far, add 1
        if sort is None:
            if level_nodes is None or len(level_nodes) == 0:
                sort = 1
            else:
                max_sort = self._get_max_sort_at_level(tree_id, segment_id, level_nodes)
                if max_sort is not None:
                    sort = max_sort + 1
                else:
                    sort = 1
            re_sort = False
        # Add child
        self.tree[tree_id][segment_id][node_id] = (parent_node_id, node_type, payload, sort, children)
        if re_sort is True:
            self._increment_sort_after_item(tree_id, segment_id, sort, parent_node_id, node_id)
        # Add child to parent's list of children
        parent_node = self.tree[tree_id][segment_id][parent_node_id]
        new_children = parent_node[4]
        if new_children is None:
            new_children = []
        new_children.append(node_id)
        parent_node = (parent_node[0], parent_node[1], parent_node[2], parent_node[3], new_children)
        self.tree[tree_id][segment_id][parent_node_id] = parent_node
        # Materialised path
        breadcrumbs = self.get_breadcrumbs(tree_id, segment_id, node_id)
        self.materialised_paths.append(str(tree_id) + '/' + str(segment_id) + '/' + '/'.join(str(x) for x in breadcrumbs))
        # TODO: also have an override sort option (for quick DB import)
        return

    def remove_node(self, tree_id, segment_id, node_id):
        """Remove node (re-sort level fully, GC, materialise)"""
        # Does the segment exist?
        if tree_id not in self.tree:
            raise KeyError('Tree ' + str(tree_id) + ' doesn\'t exist')
        if segment_id not in self.tree[tree_id]:
            raise KeyError('Segment ' + str(tree_id) + ' doesn\'t exist')
        # This is not the root right?
        node = self.tree[tree_id][segment_id][node_id]
        if node[1] == 'root':
            raise Exception('You can\'t remove the root of a segment')
        # Get parent
        parent_node_id = node[0]
        parent_node = self.tree[tree_id][segment_id][parent_node_id]
        # Get breadcrumbs (before we delete the node)
        breadcrumbs = self.get_breadcrumbs(tree_id, segment_id, node_id)
        # Remove child from parent (if found)
        new_children = parent_node[4]
        if node_id in new_children:
            new_children.remove(node_id)
            parent_node = (parent_node[0], parent_node[1], parent_node[2], parent_node[3], new_children)
            self.tree[tree_id][segment_id][parent_node_id] = parent_node
        # Re-sort items at parent's level
        self._re_sort_level(tree_id, segment_id, parent_node_id)
        # Non-atomic function, so we use try..except
        try:
            del self.tree[tree_id][segment_id][node_id]
            # GC (from root node)
            if node[1] == 'dir':
                self.garbage.append((tree_id, segment_id, node_id))
        except KeyError:
            # TODO: parent modified, re-add child to parent?
            raise Exception('Segment ' + str(segment_id) + ' does not exist')
        # Materialise
        material_path_to_node = '/'.join(str(x) for x in breadcrumbs)
        full_path = str(tree_id) + '/' + str(segment_id) + '/' + material_path_to_node
        try:
            self.materialised_paths.remove(full_path)
            if node[1] == 'dir':
                route_children = str(tree_id) + '/' + str(segment_id) + '/' + material_path_to_node + '/'
                self.materialised_paths = [x for x in self.materialised_paths if not x.startswith(route_children)]
        except KeyError:
            # TODO: Log
            pass
        return

    def move_node(self, tree_id, segment_id, node_id, target_parent_id, sort):
        """Move node (other directory, or just re-sort)"""
        # TODO
        # If just sort, then +1 all greater than current sort first
        # increment_sort_after_item(tree_id, segment_id, sort)
        # move_directory can call this function as it essentially does the same
        return

    def add_level(self, tree_id, segment_id, target_parent_id, sorted_node_tree):
        """Add a whole level under a parent (input tree must be sorted)"""
        # TODO
        return

    # endregion

    # region Generic, Persist and Cleanup

    def clear_everything(self):
        """Clear the tree completely"""
        # Non-atomic function, so we use try..except
        try:
            self.tree = {}
            self.garbage = []
            self.materialised_paths = []
        except KeyError:
            raise KeyError('Error clearing everything')
        return

    # GC (traverse tree, starting from children that point to deletednode_id, kill all orphans!)
    def gc(self):
        # TODO
        # Use self.garbage []
        # Go through self.garbage, look for nodes and child nodes pointing towards each item
        # No need to re-materialise, everything was cleaned up in sync!
        # This should be called by every destructive operation when the node has children
        return

    # endregion

    # region Private: Tree traversal & search

    def _find_node_from_root(self, tree_id, segment_id, search_node_id):
        """Find node_id (depth-first, from root)"""
        # TODO: Search materialised path first
        # Does the segment exist?
        if tree_id not in self.tree:
            raise KeyError('Tree ' + str(tree_id) + ' doesn\'t exist')
        if segment_id not in self.tree[tree_id]:
            raise KeyError('Could not find segment ' + str(tree_id) + '.' + str(segment_id) + ' when searching for node ' + str(search_node_id))
        # Search for the root
        root_node_id = self.get_segment_root_node(tree_id, segment_id)
        if root_node_id is None:
            raise KeyError('Could not find root node in segment ' + str(tree_id) + '.' + str(segment_id) + ' when searching for node ' + str(search_node_id))
        # Traverse the tree recursively (depth-first) to find child!
        return self._find_node_from_node(tree_id, segment_id, search_node_id, root_node_id)

    def _find_node_from_node(self, tree_id, segment_id, search_node_id, start_node_id):
        """Recursive (depth-first) function to find a child node starting with a node_id"""
        # Am I the one you are looking for?
        if search_node_id == start_node_id:
            return search_node_id
        # Get children
        children_node_ids = self.tree[tree_id][segment_id][start_node_id][4]
        # No children? Not found!
        if children_node_ids is None:
            return None
        # Search in children
        for node_id in children_node_ids:
            # Found? Return!
            if node_id == search_node_id:
                return node_id # Quit early!
            else:
                # Get child node
                node = self.tree[tree_id][segment_id][node_id]
                # Go one level deeper, maybe this child has children (only if dir!)
                if node[1] == 'dir':
                    result = self.find_node_from_node(tree_id, segment_id, search_node_id, node_id)
                    if result is not None:
                        return result
        # Nothing found in children? Let's head back up!
        return None

    # endregion

    # region Private: Sorting

    def _get_max_sort_at_level(self, tree_id, segment_id, level_node_ids):
        """
        Get maximum current sort for a level
        :param tree_id:
        :param segment_id:
        :param level_node_ids:
        :return:
        """
        max_sort = -1
        for node_id in level_node_ids:
            node_sort = self.tree[tree_id][segment_id][node_id][3]
            if node_sort > max_sort:
                max_sort = node_sort
        if max_sort == -1:
            return None
        return max_sort

    def _re_sort_item(self, tree_id, segment_id, modified_node_id):
        """
        Re-sort (e.g. new node with sort 4 causes all with 4 or greater to increment by 1)
        This is more of something that happens after node insertion or change (like a listener)
        :param tree_id:
        :param segment_id:
        :param modified_node_id:
        :return:
        """
        # Get modified node
        modified_node = self.tree[tree_id][segment_id][modified_node_id]
        modified_sort_position = modified_node[3]
        # Get parent
        parent_node = self.tree[tree_id][segment_id][modified_node[0]]
        # Get siblings (children of parent)
        sibling_ids = parent_node[4]
        # Find those greater or equal to sort of modified_node_id + increment by 1
        if sibling_ids is not None and len(sibling_ids) > 1:
            for node_id in sibling_ids:
                node = self.tree[tree_id][segment_id][node_id]
                if node[3] >= modified_sort_position and node_id != modified_node_id:
                    self.tree[tree_id][segment_id][node_id] = (node[0], node[1], node[2], node[3] + 1, node[4])
        return

    def _re_sort_level(self, tree_id, segment_id, parent_node_id):
        """
        Re-sort level fully (check for gaps, duplicates, negatives, etc.) called after node deletion, etc.
        :param tree_id:
        :param segment_id:
        :param parent_node_id:
        :return:
        """
        # Get parent
        parent_node = self.tree[tree_id][segment_id][parent_node_id]
        # Get level nodes (children of parent)
        level_node_ids = parent_node[4]
        level_nodes = {}
        # Quit early if nothing here
        if level_node_ids is None or len(level_node_ids) == 0:
            return
        # Form a dict which we will sort
        for level_node_id in level_node_ids:
            level_nodes[level_node_id] = self.tree[tree_id][segment_id][level_node_id]
        # If only one item, set to 1
        if len(level_node_ids) == 1:
            node_id = level_node_ids[0]
            node = self.tree[tree_id][segment_id][node_id]
            if node[3] != 1:
                self.tree[tree_id][segment_id][node_id] = (node[0], node[1], node[2], 1, node[4])
        # If more than one item, restructure
        elif len(level_node_ids) > 1:
            # Get sorted list first
            sorted_node_ids = sorted(level_nodes.keys(), key=lambda x: level_nodes[x][3])
            first_node = level_nodes[sorted_node_ids[0]]
            # Starts > 1? Push all back by MIN(sort) + 1
            if first_node[3] > 1:
                min_sort = first_node[3]
                for node_id, node in iter(level_nodes.items()):
                    new_node_sort = node[3] - min_sort + 1
                    self.tree[tree_id][segment_id][node_id] = (node[0], node[1], node[2], new_node_sort, node[4])
            # Starts < 1? Push all forward by ABS(MIN(sort)) + 1
            elif first_node[3] < 1:
                min_sort = first_node[3]
                new_min_sort = abs(min_sort) + 1
                for node_id, node in iter(level_nodes.items()):
                    new_node_sort = node[3] + new_min_sort
                    self.tree[tree_id][segment_id][node_id] = (node[0], node[1], node[2], new_node_sort, node[4])
            # Duplicates: higher node ID is pushed afterwards
            duplicates = []
            all_sorts = []
            for node_id in sorted_node_ids:
                node = level_nodes[node_id]
                sort_number = node[3]
                if sort_number in all_sorts:
                    duplicates.append(node_id)
                all_sorts.append(sort_number)
            for duplicate_node_id in duplicates:
                # TODO: Horrible, can be fixed afterwards as it is O(n^2)
                # Might also cause issues if more than one duplicate with same sort_number)
                self._re_sort_item(tree_id, segment_id, duplicate_node_id)
            # Gaps: Push all afterwards back by one
            gaps = []
            prev_sort = 0
            for node_id in sorted_node_ids:
                node = level_nodes[node_id]
                sort_number = node[3]
                if sort_number > (prev_sort + 1):
                    gaps.append(node_id)
                prev_sort = sort_number
            if len(gaps) > 0:
                started_gap_fixing = False
                prev_node_id = None
                for node_id in sorted_node_ids:
                    # Once we start fixing we have to check all the ones afterwards!
                    if prev_node_id is not None and (node_id in gaps or started_gap_fixing is True):
                        node = level_nodes[node_id]
                        sort_number = node[3]  # eg. 8
                        prev_node = self.tree[tree_id][segment_id][prev_node_id] # Has to be from the tree!
                        prev_sort_number = prev_node[3] # eg. 5
                        if sort_number > (prev_sort_number + 1):
                            difference = sort_number - prev_sort_number # eg. 3
                            new_node_sort = sort_number - difference + 1
                            self.tree[tree_id][segment_id][node_id] = (node[0], node[1], node[2], new_node_sort, node[4])
                        started_gap_fixing = True
                    prev_node_id = node_id
        level_nodes = None  # GC just in case
        return

    def _increment_sort_after_item(self, tree_id, segment_id, sort_number, parent_node_id, modified_node_id):
        """
        Looks for a specific sort target (e.g. 4) and increments all greater than that
        allowing insertion of an item '5' now that 5 became 6
        This is more of something that happens after node insertion or change (like a listener)
        :param tree_id:
        :param segment_id:
        :param sort_number:
        :param parent_node_id:
        :param node_id:
        :return:
        """
        # Get parent
        parent_node = self.tree[tree_id][segment_id][parent_node_id]
        # Get siblings (children of parent)
        sibling_ids = parent_node[4]
        # Find those greater or equal to sort of modified_node_id + increment by 1
        if sibling_ids is not None and len(sibling_ids) > 1:
            for node_id in sibling_ids:
                node = self.tree[tree_id][segment_id][node_id]
                if node[3] >= sort_number and node_id != modified_node_id:
                    self.tree[tree_id][segment_id][node_id] = (node[0], node[1], node[2], node[3] + 1, node[4])
        return

    # endregion
