def get_obj_by_id(object_list: list, id_to_find: str):
    return next(
        (obj for obj in object_list if obj['id'] == id_to_find),
        None
    )