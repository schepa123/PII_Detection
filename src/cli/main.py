import argparse
import os
import sys
import json
from dotenv import load_dotenv
from loguru import logger
import asyncio
import nest_asyncio
import cli_helper

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from src.module.llm import LLMAgent
from src.module import entities
from src.module import neo4j_conn
from src.module import llm_agents
from src.module import utils
from src.module import llm_agents_static
from src.evaluate import prepare_evaluation
nest_asyncio.apply()


async def main():
    """Main function to set up the argument parser and process the file."""
    # TODO: EINBAUEN, dass nach jedem Durchgang die Prompts gelöscht werden

    cwd = os.path.realpath(os.path.join(
        os.getcwd(), os.path.dirname(__file__)
    ))
    root_dir = os.path.dirname(
        os.path.dirname(cwd)
    )
    log_dir = os.path.join(root_dir, "log")

    logger.remove()
    logger.add(
        os.path.join(log_dir, "Baum_pp_{time:YYYY-MM-DD}.log"),
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        level="DEBUG"
    )

    load_dotenv()
    logger.info("Loading environment variables")
    parser = cli_helper.set_up_argparse()
    args = parser.parse_args()
    conn = neo4j_conn.Neo4jConnection(
        uri="bolt://neo4j:7687",
        user="neo4j",
        pwd="neo4jneo4j"
    )
    conn.query(query="""MATCH (n) DETACH DELETE n""")
    API_KEY = os.getenv("API_KEY")
    MODEL_STATIC = os.getenv("MODEL_STATIC")
    SEED = os.getenv("SEED")
    MODEL_DYNAMIC = os.getenv("MODEL_DYNAMIC")
    MODEL_PROMPT_CREATER = os.getenv("MODEL_PROMPT_CREATER")
    BASE_URL = os.getenv("BASE_URL")
    TEMPERATURE = float(os.getenv("TEMPERATURE"))

    texts_path = os.path.join(root_dir, "Data", "texts")
    output_path = os.path.join(
        root_dir,
        "Output"
    )
    files = [
        f for f in os.listdir(texts_path)
        if os.path.isfile(os.path.join(texts_path, f))
    ]

    # TODO: Das machen wir anders, wir schauen uns jede einzelne
    # Datei einzeln an
    for file in files:
        text = cli_helper.read_text_file(os.path.join(
            texts_path,
            file
        ))
        doc_id = file.split(".")[0]

        print("Start dynamic PIIs")
        await cli_helper.extract_pii_dynamic(
            text=text,
            base_url=BASE_URL,
            model_name_prompt_creater=MODEL_PROMPT_CREATER,
            model_name_meta_expert=MODEL_DYNAMIC,
            api_key_prompt_creater=API_KEY,
            api_key_meta_expert=API_KEY,
            conn=conn,
            temperature=TEMPERATURE,
            refine_prompts=False
        )
        print("Finished dynamic PIIs")

        # merge_overlapping_elements EINBAUEN

        print("Start static PIIs")
        #cli_helper.extract_pii_static(
        #    text=text,
        #    api_key=API_KEY,
        #    base_url=BASE_URL,
        #    model_name=MODEL_STATIC,
        #    temperature=TEMPERATURE,
        #    conn=conn,
        #)
        print("Finished static PIIs")

        result_path = os.path.join(
            output_path, f"{doc_id}.json"
        )

        conn.save_nodes_as_json(
            path=result_path
        )

        with open(result_path, "r") as f:
            nodes_json = json.load(f)

        position_dict = prepare_evaluation.locate_identifiers(
            nodes_json,
            original_text=text,
            doc_id=doc_id
        )
        print(position_dict)

        with open(os.path.join(
            output_path, f"{doc_id}_positions.json"
        ), "w") as f:
            json.dump(
                position_dict, f
            )

        logger.info(f"Finished {file}")

    position_files = [
        f for f in os.listdir(output_path)
        if os.path.isfile(os.path.join(output_path, f))
    ]

    position_dict_list = []
    for file in position_files:
        if not file.endswith("_positions.json"):
            continue
        with open(os.path.join(output_path, file), "r") as f:
            position_dict_list.append(
                json.load(f)
            )

    with open(os.path.join(output_path, "final.json"), "w") as f:
        json.dump(
            prepare_evaluation.combine(position_dict_list), f
        )




if __name__ == "__main__":
    asyncio.run(main())
