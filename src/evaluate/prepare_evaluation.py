import re
import uuid
import json
import os
import sys
sys.path.append(os.path.abspath('..'))
from src.module import utils
from src.cli import cli_helper


# Mach das Programm auf ein Dokument, runne locate_identifiers und speichere das Ergebnis wo ab und am Ende combine alles.


def _replace_characters(text: str) -> str:
    """
    Replaces instances of characters that the LLM doesn't use.

    Args:
        text (str): String to modify

    Returns:
        str: Modified string.
    """
    return (
        text
        .replace('“', '"')
        .replace('”', '"')
        .replace('’', "'")
        .replace('\u00A0', ' ')        # NBSP -> space
        .replace('\u00AD', '')         # soft hyphen
    )


def _build_flexible_context_regex(context: str) -> re.Pattern:
    _BETWEEN = r'(?:[\s,.;:!?()"\'' + "’“”" + r'\-–—]*?)'  # non-greedy
    ctx = _replace_characters(context)
    # words = sequences of letters/digits/underscore + Unicode letters
    tokens = re.findall(r'\w+', ctx, flags=re.UNICODE)
    if not tokens:
        # fallback to escaped literal if we somehow got no tokens
        return re.compile(re.escape(ctx), flags=re.IGNORECASE)
    pattern = r'\b' + _BETWEEN.join(map(re.escape, tokens)) + r'\b'
    return re.compile(pattern, flags=re.IGNORECASE)


def _build_verbatim_matcher(extracted: str) -> re.Pattern:
    parts = []
    for ch in extracted:
        if ch in {"'", "’"}:
            parts.append(r"(?:'|’)")
        elif ch in {'"', '“', '”'}:
            parts.append(r'(?:"|“|”)')
        elif ch in {'-', '–', '—'}:
            parts.append(r"(?:-|–|—)")
        elif ch == "\u00A0" or ch.isspace():  # space, tab, newline, NBSP
            parts.append(r"(?:\s|\u00A0)+")
        else:
            parts.append(re.escape(ch))
    pattern = "".join(parts)
    return re.compile(pattern, flags=re.IGNORECASE)


def _remove_first_last_character(text: str) -> str:
    """
    Removes the first and last characters of a string. This is
    done because the LLM sometimes makes mistakes in the first
    and last character.

    Args:
        text (str): String to modify

    Returns:
        str: Modified string.
    """
    return text[:-1][1:]


def locate_identifiers(
    pii_json: list[dict[str, str]],
    original_text: str,
    doc_id: str
) -> dict[str, list[list[int]]]:
    """
    Takes the JSON object containing the PIIs and their context
    and returns a list of list containing the starting and end
    position of a PII.
    """
    results: list[dict] = []
    position_list: list[dict[str, list[int]]] = []

    # Normalize source text (no '.' -> ','); also fix NBSP/soft hyphen
    original_text = _replace_characters(original_text).\
        replace("\u00A0", " ").\
        replace("\u00AD", "")

    for rec in pii_json:
        if "abbreviations" in rec:
            name_patterns: list[re.Pattern] = []
            full_name = rec.get("full_name")
            if full_name:
                # Escape unless you intentionally expect regex
                name_patterns.append(
                    re.compile(re.escape(full_name), flags=re.IGNORECASE)
                )

            for abbr in rec.get("abbreviations", []) or []:
                if not abbr:
                    continue
                name_patterns.append(
                    re.compile(re.escape(abbr), flags=re.IGNORECASE)
                )

            for alias in rec.get("aliases", []) or []:
                if (
                    not alias
                    or alias.lower() in {"applicant", "the applicant"}
                ):
                    continue
                name_patterns.append(
                    re.compile(re.escape(alias), flags=re.IGNORECASE)
                )

            for pat in name_patterns:
                for m in pat.finditer(original_text):
                    results.append({
                        "uuid": rec.get("uuid"),
                        "found": m.group(0),
                        "start": m.start(),
                        "end": m.end()
                    })
            continue

        identifier = (rec.get("identifier") or "").strip()
        if not identifier:
            continue

        context = rec.get("context") or ""
        context_re = _build_flexible_context_regex(context)
        context_m = context_re.search(original_text)

        if context_m:
            context_start, context_end = context_m.span()
            ident_norm = _replace_characters(identifier)
            id_re = re.compile(re.escape(ident_norm), flags=re.IGNORECASE)
            for m in id_re.finditer(original_text[context_start:context_end]):
                abs_start = context_start + m.start()
                abs_end = context_start + m.end()
                results.append({
                    "uuid": rec.get("uuid"),
                    "found": m.group(),
                    "start": abs_start,
                    "end": abs_end
                })
        else:
            ident_norm = _replace_characters(identifier)
            id_re = re.compile(re.escape(ident_norm), flags=re.IGNORECASE)
            any_hit = False
            for m in id_re.finditer(original_text):
                any_hit = True
                results.append({
                    "uuid": rec.get("uuid"),
                    "found": m.group(),
                    "start": m.start(),
                    "end": m.end()
                })
            if not any_hit:
                print(f"Context not found for uuid {rec.get('uuid')!r}")

    for r in results:
        position_list.append({r["uuid"]: [r["start"], r["end"]]})

    return {doc_id: position_list}


def merge_overlapping_elements(
    position_dict: dict[str, list[int]]
) -> dict[str, list[int]]:
    """
    Merges overlapping position ranges if the left element of
    one entry is smaller than the left element of another and
    the right element is the same.

    Args:

    """
    key = list(position_dict.keys())[0]
    position_list = position_dict[key]
    best_left_for_right = {}

    for pair in position_list:
        left, right = pair

        if right in best_left_for_right:
            if left < best_left_for_right[right]:
                best_left_for_right[right] = left
        else:
            best_left_for_right[right] = left
    merged = [[left, right] for right, left in best_left_for_right.items()]
    merged.sort(key=lambda x: (x[1], x[0]))
    return {key: merged}


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


def add_regex_search(
    conn,
    texts_path,
    result_path
):
    positions_to_add = []
    query = """
    MATCH (n)
    WHERE n:Nationality_Ethnicity OR n:Facility OR n:Organization OR n:Named_Location
    RETURN n;
    """
    query_result = conn.query(query=query)
    temp = []
    identifiers = []
    for data in query_result:
        temp.append(next(iter(data.data().values())))
    identifiers = list(set([element["identifier"] for element in temp]))
    files = [
        f for f in os.listdir(texts_path)
        if os.path.isfile(os.path.join(texts_path, f))
    ]

    # For loop über alle Dokumente in /Data/texts/
    for file in files:
        text = cli_helper.read_text_file(os.path.join(
            texts_path,
            file
        ))
        text = _replace_characters(text).\
            replace("\u00A0", " ").\
            replace("\u00AD", "")
        results = []

        with open(result_path, "r") as f:
            nodes_json = json.load(f)
        list_position_llm = nodes_json[list(nodes_json.keys())[0]]

        for ident in identifiers:
            print(ident)
            regex_ident = _build_flexible_context_regex(ident)
            search_result = regex_ident.search(text)
            start, end = search_result.span()
            results.append({
                "start": start,
                "end": end
            })

        for element in results:
            temp_position = [element["start"], element["end"]]
            if temp_position not in list_position_llm:
                positions_to_add.append({
                    str(uuid.uuid4()): temp_position
                })

    return positions_to_add