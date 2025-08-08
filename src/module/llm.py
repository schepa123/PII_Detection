import uuid
import os
from openai import OpenAI, AsyncOpenAI
import re
import json
import pprint
import yaml
import asyncio
from typing import Union
from loguru import logger


class LLMAgent:
    """
    Basic class for the LLM Agent

    Parameters
    ----------
    prompt_folder : str
        The parent folder of the diffent prompt subfolders
    model_name : str
        The name of the model
    api_key : str
        The API key for the LLM API
    port : int
        The port of the LLM API
    temperature : float
        The temperature of the model
    base_url : str
        The base URL of the LLM API
    """

    def __init__(
        self,
        local: bool,
        prompt_folder: str,
        model_name: str = None,
        api_key: str = "YOUR_API_KEY",
        port: int = None,  # 8080
        temperature: float = 1.0,
        base_url: str = "https://api.openai.com/v1"
    ):
        """
        Initializes the LLM Agent

        Parameters
        ----------
        prompt_folder : str
            The parent folder of the diffent prompt subfolders
        model_name : str
            The name of the model
        api_key : str
            The API key for the OpenAI API
        port : int
            The port of the OpenAI API
        """
        self.model_name = model_name
        self.api_key = api_key
        self.prompt_folder = prompt_folder
        self.temperature = temperature
        if local:
            self.client = OpenAI(
                api_key=self.api_key, base_url=base_url
            )
        else:
            self.client = AsyncOpenAI(
                api_key=self.api_key, base_url=base_url
            )

    def read_prompt(
        self,
        prompt_supercategory: str,
        prompt_subcategory: str,
        prompt_file_name: str
    ) -> str:
        """
        Reads a prompt from a file

        Parameters
        ----------
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
            self.prompt_folder,
            prompt_supercategory,
            prompt_subcategory,
            prompt_file_name
        )

        with open(prompt_path, "r") as file:
            prompt = file.read()

        return prompt

    async def send_prompt_async(
        self,
        developer_prompt: str,
        conversation_list: list[dict[str, str]],
    ) -> str:
        """
        Sends prompt and returns response asynchronously

        Parameters
        ----------
        developer_prompt : str
            The developer prompt
        conversation_list : list[dict[str, str]]
            The conversation list

        Returns
        -------
        str
            The response
        """
        messages = [{"role": "system", "content": developer_prompt}]
        for conversation in conversation_list:
            messages.append(conversation)

        logger.info(f"Sending prompt: {pprint.pformat(messages)}")
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature
        )
        return response.choices[0].message.content

    def send_prompt(
        self,
        developer_prompt: str,
        conversation_list: list[dict[str, str]],
    ) -> str:
        """
        Sends prompt and returns response synchronously

        Parameters
        ----------
        developer_prompt : str
            The developer prompt
        conversation_list : list[dict[str, str]]
            The conversation list

        Returns
        -------
        str
            The response
        """
        # Use asyncio.run() to execute the async function
        response_temp = asyncio.run(
            self.send_prompt_async(developer_prompt, conversation_list)
        )

        logger.info(
            "\n\n ----- Response:\n\n {response_temp}\n-----------------",
            response_temp=response_temp
        )

        return response_temp

    def send_prompt_simple(
        self,
        system_prompt: str,
        user_prompts: list[str],
    ):
        """
        Sends prompt and returns response

        Parameters
        ----------
        system_prompt : str
            The system prompt
        user_prompts : list[str]
            The user prompts
        """
        messages = [{"role": "system", "content": system_prompt}]

        for user_prompt in user_prompts:
            messages.append(
                {"role": "user", "content": user_prompt}
            )

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature
        )

        return response.choices[0].message.content

    def _extract_json_from_response(
        self,
        response: str
    ) -> dict:
        """
        Extracts the JSON from the response.

        Parameters
        ----------
        response : str
            The response to extract from.

        Returns
        -------
        dict
            The extracted JSON.
        """
        try:
            return json.loads(
                re.search(r"```json\s([\s\S]*?)```", response).group(1)
            )
        except (AttributeError, json.JSONDecodeError, IndexError):
            try:
                pattern = r"```json\s*\n([\s\S]*?)\n```"
                match = re.findall(pattern, response)[0]
                return match.replace("```json", "")
            except (AttributeError, json.JSONDecodeError, IndexError):
                try:
                    return json.loads(
                        re.search(r"```(.*?)```", response, re.DOTALL).group(1)
                    )
                except (AttributeError, json.JSONDecodeError, IndexError):
                    try:
                        return json.loads(response)
                    except (AttributeError, json.JSONDecodeError, IndexError) as e:
                        print(f"""
                        Json could not be found for response:
                        {response}
                        """)
                        raise e

    def load_yml(
        self,
        yml_path: str
    ) -> dict:
        """
        Loads a yml file

        Parameters
        ----------
        yml_path : str
            The path to the yml file

        Returns
        -------
        dict
            The loaded yml file
        """
        with open(yml_path, "r") as file:
            return yaml.safe_load(file)
