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
from src.module.utils import extract_pii_dynamic as _sync_extract_pii_dynamic

load_dotenv()

def set_up_argparse():
    """Set up the argument parser."""
    parser = argparse.ArgumentParser(description="Process a text file.")
    parser.add_argument(
        "text_path", type=str, help="Path to the text file to process"
    )
    parser.add_argument(
        "result_path", type=str, help="Path to the JSON file to save results"
    )

    return parser


def create_paths() -> tuple[str, str, str, str, str, str, str]:
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
        "../../generated_prompts"
    ))
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
    base_url: str,
    model_name_prompt_creater: str,
    model_name_meta_expert: str,
    api_key_prompt_creater: str,
    api_key_meta_expert: str,
    conn: neo4j_conn.Neo4jConnection,
    temperature: float,
    refine_prompts: bool
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
    ) = create_paths()

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
                refine_prompts=refine_prompts,
                temperature=temperature,
                base_url=base_url,
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