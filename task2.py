import ujson

# case 1 simple values
arr = ['hello', 2, 3.21, 2, 'hello', 'Hello']
print(arr := list(set(arr)))

# case 2 dicts and None
arr = [
    None,
    'hello',
    2, 3.20, 3.2, 3.2099999999999, 2, 'hello',
    {'a': {'v': 2, 'a': 3}},
    {'m': {'kk': 2}, 'z': [1, 3, 'aaa']},
    {'a': {'v': 2, 'a': 3}},
    {'a': {'a': 3, 'v': 2}},
    {'m': {'kk': 2}, 'z': ['aaa', 1, 3]},
    ]

new_arr = []

for i, k in enumerate(sorted(arr, key=lambda k: ujson.dumps(k))):
    if i == 0:
        new_arr.append(k)
        previous = k
        continue

    if previous != k:
        new_arr.append(k)

    previous = k

print(arr := new_arr)

# case 3
# for comparing objects without normal serialization (through pickle or ujson)
# class ComparatorWrapper:
#     def __eq__....
#
