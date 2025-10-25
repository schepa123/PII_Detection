import uuid
import os
from openai import OpenAI
import re
import json
import pprint
from typing import Union
import yaml
from loguru import logger
from .llm import LLMAgent
from .neo4j_conn import Neo4jConnection
from . import llm_agents_static
from . import llm_agents



def get_cwd() -> str:
    """
    Returns the current working directory.

    Args:
        None.

    Returns:
        str: The current working directory.
    """
    return os.path.realpath(os.path.join(
        os.getcwd(), os.path.dirname(__file__)
    ))


def return_root_dir() -> str:
    """
    Returns the root directory of the project.

    Args:
        None.

    Returns:
        str: The root directory of the project.
    """
    path = get_cwd()
    return os.path.dirname(
        os.path.dirname(path)
    )


def get_property_information(
    yml: dict,
    pii_name: str = None
) -> dict:
    """
    Gets the property information from the YAML file

    Parameters
    ----------
    yml : dict
        The dict from the YAML file
    pii_name : str
        The name of the PII

    Returns
    -------
    dict
        The property dict
    """
    return {pii_name: yml[pii_name]}


def read_yaml(yml_file: str) -> dict:
    """
    Reads a YAML file and returns the content as a dictionary

    Parameters
    ----------
    yml_file : str
        The path to the YAML file
    """
    with open(yml_file, 'r') as file:
        return yaml.safe_load(file)


def read_prompt(
    prompt_folder,
    prompt_supercategory: str,
    prompt_subcategory: str,
    prompt_file_name: str
) -> str:
    """
    Reads a prompt from a file

    Parameters
    ----------
    prompt_folder: str
        The folder where the prompts are stored
    prompt_supercategory: str
        The supercategory of the prompt
    prompt_subcategory: str
        The subcategory of the prompt (general,
        independent, inviduals or organizations)
    prompt_name : str
        The name of the prompt

    Returns
    -------
    str
        The prompt
    """
    prompt_path = os.path.join(
        prompt_folder,
        prompt_supercategory,
        prompt_subcategory,
        prompt_file_name
    )

    with open(prompt_path, "r") as file:
        prompt = file.read()

    return prompt


def set_prompts_argument(
    prompt_folder: str,
    prompt_config_yml: dict
) -> dict:
    """
    Creates a dict with the prompt name and the prompt text

    Parameters
    ----------
    prompt_config_yml : dict
        The prompts to set

    Returns
    -------
    None
    """
    prompt_dict = {
        "meta_prompting": {
            "general": {},
            "independent": {},
            "individuals": {},
            "organisations": {}
        },
        "linking": {}
    }
    for super_category, sub_category_dict in prompt_config_yml.items():
        for sub_category_name, name_list in sub_category_dict.items():
            for prompt_config_dict in name_list:
                prompt_name = list(prompt_config_dict.keys())[0]
                prompt_file_name = prompt_config_dict[prompt_name]
                prompt_text = read_prompt(
                    prompt_folder=prompt_folder,
                    prompt_supercategory=super_category,
                    prompt_subcategory=sub_category_name,
                    prompt_file_name=prompt_file_name,
                )
                (prompt_dict[super_category][sub_category_name]
                 [prompt_name]) = prompt_text

    return prompt_dict


def check_if_file_exists(
    prompt_folder_to_save: str,
    category: str,
    pii_name: str,
    type: str,
    file_ending: str = "md"
) -> bool:
    """
    Checks if file exists

    Parameters
    ----------
    prompt_folder_to_save: str
        The folder where the files are saved
    category: str
        The category of the PII
    pii_name : str
        The name of the PII
    file_ending : str
        The file ending to use
    type: str
        The type of the prompt (extracting,
        verifiying, issue_solving)

    Returns
    -------
    bool
        True if the file exists, False otherwise
    """
    file_path = os.path.join(
        prompt_folder_to_save,
        category,
        pii_name,
        f"{pii_name}_{type}.{file_ending}",
    )
    return os.path.isfile(file_path)


