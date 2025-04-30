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


class PromptCreater(LLMAgent):
    def __init__(
        self,
        prompt_handcrafted_folder: str,
        prompt_folder_to_save: str,
        api_key: str,
        property_yml_file: str,
        prompt_config_yml: str,
        category: str,
        model_name: str = None,
        base_url: str = "https://api.openai.com/v1",
        temperature: float = 1.0,
        local: bool = False,
        refine_prompts: bool = False,
        **prompts
    ):
        super().__init__(
            local=local,
            prompt_folder=prompt_handcrafted_folder,
            model_name=model_name,
            temperature=temperature,
            api_key=api_key,
            base_url=base_url
        )
        self.yml = utils.read_yaml(property_yml_file)
        self.category = category
        self.refine_prompts = refine_prompts
        self.prompt_folder_to_save = prompt_folder_to_save
        prompt_config_yml = utils.read_yaml(prompt_config_yml)
        self.prompts = utils.set_prompts_argument(
            prompt_folder=self.prompt_folder,
            prompt_config_yml=prompt_config_yml
        )
        self.select_prompt_from_config(category=category)

    def select_prompt_from_config(
        self,
        category: str
    ) -> None:
        """
        Selects the prompts from the config file and sets
        them as attributes. Possible categories are:
        independent, individuals, organisations

        Parameters
        ----------
        category : str
            The category to select the prompts for

        Returns
        -------
        None
        """
        temp = self.prompts["meta_prompting"]
        self.prompt_feedback_generation = (
            temp["general"]["prompt_feedback_generation"]
        )
        self.prompt_incoporate_feedback = (
            temp["general"]["prompt_incoporate_feedback"]
        )
        self.prompt_generation = (
            temp[category]["prompt_generation"]
        )
        self.prompt_example_generation = (
            temp[category]["prompt_example_generation"]
        )
        self.prompt_verifying_generation = (
            temp[category]["prompt_verifying_generation"]
        )
        self.prompt_example_verifying_generation = (
            temp[category]["prompt_example_verifying_generation"]
        )
        self.prompt_issue_solving = (
            temp[category]["prompt_issue_solving"]
        )
        self.prompt_example_issue_generation = (
            temp[category]["prompt_example_issue_generation"]
        )
        self.examples_issue = (
            temp[category]["examples_issue"]
        )

    def save_prompt_to_file(
        self,
        prompt: str,
        pii_name: str,
        type: str,
        file_ending: str = "md"
    ) -> None:
        """
        Takes a prompt and saves it to a file

        Parameters
        ----------
        prompt : str
            The prompt to save
        pii_name : str
            The name of the pii
        type: str
            The type of the prompt (extracting, verifiying, issue_solving)
        file_ending : str
            The file ending to use

        Returns
        -------
        None
        """
        utils.create_folder_to_save(
            prompt_folder_to_save=self.prompt_folder_to_save,
            category=self.category,
            pii_name=pii_name
        )
        file_path = os.path.join(
            self.prompt_folder_to_save,
            self.category,
            pii_name,
            f"{pii_name}_{type}.{file_ending}",
        )
        try:
            with open(file_path, "w") as f:
                f.write(prompt)
            print(f"Prompt saved to '{file_path}'")
            logger.info(f"Prompt saved to '{file_path}'")
        except OSError as e:
            raise OSError(f"Error saving file '{file_path}': {e}")

    def return_prompt(
        self,
        type_prompt: str,
        example: bool = None
    ) -> str:
        """
        This function returns the desired prompt based on the type of prompt

        Parameters
        ----------
        type_prompt : str
            The type of prompt
        example : bool
            If the prompt is for an example

        Returns
        -------
        str
            The desired prompt
        """
        match type_prompt:
            case "extracting" if not example:
                return self.prompt_generation
            case "extracting" if example:
                return self.prompt_example_generation
            case "verifying" if not example:
                return self.prompt_verifying_generation
            case "verifying" if example:
                return self.prompt_example_verifying_generation
            case "issue" if not example:
                return self.prompt_issue_solving
            case "issue" if example:
                return self.examples_issue
            case "feedback":
                return self.prompt_feedback_generation
            case "incorporate":
                return self.prompt_incoporate_feedback

    def create_json_for_prompts_generation(
        self,
        pii_name: str,
        meta_expert_json: dict,
        guidelines_path: str = None,
    ) -> str:
        """
        This generates the JSON with information nesscarry
        for prompt generation

        Parameters
        ----------
        pii_name : str
            The name of the PII
        guidelines_path : str
            The path to the guidelines file
        meta_expert_json : dict
            The meta expert JSON
        text : str
            The text to generate the prompt for

        Returns
        -------
        str
            The JSON string
        """
        if guidelines_path is not None:
            with open(guidelines_path, "r") as f:
                guidelines = f.read()
        pii_dict = utils.get_property_information(
            yml=self.yml,
            pii_name=pii_name
        )
        prompt_json = {
            "job description": meta_expert_json["job description"],
            "instructions": meta_expert_json["instructions"],
            "pii": pii_name,
            "description of pii": (
                pii_dict[pii_name]["description"]
            ),
            "examples": (
                pii_dict[pii_name]["example"]
            )
        }

        if guidelines_path is not None:
            prompt_json["guidelines"] = guidelines

        return json.dumps(prompt_json)

    def create_prompt_from_instructions(
        self,
        instructions: dict,
        pii_name: str,
        type_prompt: str,
        guidelines_path: str = None
    ) -> str:
        """
        Takes the instructions from the meta expert and generates a prompt

        Parameters
        ----------
        instructions : dict
            Json with the instructions and role from the meta expert
        pii_name : str
            The name of the PII
        guidelines_path : str
            The path to the guidelines file

        Returns
        -------
        str
            The response from the meta expert
        """
        developer_prompt = self.return_prompt(type_prompt, example=False)
        prompt_args = {
            "pii_name": pii_name,
            "meta_expert_json": instructions,
        }

        if guidelines_path is not None:
            prompt_args["guidelines_path"] = guidelines_path
        prompt_json = self.create_json_for_prompts_generation(**prompt_args)
        response = self.send_prompt(
            developer_prompt=developer_prompt,
            conversation_list=[{"role": "user", "content": prompt_json}]
        )

        return self.process_feedback_loop(response)

    def create_examples_for_prompt(
        self,
        pii_name: str,
        generated_prompt: str,
        type_prompt: str
    ) -> str:
        """
        Takes a generated prompt and creates examples for it

        Parameters
        ----------
        pii_name : str
            The name of the PII
        generated_prompt : str
            The generated prompt

        Returns
        -------
        str
            The prompt with examples
        """
        if type_prompt != "issue":
            developer_prompt = self.return_prompt(type_prompt, example=True)

            example_list = utils.get_property_information(
                yml=self.yml,
                pii_name=pii_name
            )[pii_name]["example"]

            user_prompt = textwrap.dedent(f"""
            <prompt>{generated_prompt}</prompt>
            <example_list>{example_list}</example_list>
            """)

            response = self.send_prompt(
                developer_prompt=developer_prompt,
                conversation_list=[{"role": "user", "content": user_prompt}]
            )

            response = re.sub(
                r'\*\*Example Generation for the entries\*\*: ',
                '',
                response
            )

            final_prompt = textwrap.dedent(f"""
            {generated_prompt}
            ## Examples
            {response}
            """
            )
            logger.info(
                "response: {response}:",
                response=response
            )
        else:
            # TODO: Schau, dass du es irgendwie hinbekommst, dass die
            # Beispiele erstellt werden vom LLM, statt sie zu hardcoden
            examples = self.return_prompt(type_prompt, example=True)
            final_prompt = textwrap.dedent(f"""
            {generated_prompt}
            ## Examples
            {examples}
            """)

        return final_prompt

    def create_prompt_with_examples(
        self,
        instructions: str,
        pii_name: str,
        type_prompt: str,
        guidelines_path: str = None,
    ) -> str:
        """
        Takes the instructions from the meta expert and generates a prompt
        with examples

        Parameters
        ----------
        instructions : str
            The instructions from the meta expert
        pii_name : str
            The name of the PII
        guidelines_path : str
            The path to the guidelines file
        type_prompt : str
            The type of prompt

        Returns
        -------
        str
            The generated prompt with examples
        """
        prompt_args = {
            "instructions": instructions,
            "pii_name": pii_name,
            "type_prompt": type_prompt,
        }
        if guidelines_path is not None:
            prompt_args["guidelines_path"] = guidelines_path

        generated_prompt = self.create_prompt_from_instructions(**prompt_args)
        return self.create_examples_for_prompt(
            pii_name=pii_name,
            generated_prompt=generated_prompt,
            type_prompt=type_prompt
        )

    def check_score(
        self,
        text: str,
        cutoff: int = 8
    ) -> bool:
        """
        Checks the score of the text

        Parameters
        ----------
        text : str
            The text to check the score of
        cutoff : int
            The cutoff value

        Returns
        -------
        bool
            True if the score is above the cutoff, False otherwise
        """
        matches = re.findall(r'\b\d+/10\b', text)
        boolean_list = [
            True if int(match.split("/")[0]) >= cutoff else False
            for match in matches
        ]
        if all(t for t in boolean_list):
            return True
        return False

    def feedback_loop(
        self,
        generated_prompt
    ) -> str | list[dict[str, str]]:
        """
        Handles the feedback-refinement loop with at least one round but
        5 rounds at most

        Parameters
        ----------
        generated_prompt : str
            The generated prompt

        Returns
        -------
        str
            The final refined prompt
        """
        developer_prompt = self.return_prompt(
            type_prompt="feedback"
        )
        user_incorporate_feedback = self.return_prompt(
            type_prompt="incorporate"
        )

        conversation_list = [
            {"role": "user", "content": f"<prompt>{generated_prompt}</prompt>"}
        ]
        responses = []
        user_feedback = "Please provide feedback on the new prompt."
        scores_satisfied = False
        round_number = 0

        responses.append(self.send_prompt(
            developer_prompt=developer_prompt,
            conversation_list=conversation_list
        ))
        logger.info(
            "Feedback: {response}:",
            response=responses[-1],
        )

        while not scores_satisfied and round_number < 5:
            logger.info(
                "Feedback loop round: {round_number}:",
                round_number=round_number + 1,
            )
            print(f"Round: {round_number + 1}")
            conversation_list.extend([
                {"role": "assistant", "content": responses[-1]},
                {"role": "user", "content": user_incorporate_feedback}
            ])
            responses.append(self.send_prompt(
                developer_prompt=developer_prompt,
                conversation_list=conversation_list
            ))
            logger.info(
                "Result of incorporating feedback: {response}:",
                response=responses[-1],
            )
            conversation_list.extend([
                {"role": "assistant", "content": responses[-1]},
                {"role": "user", "content": user_feedback}
            ])
            responses.append(self.send_prompt(
                developer_prompt=developer_prompt,
                conversation_list=conversation_list
            ))
            logger.info(
                "Feedback: {response}:",
                response=responses[-1],
            )
            scores_satisfied = self.check_score(responses[-1], 8)
            round_number += 1

        return responses[-2], responses

    def process_feedback_loop(
        self,
        prompt: str
    ) -> str:
        """
        Starts the feedback loop with the prompt if
        refine_prompts is set to True

        Parameters
        ----------
        prompt : str
            The prompt to refine

        Returns
        -----
        str
            The (potentially) refined prompt
        """
        if self.refine_prompts:
            prompt, _ = self.feedback_loop(
                generated_prompt=prompt
            )
        return prompt

    def verify_solution_prompt(
        self,
        instruction_json: dict,
        pii_name: str
    ) -> str:
        """
        Takes the instructions from the meta expert and generates a prompt

        Parameters
        ----------
        instructions : str
            The instructions from the meta expert
        pii_name : str
            The name of the PII

        Returns
        -------
        str
            The refined prompt of the feedback loop
        """
        verifying_prompt = self.create_prompt_with_examples(
            instructions=instruction_json,
            pii_name=pii_name,
            type_prompt="verifying"
        )
        return self.process_feedback_loop(verifying_prompt)


