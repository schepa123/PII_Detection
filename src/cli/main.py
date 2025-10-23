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
    SEED = int(os.getenv("SEED"))
    MODEL_DYNAMIC = os.getenv("MODEL_DYNAMIC")
    MODEL_PROMPT_CREATER = os.getenv("MODEL_PROMPT_CREATER")
    BASE_URL = os.getenv("BASE_URL")
    TEMPERATURE = float(os.getenv("TEMPERATURE"))

    documents = cli_helper.get_n_texts_random(
        path=args.input_path,
        seed=SEED,
        n=int(args.n_text)
    )
    cli_helper.save_text_from_documents(
        document_list=documents,
        save_path=args.output_path
    )

    files = [
        f for f in os.listdir(args.output_path)
        if os.path.isfile(os.path.join(args.output_path, f))
    ]

    sem = asyncio.Semaphore(3)

    async def sem_task(file_name):
        async with sem:
            file_path = os.path.join(args.output_path, file_name)
            return await cli_helper.run_pii(
                file_path=file_path,
                output_path=args.output_path,
                conn=conn,
                base_url=BASE_URL,
                model_name_prompt_creater=MODEL_PROMPT_CREATER,
                model_name_meta_expert=MODEL_DYNAMIC,
                api_key_prompt_creater=API_KEY,
                api_key_meta_expert=API_KEY,
                temperature=TEMPERATURE,
                refine_prompts=True,
            )

    # Run all PII tasks with concurrency cap of 3
    await asyncio.gather(*(sem_task(f) for f in files))
    logger.info("All files processed.")



if __name__ == "__main__":
    asyncio.run(main())
