import argparse
import random
import os
import sys
import json
import asyncio
from dotenv import load_dotenv
from loguru import logger

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from src.module.llm import LLMAgent
from src.module import entities
from src.module import neo4j_conn
from src.module import llm_agents
from src.module import utils
from src.module import llm_agents_static
from src.evaluate import prepare_evaluation
from src.module.utils import extract_pii_dynamic as _sync_extract_pii_dynamic

load_dotenv()


def set_up_argparse():
    """Set up the argument parser."""
    parser = argparse.ArgumentParser(description="Start PII process.")
    parser.add_argument(
        "--input_path",
        type=str,
        required=True,
        help="Path to the input file or directory."
    )

    parser.add_argument(
        "--output_path",
        type=str,
        required=True,
        help="Path where the output should be saved."
    )

    parser.add_argument(
        "--n_text",
        type=str,
        required=True,
        help="Number of text to get."
    )

    parser.add_argument(
        "--refine",
        type=int,
        required=True,
        help="Whether to refine the prompts or not."
    )

    parser.add_argument(
        "--generate_new_prompt",
        type=int,
        required=True,
        help="Whether to create a new prompt at every step or not."
    )

    parser.add_argument(
        "--file",
        type=str,
        nargs="+",
        required=False,
        help="One or more files to process (space-separated)."
    )


    return parser


def create_paths(doc_id: str) -> tuple[str, str, str, str, str, str, str]:
    """
    Create paths for various files and folders used in the project.

    Parameters:
    ---------
    None

    Returns:
    -------
    tuple
        A tuple containing the paths for:
        - Handcrafted prompt folder
        - Folder to save generated prompts
        - Property YAML file path
        - Prompt configuration YAML file path
        - Guidelines for extracting path
        - Guidelines for issue solving path
    """
    file_path = os.path.dirname(__file__)

    prompt_handcrafted_folder = os.path.abspath(os.path.join(
        file_path,
        "../../prompts"
    ))
    prompt_folder_to_save = os.path.abspath(os.path.join(
        file_path,
        f"../../generated_prompts/{doc_id}"
    ))
    print(f"prompt_folder_to_save: {prompt_folder_to_save}")
    property_yml_file_path = os.path.abspath(os.path.join(
        file_path,
        "../../entity_description/properties.yml"
    ))
    prompt_config_yml_path = os.path.abspath(os.path.join(
        file_path,
        "../../prompts/prompt_config/generation_config.yml"
    ))
    guidelines_path_extracting = os.path.abspath(os.path.join(
        file_path,
        "../../prompts/meta_prompting/independent/guidelines_for_extracting.md"
    ))
    guidelines_path_issue = os.path.abspath(os.path.join(
        file_path,
        "../../prompts/meta_prompting/independent/guidelines_for_issue_solving.md"
    ))
    guidelines_path_verify = os.path.abspath(os.path.join(
        file_path,
        "../../prompts/meta_prompting/independent/guidelines_for_issue_solving.md"
    ))

    return (
        prompt_handcrafted_folder,
        prompt_folder_to_save,
        property_yml_file_path,
        prompt_config_yml_path,
        guidelines_path_extracting,
        guidelines_path_issue,
        guidelines_path_verify
    )