class MetaPrompter(LLMAgent):
    def __init__(
        self,
        local: bool,
        prompt_folder: str,
        yml_file: str,
        api_key: str,
        category: str,
        prompt_creater: PromptCreater,
        prompt_config_yml: str,
        model_name: str = None,
        base_url: str = "https://api.openai.com/v1",
        temperature: float = 1.0,
        port: int = None,
        conn: Neo4jConnection = None,
    ):
        super().__init__(
            local=local,
            prompt_folder=prompt_folder,
            model_name=model_name,
            temperature=temperature,
            api_key=api_key,
            base_url=base_url,
            port=port
        )
        self.yml = utils.read_yaml(yml_file)
        self.conn = conn
        self.prompt_creater = prompt_creater
        prompt_config_yml = utils.read_yaml(prompt_config_yml)
        self.prompts = utils.set_prompts_argument(
            prompt_folder=self.prompt_folder,
            prompt_config_yml=prompt_config_yml
        )
        self.meta_expert_prompt = (
            self.prompts["meta_prompting"][category]["meta_expert_prompt"]
        )
        self.meta_expert_next_step_prompt = (
            self.prompts["meta_prompting"][category]
            ["meta_expert_next_step_prompt"]
        )

    def create_json_for_prompts_generation(
        self,
        pii_name: str,
        meta_expert_json: dict,
        guidelines_path: str = None,
    ) -> str:
        """
        This generates the JSON with information nesscarry
        for prompt generation

        Parameters
        ----------
        pii_name : str
            The name of the PII
        guidelines_path : str
            The path to the guidelines file
        meta_expert_json : dict
            The meta expert JSON
        text : str
            The text to generate the prompt for

        Returns
        -------
        str
            The JSON string
        """
        if guidelines_path is not None:
            with open(guidelines_path, "r") as f:
                guidelines = f.read()
        pii_dict = utils.get_property_information(
            yml=self.yml,
            pii_name=pii_name
        )
        prompt_json = {
            "job description": meta_expert_json["job description"],
            "instructions": meta_expert_json["instructions"],
            "pii": pii_name,
            "description of pii": (
                pii_dict[pii_name]["description"]
            ),
            "examples": (
                pii_dict[pii_name]["example"]
            )
        }

        if guidelines_path is not None:
            prompt_json["guidelines"] = guidelines

        return json.dumps(prompt_json)

    def start_meta_expert(
        self,
        pii_name: str,
    ) -> tuple[dict, str]:
        """
        Starts the conversation with the meta expert

        Parameters
        ----------
        pii_name : str
            The name of the PII

        Returns
        -------
        tuple[str, str]
            The response from the meta expert and the user prompt
            describing the pii
        """
        pii_description = utils.get_property_information(
            yml=self.yml,
            pii_name=pii_name
        )
        user_prompt_text = f"""
        <pii>{pii_description}</pii>
        """
        conversation_list = [{"role": "user", "content": user_prompt_text}]
        response = self.send_prompt(
            developer_prompt=self.meta_expert_prompt,
            conversation_list=conversation_list,
        )
        logger.info(
            textwrap.dedent("""Start of Conversation:
            {response}
            --------------------------------
            """),
            response=response
        )
        
        return self._extract_json_from_response(response), user_prompt_text

    def return_prompt(
        self,
        type_prompt: str
    ) -> str:
        """
        This function returns the desired prompt based on the type of prompt

        Parameters
        ----------
        type_prompt : str
            The type of prompt

        Returns
        -------
        str
            The desired prompt
        """
        match type_prompt:
            case "feedback":
                return (self.prompts["meta_prompting"]["general"]
                        ["prompt_feedback_generation"])
            case "incorporate":
                return (self.prompts["meta_prompting"]["general"]
                        ["prompt_incoporate_feedback"])

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
            r'(\{"Next":\s?"\w+"\})'
        ]

        for pattern in patterns:
            match = re.search(pattern, response, re.DOTALL)
            if match:
                return match.group(1)
        raise ValueError(
            f"No next step found in response:\n\n{response}"
        )

    def combine_issue_prompt_w_examples(
        self,
        issue_prompt: str,
        extracting_prompt: str
    ) -> str:
        """
        Combines the issue prompt with the examples from the extracting prompt

        Parameters
        ----------
        issue_prompt: str
            The prompt for solving the issues of wrong solution
        extracting_prompt: str
            The prompt for extracting the solution

        Returns
        -------
        str
            The issue prompt with the examples
        """
        pattern = r"## Examples.*"
        result = re.search(pattern, extracting_prompt, re.DOTALL)

        examples = result.group(0)

        return f"""{issue_prompt}\n{examples}"""

    def combine_solutions_to_string(
        self,
        solutions: str | list[dict[str, str, str, str]],
        issue_handling: bool
    ) -> str:
        """
        Takes the solutions and combines them to a string

        Parameters
        ----------
        solutions : str | list[dict[str, str, str, str]]
            The solutions
        issue_handling: bool
            If the solutions are for issue handling

        Returns
        -------
        str
            The solutions as a string
        """
        if issue_handling:
            solutions_str = "\n\n---\n\n".join([
                json.dumps(corrected_solution)
                for corrected_solution in solutions
            ])
        else:
            solutions_str = "\n\n---\n\n".join(solutions)
        return solutions_str

    def extract_with_prompt(
        self,
        text: str,
        generated_prompts: str,
        pii_name: str
    ) -> str:
        """
        Extracts the solution from the text with the help
        of the LLM

        Parameters
        ----------
        text : str
            The text to extract the solution from
        generated_prompts : str
            The generated prompts
        pii_name : str
            The name of the PII

        Returns
        -------
        str
            The response from the LLM
        """
        raise NotImplementedError("Subclasses must implement this method")

    def check_solution(
        self,
        verification_prompt: str,
        solution: str,
    ) -> str:
        """
        Sends the solution to the verification prompt

        Parameters
        ----------
        verification_prompt : str
            The verification prompt
        solution : str
            The solution to verify

        Returns
        -------
        str
            The response from the verification prompt
        """

        raise NotImplementedError("Subclasses must implement this method")

    def send_solutions_for_verification(
        text: str,
        verification_prompt: str,
        solutions: str,
        pii_name: str,
        pii_description: str,
    ) -> list[str]:
        """
        Sends every solution individually to LLM for examination

        Parameters
        ----------
        text : str
            The text where the solution was extracted from
        verification_prompt : str
            The verification prompt
        solutions : str
            The solutions to verify
        pii_name : str
            The name of the PII
        pii_description : str
            The description of the PII

        Returns
        -------
        list[str]
            The responses from the LLM
        """
        raise NotImplementedError("Subclasses must implement this method")

    def categorize_solutions(
        self,
        solutions: str,
        verification_results: list[str],
    ) -> tuple[list[str], dict[str, dict[str, str]]]:
        """
        Takes the solutions and the verification results and categorizes them
        into correct and incorrect solutions

        Parameters
        ----------
        solutions : str
            The solutions to verify
        verification_results : list[str]
            The verification results

        Returns
        -------
        tuple[list[str], dict[str, dict[str, str]]]
            The corrected identifiers and the incorrect dictionary
        """

        raise NotImplementedError("Subclasses must implement this method")

    def add_corrected_to_old_solutions(
        self,
        old_response: list[str],
        issue_solving_response: str,
        verification_results: list[str]
    ) -> str:
        """
        Takes the old response, verification results and the response
        from the issue solving prompt and outputs string of list of
        correct solutions

        Parameters
        ----------
        old_response : list[str]
            The old response
        issue_solving_response : str
            The response from the issue solving prompt
        verification_results : list[str]
            The verification results

        Returns
        -------
        list[str]
            The list of correct solutions
        """
        raise NotImplementedError("Subclasses must implement this method")

    def convert_list_solution_to_dict(
        self,
        solution_list: list[dict[str, str, str, str]]
    ) -> str:
        """
        Converts a list of solution dictionaries into a structured
        dictionary and serializes it as a JSON string.

        The output dictionary has the structure:
        {
            "uuid_person": [
                {
                    "reasoning": ...,
                    "context": ...,
                    "identifier": ...,
                    "uuid_of_solution": ...
                }
            ]
        }

        Parameters
        ----------
        solution_list : list[dict[str, str, str, str]]
            The list of solutions

        Returns
        -------
        str
            The solutions as a JSON string
        """
        raise NotImplementedError("Subclasses must implement this method")

    def send_issue_prompt(
        self,
        issue_prompt: str,
        pii_name: str,
        correct_solutions: list[dict[str, dict[str, bool, str, str]]],
        wrong_solutions: list[dict[str, dict[str, bool, str, str]]]
    ):
        raise NotImplementedError("Subclasses must implement this method")


