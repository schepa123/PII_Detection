import uuid
import os
from openai import OpenAI
import re
import json
import pprint
from typing import Union
import yaml
import asyncio
import textwrap
from loguru import logger


from .llm import LLMAgent
from .neo4j_conn import Neo4jConnection
from . import utils


class MetaExpertConversation():
    """
    Handles the conversation with the meta expert
    """
    def __init__(
        self,
        agent: LLMAgent,
        text: str,
        prompt_folder: str,
        conn: Neo4jConnection,
        doc_id: str
    ):
        self.agent = agent
        self.text = text
        self.conn = conn
        self.doc_id = doc_id
        self.prompt_folder = prompt_folder
        self.proposed_solutions = []
        self.verify_solutions = []

        self.conversation_list = []
        self.responses = []
        self.step_queue = []
        self.generated_prompts = {
            "extracting": None,
            "verifying": None,
            "issue": None
        }
        self.load_generated_prompts()
        self.load_meta_prompts()

    def load_generated_prompts(
        self
    ) -> None:
        """
        Takes the generated prompts from the folder and loads them into
        the generated_prompts dictionary

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        file_path = os.path.join(
            self.prompt_folder,
            "extracting"
        )

        for file in os.listdir(file_path):
            file_type = file.split("_")[1].split(".")[0]
            file_name = os.path.join(file_path, file)
            with open(file_name, "r") as f:
                self.generated_prompts[file_type] = f.read()

    def load_meta_prompts(
        self
    ) -> None:
        """
        Takes the meta prompts from the folder and saves them as class
        variables

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        file_path = os.path.join(
            self.prompt_folder,
            "meta_prompting"
        )

        with open(os.path.join(file_path, "meta_expert.md"), "r") as f:
            self.meta_expert_prompt = f.read()
        with open(os.path.join(file_path, "next_step_meta.md"), "r") as f:
            self.next_step_meta_prompt = f.read()

    def read_persons(self) -> str:
        """
        Reads the persons from the database and returns them as a JSON string

        Parameters
        ----------
        None

        Returns
        -------
        str
            The persons as a JSON string
        """

        query = f"""
        MATCH (designation:Entity_designation)
        WHERE designation.doc_id = {self.doc_id}
        RETURN designation
        """
        result = self.conn.query(query)

        person_dict = {}
        for person in result:
            person_dict[person["designation"].get("uuid")] = {
                "full name": person["designation"].get("name"),
                "abbrevations": person["designation"].get("abbrevation"),
                "alias": person["designation"].get("nick_name_alias"),
            }

        return json.dumps(person_dict)

    def start_conversation(
        self
    ) -> None:
        """
        Starts the conversation with the meta expert by sending the
        meta expert prompt.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        prompt = """
        Start the conversation!
        """
        conversation_list = [{"role": "user", "content": self.text}]
        reponse_temp = self.agent.send_prompt(
            developer_prompt=self.meta_expert_prompt,
            conversation_list=conversation_list
        )
        logger.info(
            textwrap.dedent("""Start of Conversation:
            --------------------------------
            """)
        )

    def add_uuid_to_person(
        self,
        response: str = None
    ) -> list[dict[str, dict[list[str], list[str], list[str]]]]:
        """
        Takes the person information and adds a UUID to it

        Parameters
        ----------
        response : str
            The response from the LLM

        Returns
        -------
        list[str, dict[list[str], list[str], list[str]]]
            The person information with the UUID added
        """
        person_dict = {}
        if response is not None:
            response_temp = response
        else:
            response_temp = self.responses[-1]
        json_object = self.agent._extract_json_from_response(
            response_temp
        )
        for person_dict_single in json_object["Persons"]:
            person_dict[str(uuid.uuid4())[:16]] = person_dict_single

        return person_dict

    def extract_individuals(
        self
    ):
        """
        Takes the text and extracts the individuals from it

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        person_dict = self.read_persons()
        user_prompt = textwrap.dedent(f"""
        <person_dict>{person_dict}</person_dict>
        <text>{self.text}</text>
        """)
        conversation_list = [{"role": "user", "content": user_prompt}]

        response = self.agent.send_prompt(
            developer_prompt=self.generated_prompts["extracting"],
            conversation_list=conversation_list
        )

        logger.info(
            textwrap.dedent("""
            Extraction Response:\n
            {response}
            --------------------------------
            """), response=response
        )

        self.responses.append(response)
        person_dict = self.add_uuid_to_person()
        self.proposed_solutions.append(person_dict)
        self.add_next_step_meta_to_conversation(
            json.dumps(person_dict)
        )

    async def send_solutions_for_verification(
        self
    ) -> list[dict[str, dict[str, str]]]:
        """
        Sends every solution individually to LLM for examination

        Parameters
        ----------

        Returns
        -------
        list[str]
            The responses from the LLM
        """
        tasks = []

        async with asyncio.TaskGroup() as tg:
            for key, value in self.proposed_solutions[-1].items():
                user_prompt = f"""
                <proposed_solution> {{{key}: {value}}} <proposed_solution>
                <text>{self.text}</text>
                """
                conversation_list = [{"role": "user", "content": user_prompt}]
                task = tg.create_task(self.agent.send_prompt_async(
                    developer_prompt=self.generated_prompts["verifying"],
                    conversation_list=conversation_list
                ))
                tasks.append(task)

        results = [task.result() for task in tasks]
        return results

    def process_verification_results(
        self,
        response: list[str]
    ):
        """
        reponse: str
            The response from the LLM regarding the verification
        """
        verification_results = [
            self.agent._extract_json_from_response(result)
            for result in response
        ]
        combined_results = {}
        for result in verification_results:
            combined_results.update(result)
        proposed_solution_temp = self.proposed_solutions[-1]

        for key in combined_results.keys():
            temp_dict = proposed_solution_temp[key]
            try:
                combined_results[key]["full name"] = temp_dict["full name"]
            except KeyError:
                combined_results[key]["full name"] = temp_dict["full_name"]
            combined_results[key]["abbreviations"] = temp_dict["abbreviations"]
            combined_results[key]["aliases"] = temp_dict["aliases"]

        return json.dumps(combined_results)

    def verify_solution(self) -> None:
        """
        Verifies the solution by sending it to the LLM and processing the
        response

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        results = asyncio.run(self.send_solutions_for_verification())
        logger.info(f"Verification response: \n\n'{results}'")

        verified_solutions = self.process_verification_results(results)
        logger.info(
            textwrap.dedent("""
            Verified Solutions:\n
            {verified_solutions}
            --------------------------------
            """), verified_solutions=verified_solutions
        )
        self.verify_solutions.append(verified_solutions)
        self.add_next_step_meta_to_conversation(verified_solutions)

    def categorize_solutions(
        self
    ) -> list[dict[str, dict[str, bool, str, str]]] | list[dict[str, dict[str, bool, str, str]]]:
        """
        Categorizes the solutions into correct and incorrect solutions

        Parameters
        ----------
        verify_results : str
            The results from the verification prompt

        Returns
        -------
        tuple[dict, dict]
            The correct and incorrect solutions
        """
        wrong_solutions = {}
        correct_solutions = {}
        temp_dict = json.loads(self.verify_solutions[-1])
        for key, value in temp_dict.items():
            if value["bool"]:
                value.pop("reasoning", None)
                value.pop("bool", None)
                correct_solutions[key] = value
            else:
                wrong_solutions[key] = value

        return correct_solutions, wrong_solutions

    def send_issue_prompt(
        self,
        correct_solutions,
        wrong_solutions
    ) -> str:
        issue_prompt = self.generated_prompts["issue"]
        user_prompt = f"""
        <text>{self.text}</text>
        <correct_solution>{json.dumps(correct_solutions)}</correct_solution>
        <wrong_solution>{json.dumps(wrong_solutions)}</wrong_solution>
        """
        conversation_list = [{"role": "user", "content": user_prompt}]

        reponse = self.agent.send_prompt(
            developer_prompt=issue_prompt,
            conversation_list=conversation_list
        )
        logger.info(
            "Response:\n {reponse}\n-----------------",
            reponse=reponse
        )
        return reponse

    def solve_issues(self):
        """
        Solves the issues with the generated prompt and
        adds the correct_solutions and newly found solutions
        to the proposed_solutions list

        Parameters
        ----------
        None

        Returns
        -------
        None
        """

        correct_solutions, wrong_solutions = self.categorize_solutions()
        results = self.send_issue_prompt(
            correct_solutions=correct_solutions,
            wrong_solutions=wrong_solutions
        )
        final_result = correct_solutions

        uuid_dict = self.add_uuid_to_person(results)
        if uuid_dict:
            for key, value in uuid_dict.items():
                final_result.update({key: value})

        self.proposed_solutions.append(final_result)
        final_result = json.dumps(final_result)
        self.add_next_step_meta_to_conversation(final_result)

    def add_to_conversation_list(
        self,
        role: str,
        content: str
    ) -> None:
        """
        Adds the role and content to the conversation list

        Parameters
        ----------
        role : str
            The role in the conversation
        content : str
            The content of the conversation (response or prompt)

        Returns
        -------
        None
        """
        self.conversation_list.append(
            {"role": role, "content": content}
        )
        logger.info(
            textwrap.dedent("""Added to conversation list:
            {role}:\n\n{content}
            --------------------------------
            """),
            role=role,
            content=content
        )

    def add_next_step_meta_to_conversation(
        self,
        response: str
    ) -> None:
        """
        Fill the next step meta prompt with the previous action and the
        response and add it to the conversation list

        Parameters
        ----------
        response : str
            The response from the meta expert

        Returns
        -------
        None
        """
        previous_action = self.step_queue[-1]["Next"]
        prompt = self.next_step_meta_prompt
        prompt = prompt \
            .replace("{{previous_action}}", previous_action) \
            .replace("{{response}}", response)

        self.add_to_conversation_list(
            role="user", content=prompt
        )

    def end_conversation(
        self
    ) -> dict:
        """
        After the conversation is done, the final verification results
        are returned

        Parameters
        ----------
        None

        Returns
        -------
        dict
            The final verification results
        """
        # If the verification is not done, somewrong happend
        # and we should return an empty dict
        if not self.verify_solutions:
            return {}
        return self.proposed_solutions[-1]

    def take_next_step(
        self
    ):
        """
        Takes the last step from the step queue and executes it

        Returns
        -------
        None
        """
        next_step = self.step_queue[-1]["Next"]
        print(f"Taking action: {next_step}")
        match next_step:
            case "extracting":
                self.extract_individuals()
            case "verification":
                self.verify_solution()
            case "issues_solving":
                self.solve_issues()
            case "end":
                return self.end_conversation()
            case _:
                raise ValueError("Invalid next step")

    def extract_next_step(
        self,
        response: str
    ) -> str:
        """
        Extract the next step from the meta expert

        Parameters
        ----------
        response : str
            The response from the meta expert

        Returns
        -------
        str
            The next step
        """
        patterns = [
            r'(\{"Next":\s?"\w+"\})',
            r"(\{'Next':\s?'\w+'\})"
        ]

        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                return match.group(1)
        raise ValueError(
            f"No next step found in response:\n\n{response}"
        )

    def generate_next_step(
        self
    ) -> None:
        """
        Takes the last response and decides the next step
        based on the meta expert response

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        if not self.step_queue:
            prompt = """
            Start the conversation!
            """
            conversation_list = [{"role": "user", "content": prompt}]
        else:
            conversation_list = self.conversation_list
        reponse_temp = self.agent.send_prompt(
            developer_prompt=self.meta_expert_prompt,
            conversation_list=conversation_list
        )
        logger.info(
            "Conv list: {conversation_list}\n-----------------",
            conversation_list=self.conversation_list
        )
        logger.info(
            "Response: {reponse_temp}\n-----------------",
            reponse_temp=reponse_temp
        )
        try:
            next_step = json.loads(self.extract_next_step(reponse_temp))
            self.step_queue.append(next_step)
        except json.JSONDecodeError:  # Sometimes the LLM uses single quotes
            reponse_temp = reponse_temp.replace("'", '"')
            next_step = json.loads(self.extract_next_step(reponse_temp))
            self.step_queue.append(next_step)

        logger.info(
            "Next Step: {next_step}\n-----------------", next_step=next_step
        )

        if self.step_queue[-1]["Next"] != "end":
            # content_temp = json.dumps(
            #    self.agent._extract_json_from_response(reponse_temp)
            # )
            self.add_to_conversation_list(
                role="assistant", content=f"Next step: {next_step}"
            )
        else:
            self.add_to_conversation_list(
                role="assistant", content=reponse_temp
            )

    def conversation_loop(
        self
    ):
        """
        Handles the conversation with the meta expert

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.generate_next_step()
        while self.step_queue[-1]["Next"] != "end":
            self.take_next_step()
            self.generate_next_step()

        result = self.take_next_step()
        #result.pop("bool", None)
        #result.pop("reasoning", None)

        return result


class ResultCorrecter():
    """
    A class used to correct the result of the LLM
    for extraction of individuals

    Attributes
    ----------
    agent : LLMAgent
        The LLM agent
    prompt_folder : str
        The folder where the prompt is stored
    conn : Neo4jConnection
        The connection to the Neo4j database
    correction_prompt : str
        The prompt for the correction
    response : dict
        The response from the LLM
    doc_id : str
        The ID of the document.
    """
    def __init__(
        self,
        agent: LLMAgent,
        prompt_folder: str,
        conn: Neo4jConnection,
        doc_id: str
    ):
        self.agent = agent
        self.conn = conn
        self.prompt_folder = prompt_folder
        self.response = None
        self.doc_id = doc_id
        self.load_correction_prompt()

    def load_correction_prompt(self) -> None:
        """
        Takes the generated prompts from the folder and loads them into
        the generated_prompts dictionary

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        file_path = os.path.join(
            self.prompt_folder,
            "database",
            "condense.md"
        )

        with open(file_path, "r") as f:
            self.correction_prompt = f.read()

    def send_prompt(self) -> dict[str, dict[str, str, str]]:
        """
        Takes the individuals from the database and sends them to the LLM
        for correction. The response is saved in the response variable
        with format

        {
            "uuid": {
                "full name": str,
                "abbreviations": str,
                "aliases": str
            }
        }

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        conversation_list = [{
            "role": "user",
            "content": f"<person_dict>{self.conn.read_persons(self.doc_id)}</person_dict>"
        }]
        response_temp = self.agent.send_prompt(
            developer_prompt=self.correction_prompt,
            conversation_list=conversation_list
        )
        self.response = self.agent._extract_json_from_response(
            response_temp
        )

    def load_result_in_database(self) -> None:
        """
        Drops the Entity_designation category and recreates the nodes
        with the corrected information

        Parameters
        ----------
        None

        Returns
        -------
        None

        """
        self.conn.drop_node_category(
            category="Entity_designation",
            doc_id=self.doc_id
        )
        self.conn.create_nodes_individual(
            result=self.response,
            doc_id=self.doc_id
        )

    def correct_result(self) -> None:
        """
        Corrects the result from the LLM

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.send_prompt()
        self.load_result_in_database()
