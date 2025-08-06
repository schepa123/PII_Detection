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

nest_asyncio.apply()


async def main():
    """Main function to set up the argument parser and process the file."""
    cwd = os.path.realpath(os.path.join(
        os.getcwd(), os.path.dirname(__file__)
    ))
    root_dir = os.path.dirname(
        os.path.dirname(cwd)
    )
    log_dir = os.path.join(root_dir, "log")

    logger.remove()
    logger.add(
        os.path.join(log_dir, "app_{time:YYYY-MM-DD}.log"),
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
    API_KEY = os.getenv("API_KEY")
    MODEL_STATIC = os.getenv("MODEL_STATIC")
    MODEL_DYNAMIC = os.getenv("MODEL_DYNAMIC")
    MODEL_PROMPT_CREATER = os.getenv("MODEL_PROMPT_CREATER")
    BASE_URL = os.getenv("BASE_URL")
    TEMPERATURE = float(os.getenv("TEMPERATURE"))
    text = cli_helper.read_text_file(args.text_path)

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
    )
    print("Finished dynamic PIIs")

    print("Start static PIIs")
    cli_helper.extract_pii_static(
        text=text,
        api_key=API_KEY,
        base_url=BASE_URL,
        model_name=MODEL_STATIC,
        temperature=TEMPERATURE,
        conn=conn,
    )
    print("Finished static PIIs")

    conn.save_nodes_as_json(
        path=args.result_path,
    )



if __name__ == "__main__":
    asyncio.run(main())
