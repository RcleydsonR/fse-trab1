import json
def get_obj_by_id(object_list: list, id_to_find: str):
    return next(
        (obj for obj in object_list if obj['id'] == id_to_find),
        None
    )

def get_initial_state():
    return {
        "L_01": 0,
        "L_02": 0,
        "AC": 0,
        "PR": 0,
        "AL_BZ": 0,
        "SPres": 0,
        "SFum": 0,
        "SJan": 0,
        "SPor": 0,
        "SC_IN": 0,
        "SC_OUT": 0,
        "Temperature": 0,
        "Humidity": 0
    }

def encode_command(**data):
    encoded_json = {}
    for key, value in data.items():
        encoded_json[key] = value
    return json.dumps(encoded_json)

# print(encode_command(type="first_access", id_value="1"))