def create_folder_generated_prompts(
    prompt_folder_to_save: str
) -> None:
    """
    Creates the folers for the generate prompts.

    Args:
        prompt_folder_to_save (str): Location to where to save
        the prompts to.

    Returns:
        None.
    """
    if not os.path.exists(prompt_folder_to_save):
        os.makedirs(prompt_folder_to_save)
        os.makedirs(os.path.join(prompt_folder_to_save, "independent"))
        prompt_folder_to_save = os.path.join(
            prompt_folder_to_save,
            "independent"
        )
        os.makedirs(os.path.join(prompt_folder_to_save, "age_number"))
        os.makedirs(os.path.join(prompt_folder_to_save, "charges"))
        os.makedirs(os.path.join(prompt_folder_to_save, "code"))
        os.makedirs(os.path.join(prompt_folder_to_save, "court_case_name"))
        os.makedirs(os.path.join(
            prompt_folder_to_save, "Crime_Related_Circumstances")
        )
        os.makedirs(os.path.join(prompt_folder_to_save, "date"))
        os.makedirs(os.path.join(prompt_folder_to_save, "duration"))
        os.makedirs(os.path.join(prompt_folder_to_save, "facility"))
        os.makedirs(os.path.join(prompt_folder_to_save, "health"))
        os.makedirs(os.path.join(prompt_folder_to_save, "item"))
        os.makedirs(os.path.join(prompt_folder_to_save, "job_title"))
        os.makedirs(os.path.join(
            prompt_folder_to_save, "laws_legal_provisions_Name_Number")
        )
        os.makedirs(os.path.join(prompt_folder_to_save, "named_location"))
        os.makedirs(os.path.join(prompt_folder_to_save, "Nationality_Ethnicity"))
        os.makedirs(os.path.join(prompt_folder_to_save, "organization"))
        os.makedirs(os.path.join(prompt_folder_to_save, "political_stance"))
        os.makedirs(os.path.join(prompt_folder_to_save, "quantity"))
        os.makedirs(os.path.join(prompt_folder_to_save, "real_estate"))
        os.makedirs(os.path.join(prompt_folder_to_save, "realative_time"))


def read_text_file(file_path) -> str:
    """
    Read the content of a text file.

    Parameters:
    ---------
    file_path : str
        The path to the text file.

    Returns:
    -------
    str
        The content of the text file.
    """
    if not os.path.isfile(file_path):
        print(f"Error: {file_path} is not a valid file.")
        return None

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"An error occurred while reading the file: {e}")
        return None


def extract_pii_static(
    text: str,
    doc_id: str,
    api_key: str,
    base_url: str,
    model_name: str,
    temperature: float,
    conn: neo4j_conn.Neo4jConnection,
) -> None:
    """
    Extract PII using static methods.

    Parameters:
    ---------
    text : str
        The text from which to extract PII.
    doc_id : str
        The ID of the document.
    api_key : str
        The API key for the LLM.
    base_url : str
        The base URL for the LLM API.
    model_name : str
        The model name for the LLM.
    temperature : float
        The temperature for the LLM API.
    conn : neo4j_conn.Neo4jConnection
        The Neo4j connection object.

    Returns:
    -------
    None
    """
    utils.extract_pii_static(
        pii_name="Entity_designation",
        text=text,
        doc_id=doc_id,
        drop_category=True,
        prompt_folder=os.path.abspath(os.path.join(
            os.path.dirname(__file__),
            "../../prompts/recognize"
        )),
        model_name=model_name,
        temperature=temperature,
        api_key=api_key,
        base_url=base_url,
        conn=conn
    )


async def extract_pii_dynamic(
    text: str,
    doc_id: str,
    base_url: str,
    model_name_prompt_creater: str,
    model_name_meta_expert: str,
    api_key_prompt_creater: str,
    api_key_meta_expert: str,
    conn: neo4j_conn.Neo4jConnection,
    temperature: float,
    refine_prompts: bool,
    generate_new_prompt: bool
) -> None:
    """
    Extract PII using dynamic methods with a concurrency limit of 4.
    """
    # 1) Build local paths
    (
        prompt_handcrafted_folder,
        prompt_folder_to_save,
        property_yml_file_path,
        prompt_config_yml_path,
        guidelines_path_extracting,
        guidelines_path_issue,
        guidelines_path_verify
    ) = create_paths(doc_id=doc_id)

    create_folder_generated_prompts(
        prompt_folder_to_save=prompt_folder_to_save
    )

    # 2) Load PII definitions
    property_dict = utils.read_yaml(property_yml_file_path)

    # 3) Define concurrency limit
    semaphore = asyncio.Semaphore(19)

    async def sem_task(pii_name: str):
        async with semaphore:
            return await asyncio.to_thread(
                _sync_extract_pii_dynamic,
                pii_name=pii_name,
                category="independent",
                text=text,
                drop_category=True,
                prompt_handcrafted_folder=prompt_handcrafted_folder,
                prompt_folder_to_save=prompt_folder_to_save,
                model_name_prompt_creater=model_name_prompt_creater,
                model_name_meta_expert=model_name_meta_expert,
                api_key_prompt_creater=api_key_prompt_creater,
                api_key_meta_expert=api_key_meta_expert,
                property_yml_file_path=property_yml_file_path,
                prompt_config_yml_path=prompt_config_yml_path,
                guidelines_path_extracting=guidelines_path_extracting,
                guidelines_path_issue=guidelines_path_issue,
                guidelines_path_verify=guidelines_path_verify,
                conn=conn,
                generate_new_prompt=generate_new_prompt,
                refine_prompts=refine_prompts,
                temperature=temperature,
                base_url=base_url,
                doc_id=doc_id
            )

    # 4) Create and run tasks
    tasks = [
        asyncio.create_task(sem_task(pii_name))
        for pii_name in property_dict.keys()
    ]
    await asyncio.gather(*tasks)


