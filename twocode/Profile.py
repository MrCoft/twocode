import humanize

def list_objects(module):
    memo = set()
    objects = []
    def travel(node):
        ptr = id(node)
        if ptr in memo:
            return 0, 0, 0
        memo.add(ptr)
        objects.append(node)

def code_size(module):
    memo = set()
    def travel(node):
        ptr = id(node)
        if ptr in memo:
            return 0, 0, 0
        memo.add(ptr)

        count, depth, size = 1, 0, 0
        if isinstance(node, Object) or isinstance(node, dict):
            for key, value in node.items():
                size += 8

                c, d, s = travel(value)
                count += c
                depth = max(depth, d)
                size += s
            depth += 1
        else:
            if node is None:
                pass
            elif isinstance(node, str):
                size += len(node.encode("utf-8"))
            elif isinstance(node, list):
                size += 8
                for item in node:
                    c, d, s = travel(item)
                    count += c
                    depth = max(depth, d)
                    size += s
                depth += 1

        return count, depth, size

    count, depth, size = travel(module)

    return " ".join(str(item) for item in [count, "nodes,", depth, "depth,", humanize.naturalsize(size), "memory size"])