class MetaPrompterIndependent(MetaPrompter):
    def __init__(
        self,
        prompt_folder: str,
        yml_file: str,
        api_key: str,
        category: str,
        prompt_creater: PromptCreater,
        prompt_config_yml: str,
        model_name: str = None,
        local: bool = False,
        base_url: str = "https://api.openai.com/v1",
        temperature: float = 1.0,
        port: int = None,
        conn: Neo4jConnection = None,
    ):
        super().__init__(
            local=local,
            prompt_folder=prompt_folder,
            model_name=model_name,
            temperature=temperature,
            api_key=api_key,
            category=category,
            base_url=base_url,
            port=port,
            yml_file=yml_file,
            prompt_config_yml=prompt_config_yml,
            prompt_creater=prompt_creater,
            conn=conn
        )

    def extract_with_prompt(
        self,
        text: str,
        generated_prompts: str,
        pii_name: str
    ) -> str:
        """
        Extracts the solution from the text with the help
        of the LLM

        Parameters
        ----------
        text : str
            The text to extract the solution from
        generated_prompts : str
            The generated prompts
        pii_name : str
            The name of the PII

        Returns
        -------
        str
            The response from the LLM
        """
        pii_dict = utils.get_property_information(
            yml=self.yml,
            pii_name=pii_name
        )
        user_prompt_text = textwrap.dedent(f"""
            <text>{text}</text>
            <pii>{pii_dict[pii_name]}</pii>
            <pii_description>{pii_dict[pii_name]["description"]}</pii_description>
        """)
        conversation_list = [{"role": "user", "content": user_prompt_text}]
        response = self.send_prompt(
            developer_prompt=generated_prompts,
            conversation_list=conversation_list
        )
        response = self._extract_json_from_response(response)
        return json.dumps(response)

    def add_uuid_to_solution(
        self,
        solution: dict
    ) -> list:
        """
        Adds a UUID to the solutions

        Parameters
        ----------
        solution : dict
            The solution to add the UUID to

        Returns
        -------
        list
            The solution with the UUID
        """
        uuid_list = []
        for result in solution["extracted_information"]:
            uuid_list.append(
                {str(uuid.uuid4())[:16]: result}
            )

        return uuid_list

    async def send_solutions_for_verification(
        self,
        text: str,
        verification_prompt: str,
        solutions: str,
        pii_name: str,
        pii_description: str,
    ) -> list[str]:
        """
        Sends every solution individually to LLM for examination

        Parameters
        ----------
        text : str
            The text where the solution was extracted from
        verification_prompt : str
            The verification prompt
        solutions : str
            The solutions to verify
        pii_name : str
            The name of the PII
        pii_description : str
            The description of the PII

        Returns
        -------
        list[str]
            The responses from the LLM
        """
        tasks = []
        solutions = json.loads(solutions)
        async with asyncio.TaskGroup() as tg:
            for solution in solutions:
                user_prompt = f"""
                <solution>{solution}</solution>
                <text>{text}</text>
                <pii>{pii_name}: {pii_description}</pii>
                """
                conversation_list = [{"role": "user", "content": user_prompt}]
                task = tg.create_task(self.send_prompt_async(
                    developer_prompt=verification_prompt,
                    conversation_list=conversation_list
                ))
                tasks.append(task)

        results = [task.result() for task in tasks]
        return results

    def categorize_solutions(
        self,
        verify_results: str
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
        temp_dict = json.loads(verify_results)
        for key, value in temp_dict.items():
            if value["bool"]:
                correct_solutions[key] = value
            else:
                wrong_solutions[key] = value

        return correct_solutions, wrong_solutions

    def send_issue_prompt(
        self,
        text: str,
        issue_prompt: str,
        pii_name: str,
        correct_solutions: list[dict[str, dict[str, bool, str, str]]],
        wrong_solutions: list[dict[str, dict[str, bool, str, str]]]
    ) -> dict[str, dict[str, bool, str, str]]:
        """
        Sends the issue prompt to the LLM and the LLM returns the corrected
        and newly found solutions

        Parameters
        ----------
        text : str
            The text to extract the solution from
        issue_prompt : str
            The issue prompt
        pii_name : str
            The name of the PII
        correct_solutions : list[dict[str, dict[str, bool, str, str]]]
            The correct solutions
        wrong_solutions : list[dict[str, dict[str, bool, str, str]]]
            The wrong solutions

        Returns
        -------
        dict[str, dict[str, bool, str, str]]
            Correct_solutions and newly found solutions

        """
        pii_dict = utils.get_property_information(
            yml=self.yml,
            pii_name=pii_name
        )[pii_name]

        user_prompt = f"""
        <text>{text}</text>
        <correct_solution>{json.dumps(correct_solutions)}</correct_solution>
        <wrong_solution>{json.dumps(wrong_solutions)}</wrong_solution>
        <pii_name**>{pii_name}</pii_name>
        <pii_description>{pii_dict["description"]}</pii_description>
        """
        conversation_list = [{"role": "user", "content": user_prompt}]
        reponse = self.send_prompt(
            developer_prompt=issue_prompt,
            conversation_list=conversation_list
        )
        logger.info(
            "Response: {reponse}\n-----------------",
            reponse=reponse
        )
        result = self.add_uuid_to_solution(
            self._extract_json_from_response(reponse)
        )
        temp_dict = {}

        correct_solutions_list = []
        for key, value in correct_solutions.items():
            correct_solutions_list.append({key: value})

        for dict in result + correct_solutions_list:
            for key, value in dict.items():
                value.pop("bool", None)
                temp_dict[key] = value
        return temp_dict


class MetaPrompterIndividuals(MetaPrompter):
    def __init__(
        self,
        local: bool,
        prompt_folder: str,
        yml_file: str,
        api_key: str,
        category: str,
        prompt_creater: PromptCreater,
        prompt_config_yml: str,
        model_name: str = None,
        temperature: float = 1.0,
        base_url: str = "https://api.openai.com/v1",
        port: int = None,
        conn: Neo4jConnection = None,
    ):
        super().__init__(
            local=local,
            prompt_folder=prompt_folder,
            model_name=model_name,
            temperature=temperature,
            api_key=api_key,
            category=category,
            base_url=base_url,
            port=port,
            yml_file=yml_file,
            prompt_config_yml=prompt_config_yml,
            prompt_creater=prompt_creater,
            conn=conn
        )

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

        query = """
        MATCH (designation:Entity_designation)
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

    def add_uuid_to_solution(
        self,
        solution: dict
    ) -> dict:
        """
        Adds a UUID to the solutions

        Parameters
        ----------
        solution : dict
            The solution to add the UUID to

        Returns
        -------
        dict
            The solution with the UUID
        """
        for person in solution.keys():
            for entry in solution[person]:
                entry["uuid_of_solution"] = str(uuid.uuid4())[:16]

        return solution

    def extract_with_prompt(
        self,
        text: str,
        generated_prompts: str,
        pii_name: str
    ) -> str:
        """
        Extracts the solution from the text with the help
        of the LLM

        Parameters
        ----------
        text : str
            The text to extract the solution from
        generated_prompts : str
            The generated prompts
        pii_name : str
            The name of the PII

        Returns
        -------
        str
            The response from the LLM
        """
        pii_dict = utils.get_property_information(
            yml=self.yml,
            pii_name=pii_name
        )
        user_prompt_text = f"""
        <person_dict>{self.read_persons()}</person_dict>
        <text>{text}</text>
        <pii>{pii_dict[pii_name]}</pii>
        <pii_description>{pii_dict[pii_name]["description"]}</pii_description>
        """
        # The experts don't have memory, so we need to provide the context
        conversation_list = [{"role": "user", "content": user_prompt_text}]
        response = self.send_prompt(
            developer_prompt=generated_prompts,
            conversation_list=conversation_list
        )
        response = self._extract_json_from_response(response)
        return json.dumps(response)

    def check_solution(
        self,
        verification_prompt: str,
        solution: str,
    ) -> str:
        """
        Sends the solution to the verification prompt

        Parameters
        ----------
        verification_prompt : str
            The verification prompt
        solution : str
            The solution to verify

        Returns
        -------
        str
            The response from the verification prompt
        """
        user_prompt = textwrap.dedent(f"""
        <persons>{self.read_persons()}</persons>
        <soltions>{solution}</solutions>
        """)
        conversation_list = [{"role": "user", "content": user_prompt}]
        return self.send_prompt(
            developer_prompt=verification_prompt,
            conversation_list=conversation_list
        )

    async def send_solutions_for_verification(
        self,
        text: str,
        verification_prompt: str,
        solutions: str,
        pii_name: str,
        pii_description: str,
    ) -> list[str]:
        """
        Sends every solution individually to LLM for examination

        Parameters
        ----------
        text : str
            The text where the solution was extracted from
        verification_prompt : str
            The verification prompt
        solutions : str
            The solutions to verify
        pii_name : str
            The name of the PII
        pii_description : str
            The description of the PII

        Returns
        -------
        list[str]
            The responses from the LLM
        """
        solutions_list = self.prepare_solution_for_verification(solutions)
        person_dict = json.loads(self.read_persons())
        tasks = []
        # TODO: Hier kannst du schauen, dass das person_dict nur auf die
        # Personen beschränkt ist, die in der Lösung vorkommt
        async with asyncio.TaskGroup() as tg:
            for solution in solutions_list:
                user_prompt = f"""
                <persons>{person_dict}</persons>
                <solution>{solution}</solution>
                <text>{text}</text>
                <pii>{pii_name}: {pii_description}</pii>
                """
                conversation_list = [{"role": "user", "content": user_prompt}]
                task = tg.create_task(self.send_prompt_async(
                    developer_prompt=verification_prompt,
                    conversation_list=conversation_list
                ))
                tasks.append(task)

        results = [task.result() for task in tasks]
        return results

    def categorize_solutions(
        self,
        solutions: str,
        verification_results: list[str],
    ) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
        """
        Takes the solutions and the verification results and categorizes them
        into correct and incorrect solutions

        Parameters
        ----------
        solutions : str
            The solutions to verify
        verification_results : list[str]
            The verification results

        Returns
        -------
        tuple[list[str], dict[str, dict[str, str]]]
            The corrected identifiers and the incorrect dictionary
        """
        solution_dict = self.prepare_solution_for_verification(solutions)
        solution_temp_dict = {
            inner["uuid_of_solution"]: {
                "reasoning": inner["reasoning"],
                "context": inner["context"],
                "identifier": inner["identifier"],
                "uuid_person": uuid_person
            }
            for solution in solution_dict
            for uuid_person, inner in solution.items()
        }
        verification_results_dict = {
            list(temp.keys())[0]: temp[list(temp.keys())[0]]
            for result in verification_results
            for temp in [self._extract_json_from_response(result)]
        }

        corrected_identifiers = []
        incorrect_dict = {}
        for key, val_dict in verification_results_dict.items():
            if val_dict["bool"]:
                corrected_identifiers.append(
                    solution_temp_dict[key]["identifier"]
                )
            else:
                incorrect_dict[key] = {
                    "identifier": solution_temp_dict[key]["identifier"],
                    "reason_why_false": val_dict["reasoning"],
                    "context": solution_temp_dict[key]["context"],
                    "uuid_person": solution_temp_dict[key]["uuid_person"]
                }
        return corrected_identifiers, incorrect_dict

    def prepare_solution_for_verification(
        self,
        solutions: str
    ) -> list:
        """
        Prepares the solutions for verification

        Parameters
        ----------
        solutions : str
            The solutions to prepare

        Returns
        -------
        list
            The prepared solutions
        """
        temp = json.loads(solutions)
        solutions_list = []
        for person, val_dict_list in temp.items():
            if val_dict_list:
                for val_dict in val_dict_list:
                    solutions_list.append({
                        person: val_dict
                    })

        return solutions_list

    def add_corrected_to_old_solutions(
        self,
        old_response: list[str],
        issue_solving_response: str,
        verification_results: list[str]
    ) -> str:
        """
        Takes the old response, verification results and the response
        from the issue solving prompt and outputs string of list of
        correct solutions

        Parameters
        ----------
        old_response : list[str]
            The old response
        issue_solving_response : str
            The response from the issue solving prompt
        verification_results : list[str]
            The verification results

        Returns
        -------
        list[str]
            The list of correct solutions
        """
        further_solutions = self.add_uuid_to_solution(
            self._extract_json_from_response(issue_solving_response)
        )
        further_solutions = self.prepare_solution_for_verification(
            json.dumps(further_solutions)
        )
        correct_solutions, _ = self.categorize_solutions(
            solutions=old_response,
            verification_results=verification_results
        )
        solutions_list = self.prepare_solution_for_verification(old_response)
        # TODO: Was wenn mehr als eine further solution. DAS MUSST DU LÖSEN!!!
        solutions_list.extend(further_solutions)
        correct_solutions_list = [
            {key_name: solution[key_name]}
            for solution in solutions_list
            for key_name in solution
            if solution[key_name]["identifier"] in correct_solutions
        ]
        correct_solutions_list.extend(further_solutions)

        return correct_solutions_list

    def convert_list_solution_to_dict(
        self,
        solution_list: list[dict[str, str, str, str]]
    ) -> str:
        """
        Converts a list of solution dictionaries into a structured
        dictionary and serializes it as a JSON string.

        The output dictionary has the structure:
        {
            "uuid_person": [
                {
                    "reasoning": ...,
                    "context": ...,
                    "identifier": ...,
                    "uuid_of_solution": ...
                }
            ]
        }

        Parameters
        ----------
        solution_list : list[dict[str, str, str, str]]
            The list of solutions

        Returns
        -------
        str
            The solutions as a JSON string
        """
        corrected_solutions_dict = {}
        all_keys = list(
            set().union(*(d.keys() for d in solution_list))
        )
        for key in all_keys:
            corrected_solutions_dict[key] = []
        for solution in solution_list:
            key_name = list(solution.keys())[0]
            corrected_solutions_dict[key_name].append(solution[key_name])

        return json.dumps(corrected_solutions_dict)


class MetaExpertConversation():
    """
    Handles the conversation with the meta expert
    """
    def __init__(
        self,
        agent: MetaPrompter,
        prompt_generator: PromptCreater,
        text: str,
        generated_prompt_folder: str,
        generate_new_prompt: bool,
        pii_name: str,
        guidelines_path_extracting: str,
        guidelines_path_issue: str,
        refine_prompts: bool = False
    ):
        self.agent = agent
        self.text = text
        self.generated_prompt_folder = generated_prompt_folder
        self.generate_new_prompt = generate_new_prompt
        self.pii_name = pii_name
        self.guidelines_path_extracting = guidelines_path_extracting
        self.guidelines_path_issue = guidelines_path_issue
        self.refine_prompts = refine_prompts
        self.prompt_generator = prompt_generator
        self.proposed_solutions = []
        self.verify_solutions = []

        prompts = agent.prompts["meta_prompting"]["general"]
        self.meta_expert_prompt = agent.meta_expert_prompt
        self.meta_expert_next_step_prompt = agent.meta_expert_next_step_prompt
        self.next_instruction_meta_prompt = prompts["next_instruction_meta"]
        self.next_step_meta_prompt = prompts["next_step_meta"]

        self.conversation_list = []
        self.responses = []
        self.step_queue = []
        self.generated_prompts = {
            "extracting": [],
            "verifying": [],
            "issue": []
        }

        if self.generate_new_prompt:
            self.to_generate = {
                "extracting": True,
                "verifying": True,
                "issue": True
            }
        if not self.generate_new_prompt:
            self.to_generate = {
                "extracting": False,
                "verifying": False,
                "issue": False
            }
            try:
                self.load_generated_prompts()
            except FileNotFoundError:
                self.generate_new_prompt = True
                # TODO: Das wieder richtig stellen
                # self.refine_prompts = True

    def select_prompt_from_config(
        self,
        category: str
    ) -> None:
        """
        Selects the prompts from the config file and sets
        them as attributes. Possible categories are:
        independent, individuals, organisations

        Parameters
        ----------
        category : str
            The category to select the prompts for

        Returns
        -------
        None
        """
        temp = self.prompts["meta_prompting"][category]
        self.meta_expert_prompt = temp["meta_expert_prompt"]
        self.meta_expert_next_step_prompt = temp["meta_expert_next_step_prompt"]
        self.next_instruction_meta_prompt = temp["next_instruction_meta"]
        self.next_step_meta_prompt = temp["meta_expert_next_step_prompt"]

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
        self.start_conversation()
        while self.step_queue[-1]["Next"] != "end":
            self.take_next_step()
            self.generate_next_step()

        return self.take_next_step()

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

    def save_prompt_to_file(
        self,
        prompt: str,
        type: str
    ) -> None:
        """
        Checks if type of prompt for pii exists and if not
        saves the prompt to the file

        Parameters
        ----------
        prompt : str
            The prompt to save
        type : str
            The type of the prompt (extracting, verifiying, issue_solving)

        Returns
        -------
        None
        """
        # TODO: Vielleicht solltest du das anders machen und jedes Mal den
        # Prompt neu speichern, wenn du den Prompt neu generierst und den
        # Alten dann backupacken

        self.prompt_generator.save_prompt_to_file(
            prompt=prompt,
            pii_name=self.pii_name,
            type=type
        )

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
            self.generated_prompt_folder,
            self.prompt_generator.category,
            self.pii_name
        )

        prompt_types = ["extracting", "issue", "verifying"]

        for prompt_type in prompt_types:
            file_path_temp = os.path.join(
                file_path,
                f"{self.pii_name}_{prompt_type}.md"
            )
            try:
                with open(file_path_temp, "r") as f:
                    self.generated_prompts[prompt_type].append(f.read())
            except FileNotFoundError:
                self.to_generate[prompt_type] = True

    def start_conversation(
        self
    ) -> None:
        """
        Starts the conversation with the meta expert and adds the
        description of the pii to the conversation list and
        the instructions for extracting. Can create prompt for
        extracting and sets next step as verification.

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        instructions, user_prompt = self.agent.start_meta_expert(
            pii_name=self.pii_name
        )
        self.add_to_conversation_list(
            role="user", content=json.dumps(user_prompt)
        )
        self.add_to_conversation_list(
            role="assistant", content=json.dumps(instructions)
        )

        if self.to_generate["extracting"]:
            generated_prompt = self.prompt_generator.\
                create_prompt_with_examples(
                    instructions=instructions,
                    pii_name=self.pii_name,
                    guidelines_path=self.guidelines_path_extracting,
                    type_prompt="extracting"
                )

            if self.refine_prompts:
                generated_prompt = self.prompt_generator.process_feedback_loop(
                    prompt=generated_prompt
                )

            self.generated_prompts["extracting"].append(generated_prompt)
            self.save_prompt_to_file(
                prompt=self.generated_prompts["extracting"][-1],
                type="extracting"
            )

        self.step_queue.append({"Next": 'extracting'})
        logger.info(
            "Next Step: extracting\n-----------------",
        )

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
                self.run_prompt(type="extracting")
            case "verification":
                self.verify_solution()
            case "issues_solving":
                self.solve_issues()
            case "end":
                return self.end_conversation()
            case _:
                raise ValueError("Invalid next step")

    def extract_solution(
        self
    ) -> None:
        """
        Extracts the solution from the text with a generated prompt.
        Adds the solution to the conversation list and sets the next step

        Returns
        -------
        None
        """
        reponse_temp = self.agent.extract_with_prompt(
            text=self.text,
            generated_prompts=self.generated_prompts["extracting"][-1],
            pii_name=self.pii_name
        )
        self.responses.append(reponse_temp)

        self.add_next_step_meta_to_conversation(
            response=reponse_temp,
            issue_handling=False
        )

    def add_next_step_meta_to_conversation(
        self,
        response: str | list[dict[str, str, str, str]],
        issue_handling: bool
    ) -> None:
        """
        Takes the conversation list and adds the next step for the meta expert

        Parameters
        ----------
        response : str | list[dict[str, str, str, str]]
            The response from the meta expert
        issue_handeling: bool
            If the response is for issue handeling

        Returns
        -------
        None
        """
        try:
            expert = json.loads(
                self.conversation_list[-1]["content"]
            )["job description"]
        except KeyError:  # When the LLM formats the response wrongly
            expert = json.loads(
                self.conversation_list[-1]["content"]
            )["Instructions"]["job description"]
        except TypeError:
            expert = utils.extract_instruction(
                self.conversation_list[-1]["content"]
            )

        previous_step = self.step_queue[-1]["Next"]

        prompt = self.next_instruction_meta_prompt
        prompt = prompt \
            .replace("{{expert}}", expert) \
            .replace("{{previous_step}}", previous_step) \
            .replace("{{response}}", response)

        self.add_to_conversation_list(
            role="user", content=prompt
        )

    def construct_last_step(
        self
    ) -> None:
        """
        123
        """
        pattern = r"<response>(.*?)</response>"
        text = self.conversation_list[-1]["content"]
        match = re.search(pattern, text, re.DOTALL)

        if match:
            response = match.group(1)

        previous_step = self.step_queue[-1]["Next"]
        # Das auf next_instructions änder
        prompt = self.next_step_meta_prompt
        prompt = prompt \
            .replace("{{previous_step}}", previous_step) \
            .replace("{{response}}", response)

        return prompt

    def create_next_step(
        self
    ) -> None:
        """
        Sends the last response to the meta expert and decides the next step

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        user_prompt = self.construct_last_step()
        reponse_temp = self.agent.send_prompt(
            developer_prompt=self.meta_expert_next_step_prompt,
            conversation_list=[{"role": "user", "content": user_prompt}]
        )
        next_step = json.loads(self.agent.extract_next_step(reponse_temp))
        self.step_queue.append(next_step)
        logger.info(
            "Next Step: {next_step}\n-----------------",
            next_step=next_step
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
        if self.step_queue[-1]["Next"] != "end":
            self.create_next_step()
            response_temp = self.agent.send_prompt(
                developer_prompt=self.meta_expert_prompt,
                conversation_list=self.conversation_list[-6:]
            )

            try:
                response_temp = self.agent._extract_json_from_response(
                    response_temp
                )
            except IndexError:
                response_temp = utils.extract_instruction(
                    response_temp
                )

            content_temp = json.dumps(
                response_temp
            )
            self.add_to_conversation_list(
                role="assistant", content=content_temp
            )

    def run_prompt(
        self,
        type: str
    ) -> None:
        """
        Runs the prompt for the given type. Adds the response to the
        conversation list and sets the next step

        Parameters
        ----------
        type : str
            The type of the prompt

        Returns
        -------
        None
        """
        if type == "extracting":
            reponse_temp = self.agent.extract_with_prompt(
                text=self.text,
                generated_prompts=self.generated_prompts[type][-1],
                pii_name=self.pii_name
            )
            logger.info(f"Extraction response\n\n'{reponse_temp}'")
            self.responses.append(reponse_temp)
            solution_dict = self.agent.add_uuid_to_solution(
                json.loads(self.responses[-1])
            )
            self.proposed_solutions.append(json.dumps(solution_dict))

        self.add_next_step_meta_to_conversation(
            response=reponse_temp,
            issue_handling=False
        )

    def create_verifying_prompt(
        self
    ) -> None:
        """
        Creates the prompt for verifying the solution

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        instruction_json = json.loads(self.conversation_list[-1]["content"])
        final_prompt = self.prompt_generator.create_prompt_with_examples(
            instructions=instruction_json,
            pii_name=self.pii_name,
            type_prompt="verifying"
        )
        if self.refine_prompts:
            final_prompt, responses_feedback = self.prompt_generator.\
                process_feedback_loop(
                    prompt=final_prompt
                )

        self.generated_prompts["verifying"].append(final_prompt)
        self.save_prompt_to_file(
            prompt=final_prompt,
            type="verifying"
        )

    def create_issue_prompt(
        self
    ) -> None:
        """
        Creates the prompt for solving the issue

        Parameters
        ----------
        None

        Returns
        -------
        None

        """
        instruction_json = json.loads(self.conversation_list[-1]["content"])
        final_prompt = self.prompt_generator.create_prompt_with_examples(
            instructions=instruction_json,
            pii_name=self.pii_name,
            type_prompt="issue"
        )
        if self.refine_prompts:
            final_prompt, responses_feedback = self.prompt_generator.\
                process_feedback_loop(
                    generated_prompt=final_prompt
                )
        self.generated_prompts["issue"].append(final_prompt)
        self.save_prompt_to_file(
            prompt=final_prompt,
            type="issue"
        )

    def verify_solution(
        self
    ):
        """
        Verifies the solution with the generated prompt and
        add verification results to the verify_solutions list
        and sets the next step

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        if self.to_generate["verifying"]:
            self.create_verifying_prompt()
            self.save_prompt_to_file(
                prompt=self.generated_prompts["verifying"][-1],
                type="verifying"
            )

        pii_dict = utils.get_property_information(
            yml=self.agent.yml,
            pii_name=self.pii_name
        )
        results = asyncio.run(self.agent.send_solutions_for_verification(
            text=self.text,
            verification_prompt=self.generated_prompts["verifying"][-1],
            solutions=self.proposed_solutions[-1],
            pii_name=self.pii_name,
            pii_description=pii_dict[self.pii_name]["description"]
        ))
        logger.info(f"Verification response'{results}'")
        self.verify_solutions.append(
            self.process_verification_results(
                verification_results=results,
                unverified_solutions=json.loads(self.proposed_solutions[-1])
            )
        )
        self.add_next_step_meta_to_conversation(
            response=self.verify_solutions[-1],
            issue_handling=False
        )

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
        if self.to_generate["issue"]:
            self.create_issue_prompt()
            self.save_prompt_to_file(
                prompt=self.generated_prompts["issue"][-1],
                type="issue"
            )

        correct_solutions, wrong_solutions = self.agent.categorize_solutions(
            self.verify_solutions[-1]
        )
        results = self.agent.send_issue_prompt(
            issue_prompt=self.generated_prompts["issue"][-1],
            text=self.text,
            pii_name=self.pii_name,
            correct_solutions=correct_solutions,
            wrong_solutions=wrong_solutions
        )
        self.proposed_solutions.append(json.dumps(results))

        self.add_next_step_meta_to_conversation(
            response=self.proposed_solutions[-1],
            issue_handling=False
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
        if not self.verify_solutions:
            return {}
        # TODO: Checken ob das wirklich stimmt!
        # Alt: json.loads(self.verify_solutions[-1])
        last_proposed_solution = json.loads(self.proposed_solutions[-1])
        if isinstance(last_proposed_solution, list):
            return last_proposed_solution
        return [
            {key: value} for key, value in last_proposed_solution.items()
        ]

    def process_verification_results(
        self,
        verification_results: list[str],
        unverified_solutions: dict[str, list[dict[str, str, str, str]]]
    ) -> str:
        """
        Takes the verification results and adds info (person_uuid, reasoning
        and identifier) to the solutions proposed

        Parameters
        ----------
        verification_results : list[str]
            The verification results
        unverified_solutions : dict[str, list[dict[str, str, str, str]]]
            The unverified solutions

        Returns
        -------
        str
            The verification results with the added info
        """
        raise NotImplementedError(
            "This method needs to be implemented in the subclass"
        )


class MetaExpertConversationIndependet(MetaExpertConversation):
    """
    Handles the conversation with the meta expert
    """
    def __init__(
        self,
        agent: MetaPrompter,
        prompt_generator: PromptCreater,
        text: str,
        generated_prompt_folder: str,
        generate_new_prompt: bool,
        pii_name: str,
        guidelines_path_extracting: str,
        guidelines_path_issue: str,
        refine_prompts: bool = False
    ):
        super().__init__(
            agent=agent,
            prompt_generator=prompt_generator,
            text=text,
            generated_prompt_folder=generated_prompt_folder,
            generate_new_prompt=generate_new_prompt,
            pii_name=pii_name,
            guidelines_path_extracting=guidelines_path_extracting,
            guidelines_path_issue=guidelines_path_issue,
            refine_prompts=refine_prompts
        )

    def process_verification_results(
        self,
        verification_results: list[str],
        unverified_solutions: dict[str, list[dict[str, str, str, str]]]
    ) -> str:
        """
        Takes the verification results and adds info (person_uuid, reasoning
        and identifier) to the solutions proposed

        Parameters
        ----------
        verification_results : list[str]
            The verification results
        unverified_solutions : dict[str, list[dict[str, str, str, str]]]
            The unverified solutions

        Returns
        -------
        str
            The verification results with the added info
        """
        solutions_proposed = {}
        if type(unverified_solutions) is not list:
            unverified_solutions = [
                {key: value} for key, value in unverified_solutions.items()
            ]
        for solution in unverified_solutions:
            key = list(solution.keys())[0]
            solutions_proposed[key] = {
                "reasoning": solution[key]["reasoning"],
                "identifier": solution[key]["identifier"],
                "context": solution[key]["context"],
            }
        verification_solution_dict = {}
        for verifaction_string in verification_results:
            verification_solution_dict.update(
                self.agent._extract_json_from_response(verifaction_string)
            )
        for key in verification_solution_dict.keys():
            verification_solution_dict[key]["identifier"] = (
                solutions_proposed[key]["identifier"]
            )
            verification_solution_dict[key]["context"] = (
                solutions_proposed[key]["context"]
            )
        return json.dumps(verification_solution_dict)


class MetaExpertConversationIndividual(MetaExpertConversation):
    """
    Handles the conversation with the meta expert
    """
    def __init__(
        self,
        agent: MetaPrompter,
        prompt_generator: PromptCreater,
        text: str,
        generated_prompt_folder: str,
        generate_new_prompt: bool,
        pii_name: str,
        guidelines_path_extracting: str,
        guidelines_path_issue: str,
        refine_prompts: bool = False
    ):
        super().__init__(
            agent=agent,
            prompt_generator=prompt_generator,
            text=text,
            generated_prompt_folder=generated_prompt_folder,
            generate_new_prompt=generate_new_prompt,
            pii_name=pii_name,
            guidelines_path_extracting=guidelines_path_extracting,
            guidelines_path_issue=guidelines_path_issue,
            refine_prompts=refine_prompts
        )

    def process_verification_results(
        self,
        verification_results: list[str],
        unverified_solutions: dict[str, list[dict[str, str, str, str]]]
    ) -> str:
        """
        Takes the verification results and adds info (person_uuid, reasoning
        and identifier) to the solutions proposed

        Parameters
        ----------
        verification_results : list[str]
            The verification results
        unverified_solutions : dict[str, list[dict[str, str, str, str]]]
            The unverified solutions

        Returns
        -------
        str
            The verification results with the added info
        """
        solutions_proposed = {}
        for person_uuid, solutions_person in unverified_solutions.items():
            if solutions_person is None:
                continue
            for solution in solutions_person:
                solutions_proposed[solution["uuid_of_solution"]] = {
                    "reasoning": solution["reasoning"],
                    "identifier": solution["identifier"],
                    "context": solution["context"],
                    "person_uuid": person_uuid
                }
        verification_solution_dict = {}
        for verifaction_string in verification_results:
            verification_solution_dict.update(
                self.agent._extract_json_from_response(verifaction_string)
            )
        for key in verification_solution_dict.keys():
            verification_solution_dict[key]["person_uuid"] = (
                solutions_proposed[key]["person_uuid"]
            )
            verification_solution_dict[key]["identifier"] = (
                solutions_proposed[key]["identifier"]
            )
            verification_solution_dict[key]["context"] = (
                solutions_proposed[key]["context"]
            )
        return json.dumps(verification_solution_dict)