def get_n_texts_random(
    path: str,
    seed: int,
    n: int
) -> list[dict]:
    """
    Loads file holding the documents and returns n randomely
    sampled texts.

    Args:
        path (str): Path to the the file holding the documents.
        seed (int): Seed for random.
        n (int): Number of documents to return.

    Returns:
        list[dict]: List of n elements with the documents.
    """
    random.seed(seed)
    with open(path, "r") as f:
        temp = json.load(f)

    return random.sample(temp, n)


def save_text_from_documents(
    document_list: list[dict],
    save_path: str
) -> None:
    """
    Takes the documen_list and saves every text from a document as a
    text file with doc_id as file_name.

    Args:
        document_list (list[dict]): List of documents
        save_path (str): Path where to save documents to.

    Returns:
        None.
    """
    for document in document_list:
        doc_id = document["doc_id"]
        text = document["text"]
        with open(os.path.join(save_path, f"{doc_id}.txt"), "w") as f:
            f.write(text)


async def run_pii(
    file_path: str,
    output_path: str,
    conn: neo4j_conn.Neo4jConnection,
    base_url: str,
    model_name_prompt_creater: str,
    model_name_meta_expert: str,
    api_key_prompt_creater: str,
    api_key_meta_expert: str,
    temperature: float,
    generate_new_prompt: bool,
    refine_prompts: bool
):
    """
    123
    """
    text = read_text_file(file_path)
    print(f"file_path for run_pii: {file_path}")    
    doc_id = file_path.split(".")[0].split("/")[-1]
    print(f"Start dynamic PIIs for doc: {doc_id}")
    await extract_pii_dynamic(
        text=text,
        base_url=base_url,
        model_name_prompt_creater=model_name_prompt_creater,
        model_name_meta_expert=model_name_meta_expert,
        api_key_prompt_creater=api_key_prompt_creater,
        api_key_meta_expert=api_key_meta_expert,
        conn=conn,
        temperature=temperature,
        refine_prompts=refine_prompts,
        generate_new_prompt=generate_new_prompt,
        doc_id=doc_id
    )
    print(f"Finished dynamic PIIs for doc_id: {doc_id}")
    print("Start static PIIs")
    extract_pii_static(
        text=text,
        doc_id=doc_id,
        api_key=api_key_prompt_creater,
        base_url=base_url,
        model_name=model_name_prompt_creater,
        temperature=temperature,
        conn=conn,
    )
    print("Finished static PIIs")
    result_path = os.path.join(
        output_path, f"{doc_id}.json"
    )
    conn.save_nodes_as_json(
        path=result_path,
        doc_id=doc_id
    )
    with open(result_path, "r") as f:
        nodes_json = json.load(f)

    position_dict = prepare_evaluation.locate_identifiers(
        nodes_json,
        original_text=text,
        doc_id=doc_id
    )
    position_path = os.path.join(
        output_path, f"{doc_id}_positions.json"
    )
    with open(position_path, "w") as f:
        json.dump(position_dict, f)

    temp_to_add = prepare_evaluation.add_regex_search(
        conn=conn,
        text_path=file_path,
        result_path=position_path,
        doc_id=doc_id
    )
    position_dict[doc_id].extend(temp_to_add)
    position_dict = prepare_evaluation.merge_overlapping_elements(
        position_dict
    )

    logger.info(f"Finished {doc_id}")
