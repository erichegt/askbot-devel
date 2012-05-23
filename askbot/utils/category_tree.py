"""This is temporary code to parse category
tree, stored in the settings.
The tree is plain text, with levels of branching 
reflected by indentation (2 spaces per level).
"""
def get_subtree(tree, path):
        if len(path) == 1:
            assert(path[0] == 0)
            return tree
        else:
            import copy
            parent_path = copy.copy(path)
            leaf_index = parent_path.pop()
            branch_index = parent_path[-1]
            parent_tree = get_subtree(tree, parent_path)
            return parent_tree[branch_index][1]

def parse_tree(text):
    """parse tree represented as indented text
    one item per line, with two spaces per level of indentation
    """
    lines = text.split('\n')
    import re
    in_re = re.compile(r'^([ ]*)')

    tree = [['dummy', []]]
    subtree_path = [0]
    clevel = 0

    for line in lines:
        if line.strip() == '':
            continue
        match = in_re.match(line)
        level = len(match.group(1))/2 + 1

        if level > clevel:
            subtree_path.append(0)#
        elif level < clevel:
            subtree_path = subtree_path[:level+1]
            leaf_index = subtree_path.pop()
            subtree_path.append(leaf_index + 1)
        else:
            leaf_index = subtree_path.pop()
            subtree_path.append(leaf_index + 1)

        clevel = level
        try:
            subtree = get_subtree(tree, subtree_path)
        except:
            return tree
        subtree.append([line.strip(), []])

    return tree