def create_folder_to_save(
    prompt_folder_to_save: str,
    category: str,
    pii_name: str
) -> None:
    """
    Creates a folder to save files if it doesn't already exist.

    Parameters
    ----------
    prompt_folder_to_save: str
        The folder where the files are saved
    category: str
        The category of the PII
    pii_name : str
        The name of the PII

    Returns
    -------
    None
    """
    folder_path = os.path.join(
        prompt_folder_to_save,
        category,
        pii_name
    )
    try:
        os.makedirs(folder_path, exist_ok=True)
    except OSError as e:
        raise OSError(f"Error creating folder '{folder_path}': {e}")


def extract_information(
    text: str
) -> dict:
    """
    Extracts the information from the text

    Parameters
    ----------
    text : str
        The text to extract the information from

    Returns
    -------
    dict
        The information
    """
    pattern = r"\{'extracted_information': \[(.*?)\]\}"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        extracted_info = match.group(1)
        return json.loads(extracted_info)


def extract_instruction(
    text: str
):
    """
    Extracts the instructions from the text

    Parameters
    ----------
    text : str
        The text to extract the instructions from

    Returns
    -------
    dict
        The instructions
    """
    pattern = r'\{"job description": .*?\}'
    match = re.search(pattern, text, re.DOTALL)
    if match:
        extracted_info = match.group(0)
        return json.loads(extracted_info)


def split_text(
    text: str,
    paragraphs_to_merge: int = 2
) -> list[str]:
    """
    Splits the text into paragraphs and merges them
    into groups of paragraphs_to_merge

    Parameters
    ----------
    text : str
        The text to split
    paragraphs_to_merge : int
        The number of paragraphs to merge

    Returns
    -------
    list[str]
        The list of paragraphs
    """
    ignore_list = json.loads(os.environ['IGNORE_LIST'])
    text_splitted = text.split(sep="\n\n")
    text_splitted = [text for text in text_splitted if text not in ignore_list]
    text_splitted = [
        "\n\n".join(text_splitted[i:i+paragraphs_to_merge])
        for i in range(0, len(text_splitted), paragraphs_to_merge)
    ]

    return text_splitted


def extract_pii_static(
    pii_name: str,
    doc_id: str,
    text: str,
    drop_category: bool,
    prompt_folder: str,
    model_name: str,
    temperature: float,
    api_key: str,
    base_url: str,
    conn: Neo4jConnection,
) -> None:
    """
    Extracts PIIs from the text and creates nodes in the database
    by starting the conversation loop. This function handles
    manually crafted prompts and not dynamically generated ones.

    Parameters
    ----------
    pii_name : str
        The name of the PII
    doc_id : str
        The ID of the document.
    text : str
        The text to extract the PII from
    drop_category : bool
        If True, the category will be dropped in the database
    prompt_folder : str
        The folder where the prompts are stored
    model_name : str
        The name of the model to use
    temperature : float
        The temperature to use for the model
    api_key : str
        The API key to use
    conn : Neo4jConnection
        The connection to the Neo4j database
    Returns
    -------
    None
    """
    text_splitted = split_text(text)
    agent = LLMAgent(
        local=False,
        model_name=model_name,
        api_key=api_key,
        base_url=base_url,
        prompt_folder=None,
        temperature=temperature
    )
    correcter = llm_agents_static.ResultCorrecter(
        agent=agent,
        prompt_folder=prompt_folder,
        conn=conn,
        doc_id=doc_id
    )

    if drop_category:
        conn.drop_node_category(
            category=pii_name,
            doc_id=doc_id
        )

    for i, text in enumerate(text_splitted):
        print(f"Processing text {i + 1}/{len(text_splitted)}")
        logger.info(f"\n\nProcessing text: {text}")
        conv = llm_agents_static.MetaExpertConversation(
            agent=agent,
            text=text,
            prompt_folder=prompt_folder,
            conn=conn,
            doc_id=doc_id
        )
        result = conv.conversation_loop()
        if result:
            conn.create_nodes_individual(
                result=result,
                doc_id=doc_id
            )

    correcter.correct_result()


