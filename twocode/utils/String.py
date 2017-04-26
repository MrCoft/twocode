def shared_str(s1, s2):
    len = 0
    for c1, c2 in zip(s1, s2):
        if c1 == c2:
            len += 1
        else:
            break
    return len