"""
Module for converting jsonp to json.
"""


def jsonp_to_json(jsonp):
    try:
        l_index = jsonp.index("(") + 1
        r_index = jsonp.rindex(")")
    except ValueError:
        print("Input is not in jsonp format.")
        return None

    res = jsonp[l_index:r_index]
    return res