def extract_pii_dynamic(
    pii_name: str,
    category: str,
    text: str,
    doc_id: str,
    drop_category: bool,
    prompt_handcrafted_folder: str,
    prompt_folder_to_save: str,
    base_url: str,
    model_name_prompt_creater: str,
    model_name_meta_expert: str,
    api_key_prompt_creater: str,
    api_key_meta_expert: str,
    property_yml_file_path: str,
    prompt_config_yml_path: str,
    guidelines_path_extracting: str,
    guidelines_path_issue: str,
    guidelines_path_verify: str,
    conn: Neo4jConnection,
    refine_prompts=False,
    temperature: float = 0.5,
) -> None:
    """
    Extracts PIIs from the text and creates nodes in the database by starting
    the conversation loop. This function handles dynamically generated prompts.

    Parameters
    ----------
    pii_name : str
        The name of the PII
    category : str
        The category to select the prompts for
    text : str
        The text to extract the PII from
    doc_id : str
        ID of document
    drop_category : bool
        If True, the category will be dropped in the database
    prompt_handcrafted_folder : str
        The folder where the handcrafted prompts are stored
    prompt_folder_to_save : str
        The folder where the generated prompts are saved
    base_url : str
        The base URL of the API
    model_name_prompt_creater : str
        The name of the model to use for the prompt creator
    model_name_meta_expert : str
        The name of the model to use for the meta expert
    api_key_prompt_creater : str
        The API key to use for the prompt creator
    api_key_meta_expert : str
        The API key to use for the meta expert
    property_yml_file_path : str
        The path to the property YAML file
    prompt_config_yml_path : str
        The path to the prompt config YAML file
    guidelines_path_extracting : str
        The path to the guidelines for extracting
    guidelines_path_issue : str
        The path to the guidelines for issue solving
    guidelines_path_verify: str
        The path to the guidelines for verifying
    conn : Neo4jConnection
        The connection to the Neo4j database
    refine_prompts : bool
        If True, the prompts will be refined
    temperature : float
        The temperature to use for the model

    Returns
    -------
    None
    """
    if drop_category:
        conn.drop_node_category(
            pii_name,
            doc_id=doc_id
        )
    text_splitted = split_text(text)
    prompt_creater = llm_agents.PromptCreater(
        prompt_handcrafted_folder=prompt_handcrafted_folder,
        prompt_folder_to_save=prompt_folder_to_save,
        api_key=api_key_prompt_creater,
        base_url=base_url,
        model_name=model_name_prompt_creater,
        category=category,
        property_yml_file=property_yml_file_path,
        prompt_config_yml=prompt_config_yml_path,
        refine_prompts=refine_prompts,
        temperature=temperature
    )
    agent_independent = llm_agents.MetaPrompterIndependent(
        prompt_folder=prompt_handcrafted_folder,
        doc_id=doc_id,
        model_name=model_name_meta_expert,
        api_key=api_key_meta_expert,
        base_url=base_url,
        category=category,
        conn=conn,
        yml_file=property_yml_file_path,
        prompt_creater=prompt_creater,
        prompt_config_yml=prompt_config_yml_path,
        temperature=temperature
    )
    for i, text in enumerate(text_splitted):
        print(f"{pii_name}: Processing text {i+1}/{len(text_splitted)}")
        logger.info(f"\n\nProcessing text for {pii_name}: {text}")
        conv = llm_agents.MetaExpertConversationIndependet(
            agent=agent_independent,
            prompt_generator=prompt_creater,
            text=text,
            generated_prompt_folder=prompt_folder_to_save,
            generate_new_prompt=False,
            pii_name=pii_name,
            guidelines_path_extracting=guidelines_path_extracting,
            guidelines_path_issue=guidelines_path_issue,
            guidelines_path_verify=guidelines_path_verify,
            refine_prompts=refine_prompts
        )
        result = conv.conversation_loop()
        conn.create_nodes_pii_independent(
            pii=pii_name,
            result=result,
            doc_id=doc_id
        )