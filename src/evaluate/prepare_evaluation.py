import re
import json
import os
import sys
sys.path.append(os.path.abspath('..'))
from src.module import utils


# Mach das Programm auf ein Dokument, runne locate_identifiers und speichere das Ergebnis wo ab und am Ende combine alles.

def locate_identifiers(
    pii_json: list[dict[str, str]],
    original_text: str,
    doc_id: str
) -> dict[str, list[list[int]]]:
    """
    Takes the JSON object containing the PIIs and their context
    and returns a list of list containing the starting and end
    position of a PII.

    Args:
        pii_json (list[dict[str, str]]): List of dicts of identified
        PIIs with identifier, context, uuid keys.
        original_text (str): Text from where PII was identified.
        doc_id (str): ID of Document.

    Returns:
        dict[str, list[list[inst]]]: List of list with start and end
        position of PII.
    """
    results = []
    position_list = []
    for rec in pii_json:
        context = rec["context"]
        identifier = rec["identifier"]

        context_re = re.compile(re.escape(context))
        context_m = context_re.search(original_text)
        if not context_m:
            print(f"Context not found for uuid {rec['uuid']!r}")
            continue

        context_start, context_end = context_m.span()

        id_re = re.compile(re.escape(identifier), flags=re.IGNORECASE)
        for m in id_re.finditer(original_text[context_start:context_end]):
            abs_start = context_start + m.start()
            abs_end = context_start + m.end()
            results.append({
                "uuid": rec["uuid"],
                "found": m.group(),
                "start": abs_start,
                "end": abs_end
            })

    for result in results:
        position_list.append([result["start"], result["end"]])

    return {doc_id: position_list}


def combine(
    list_position_dict: list[dict[str, list[list[int]]]]
) -> dict[str, list[list[int]]]:
    """
    Returns a combined dict of all dicts in list_position_dict.

    Args:
        list_position_dict (list[dict[str, list[list[int]]]]): List
        of dicts having the doc id as key and the PII positions as values.

    Returns:
        dict[str, list[list[int]]]: Combined Dict.
    """
    final_dict = {}

    for position_dict in list_position_dict:
        final_dict = final_dict | position_dict

    return final_dict


def save_text_from_docs(doc_json_path: str) -> None:
    """
    Reads the JSON containg the anyomization process as well
    as the text, extracts text and saves text with doc id as
    file name.

    Args:
        doc_json_path(str): Path to the JSON object.

    Returns:
        None.
    """
    with open(doc_json_path, "r") as f:
        doc_list = json.loads(f.read())

    for doc in doc_list:
        doc_id = doc["doc_id"]
        text = doc["text"]
        root_dir = utils.return_root_dir()
        with open(os.path.join(
            root_dir,
            "Data",
            "texts",
            f"{doc_id}.txt"
        ), "w") as f:
            f.write(text)
