import uuid
import os
from openai import OpenAI
import regex as re
import json
import pprint
from typing import Union

# Zietiere hierfür: https://github.com/FullStackRetrieval-com/RetrievalTutorials/blob/main/tutorials/LevelsOfTextSplitting/5_Levels_Of_Text_Splitting.ipynb
# TODO: Docstrings schreiben
# TODO: Experiment über die erstellte Chunkgröße


class AgenticChunker:
    """
    Agentically chunks propositions into chunks

    Parameters
    ----------
    prompt_folder : str
        The folder where the prompts are stored
    model_name : str
        The name of the model to use
    api_key : str
        The API key to use
    port : int
        The port to use
    generate_new_metadata_ind : bool
        Whether or not to generate new metadata
    print_logging : bool
        Whether or not to print logging

    Attributes
    ----------
    api_key : str
        The API key
    client : OpenAI
        The OpenAI client
    prompt_folder : str
        The folder where the prompts are stored
    chunks : dict
        The chunks
    id_truncate_limit : int
        The ID truncate limit
    generate_new_metadata_ind : bool
        Whether or not to generate new metadata
    print_logging : bool
        Whether or not to print logging
    model_name : str
        The model name

    Methods
    -------
    send_prompt(system_prompt: str, user_prompts: list[str], temperature: float = 0)
        Sends prompt and returns response
    get_default_model()
        Fetches the default model
    _create_new_chunk(proposition)
        Creates a new chunk with the given proposition
    _get_new_chunk_summary(proposition)
        Creates a new summary for a new chunk that the proposition will go into
    _get_new_chunk_title(summary)
        Creates a new title for a new chunk without title
    add_propositions(propositions)
        Adds multiple propositions to the chunker
    add_proposition(proposition)
        Adds a proposition to the chunker
    add_proposition_to_chunk(chunk_id, proposition)
        Adds a proposition to a chunk
    _update_chunk_summary(chunk)
        Updates the summary of a chunk
    _update_chunk_title(chunk)
        Updates the title of a chunk
    _extract_json_from_response(response)
        Extracts the JSON from the response
    get_chunk_outline()
        Gets the overview of the chunks
    _find_relevant_chunk(proposition)
        Finds the relevant chunkID to which the given proposition should be added
    get_chunks(type)
        Returns the chunks in the specified format
    pretty_print_chunks()
        Pretty prints the chunks
    """

    def __init__(
        self,
        prompt_folder: str,
        model_name: str = None,
        api_key: str = "YOUR_API_KEY",
        port: int = 8080,
        generate_new_metadata_ind: bool = True,
        print_logging: bool = True
    ):
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key, base_url=f"http://0.0.0.0:{port}/v1")
        self.prompt_folder = prompt_folder
        self.chunks = {}
        self.id_truncate_limit = 8

        # Whether or not to update/refine summaries and titles as you get new information
        self.generate_new_metadata_ind = generate_new_metadata_ind
        self.print_logging = print_logging

        # self.model_name = model_name or self.get_default_model()

    def send_prompt(
        self,
        system_prompt: str,
        user_prompts: list[str],
        temperature: float = 0
    ):
        """
        Sends prompt and returns response

        Parameters
        ----------
        system_prompt : str
            The system prompt
        user_prompts : list[str]
            The user prompts
        temperature : float
            The temperature of the LLM call
        """
        messages = [{"role": "system", "content": system_prompt}]

        for user_prompt in user_prompts:
            messages.append(
                {"role": "user", "content": user_prompt}
            )

        response = self.client.chat.completions.create(
            model="benedikt",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
        )

        return self._extract_json_from_response(
            response.choices[0].message.content
        )

    def get_default_model(self) -> str:
        """Fetches the default model."""
        try:
            models = self.client.models.list().data
            if models:
                return models[0].id
            else:
                raise ValueError("No models available from the API.")
        except Exception as e:
            raise RuntimeError(f"Failed to fetch models: {str(e)}")

    def _create_new_chunk(self, proposition) -> None:
        """
        Creates a new chunk with the given proposition

        Parameters
        ----------
        proposition : str
            The proposition to be added to the new chunk

        Returns
        -------
        None
        """
        new_chunk_id = str(uuid.uuid4())[
            : self.id_truncate_limit
        ]
        new_chunk_summary = self._get_new_chunk_summary(proposition)
        new_chunk_title = self._get_new_chunk_title(new_chunk_summary)

        self.chunks[new_chunk_id] = {
            "chunk_id": new_chunk_id,
            "propositions": [proposition],
            "title": new_chunk_title,
            "summary": new_chunk_summary,
            "chunk_index": len(self.chunks),
        }
        if self.print_logging:
            print(f"Created new chunk ({new_chunk_id}): {new_chunk_title}")

    def _get_new_chunk_summary(self, proposition) -> str:
        """
        Creates a new summary for a new chunk that the proposition will go into

        Parameters
        ----------
        proposition : str
            The proposition that will go into the new chunk

        Returns
        -------
        str
            The summary of the new chunk
        """
        with open(f"{self.prompt_folder}/create_new_summary_of_chunk.txt", "r") as f:
            system_prompt = f.read()
        user_prompt = (
            f"Determine the summary of the new chunk that this proposition will go into:\n{proposition}"
        )

        return (
            self.send_prompt(system_prompt, user_prompts=[user_prompt])["summary"]
        )

    def _get_new_chunk_title(self, summary) -> str:
        """
        Creates a new title for a new chunk without title

        Parameters
        ----------
        summary : str
            The summary of the new chunk

        Returns
        -------
        str
            The title of the new chunk
        """
        with open(f"{self.prompt_folder}/create_new_chunk_title.txt", "r") as f:
            system_prompt = f.read()
        user_prompt = f"Determine the title of the chunk that this summary belongs to:\n{summary}"

        return (
            self.send_prompt(system_prompt, user_prompts=[user_prompt])["title"]
        )

    def add_propositions(self, propositions: list[str]) -> None:
        """
        Adds multiple propositions to the chunker

        Parameters
        ----------
        propositions : list[str]
            The propositions to be added to the chunker

        Returns
        -------
        None
        """
        for proposition in propositions:
            self.add_proposition(proposition)

    def add_proposition(self, proposition: str) -> None:
        """
        Adds a proposition to the chunker

        Parameters
        ----------
        proposition : str
            The proposition to be added to the chunker

        Returns
        -------
        None
        """
        if self.print_logging:
            print(f"\nAdding: '{proposition}'")
        chunk_id = None
        if len(self.chunks) == 0:
            if self.print_logging:
                print("No chunks, creating a new one")
        else:
            chunk_id = self._find_relevant_chunk(proposition)

        if chunk_id != "No chunk" and chunk_id is not None:
            if self.print_logging:
                print(
                    f"Chunk Found ({self.chunks[chunk_id]['chunk_id']}), adding to: {self.chunks[chunk_id]['title']}"
                )
            self.add_proposition_to_chunk(chunk_id, proposition)
        else:
            if self.print_logging:
                print("No chunks found")
            # If a chunk wasn't found, then create a new one
            self._create_new_chunk(proposition)

    def add_proposition_to_chunk(
        self,
        chunk_id: str,
        proposition: str
    ) -> None:
        """
        Adds a proposition to a chunk

        Parameters
        ----------
        chunk_id : str
            The chunk ID to which the proposition should be added
        proposition : str
            The proposition to be added to the chunk

        Returns
        -------
        None
        """
        self.chunks[chunk_id]["propositions"].append(proposition)

        if self.generate_new_metadata_ind:
            # We don't need to generate a new summary, title for a chunk with a 
            # single proposition in it
            if len(self.chunks[chunk_id]["propositions"]) > 1:
                self.chunks[chunk_id]["summary"] = self._update_chunk_summary(
                    self.chunks[chunk_id]
                )
                self.chunks[chunk_id]["title"] = self._update_chunk_title(
                    self.chunks[chunk_id]
                )

    def _update_chunk_summary(self, chunk: dict) -> str:
        """
        Updates the summary of a chunk

        Parameters
        ----------
        chunk : dict
            The chunk to update the summary of

        Returns
        -------
        str
            The updated summary of the chunk
        """
        with open(f"{self.prompt_folder}/update_chunk_summary.txt", "r") as f:
            system_prompt = f.read()
        current_summary = chunk["summary"]
        propositions = chunk["propositions"]

        user_prompt = f"""
        Current summary of the chunk: {current_summary}; Propositions belonging to the chunk: {propositions}
        """

        return self.send_prompt(system_prompt, user_prompts=[user_prompt])["updated_summary"]

    def _update_chunk_title(self, chunk: dict) -> str:
        """
        Updates the title of a chunk

        Parameters
        ----------
        chunk : dict
            The chunk to update the title of

        Returns
        -------
        str
            The updated title of the chunk
        """
        with open(f"{self.prompt_folder}/update_chunk_title.txt", "r") as f:
            system_prompt = f.read()

        summary = chunk["summary"]
        propositions = chunk["propositions"]
        current_title = chunk["propositions"]

        user_prompt = f"""
        Summary of the chunk: {summary}; Propositions belonging to the chunk: {propositions}; Current title: {current_title}
        """

        return self.send_prompt(system_prompt, user_prompts=[user_prompt])["updated_title"]

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
        except AttributeError:
            try:
                return json.loads(
                    re.search(r"```json\s([\s\S]*?)```", response).group(1)
                )
            except AttributeError:
                print(f"""
                Json could not be found for response:
                {response}
                """)
                return None

    def get_chunk_outline(self) -> str:
        """
        Gets the overview of the chunks

        Parameters
        ----------
        None

        Returns
        -------
        str
            The chunk outline
        """
        chunk_outline = ""

        for _, chunk in self.chunks.items():
            single_chunk_string = (
                f"""Chunk ID: {chunk['chunk_id']}\nChunk Name: {chunk['title']}\nChunk Summary: {chunk['summary']}\n\n"""
            )

            chunk_outline += single_chunk_string

        return chunk_outline

    def _find_relevant_chunk(self, proposition: str) -> str:
        """
        Finds the relevant chunkID to which the given proposition should be added

        Parameters
        ----------
        proposition : str
            The proposition to be added to a chunk

        Returns
        -------
        str
            The relevant chunk ID
        """
        current_chunk_outline = self.get_chunk_outline()

        with open(f"{self.prompt_folder}/find_relevant_chunk.txt", "r") as f:
            system_prompt = f.read()
        first_user_prompt = (
            f"Current Chunks:\n--Start of current chunks--\n{current_chunk_outline}\n--End of current chunks--"
        )
        second_user_prompt = (
            f"Determine if the following statement should belong to one of the chunks outlined:\n{proposition}."
        )
        messages = [{"role": "system", "content": system_prompt}]
        user_prompts = [first_user_prompt, second_user_prompt]
        for user_prompt in user_prompts:
            messages.append(
                {"role": "user", "content": user_prompt}
            )
        response = self.client.chat.completions.create(
            model="benedikt",
            messages=messages,
            temperature=0,
        )
        answer_dict = self._extract_json_from_response(
            response.choices[0].message.content
        )
        try:
            return answer_dict["chunk_id"]
        except TypeError:
            print(answer_dict)
            return None

    def _find_relevant_chunk_backup(self, proposition) -> str:
        """
        Finds the relevant chunkID to which the given proposition should be added

        Parameters
        ----------
        proposition : str
            The proposition to be added to a chunk

        Returns
        -------
        str
            The relevant chunk ID
        """
        current_chunk_outline = self.get_chunk_outline()

        with open(f"{self.prompt_folder}/find_relevant_chunk.txt", "r") as f:
            system_prompt = f.read()
        first_user_prompt = (
            f"""
            Current Chunks:\n--Start of current chunks--\n{current_chunk_outline}\n--End of current chunks--
            Determine if the following statement should belong to one of the chunks outlined:\n{proposition}
            """
        )
        # second_user_prompt = (
        #    f"Determine if the following statement should belong to one of the chunks outlined:\n{proposition}"
        # )

        answer_dict = self.send_prompt(
            system_prompt,
            user_prompts=[first_user_prompt]
        )

        if "chunk_ids" in answer_dict:
            chunk_id = answer_dict["chunk_ids"]
            if len(chunk_id) == self.id_truncate_limit:
                return chunk_id
        return None

    def get_chunks(
        self,
        type: str = "dict"
    ) -> Union[dict, list]:
        """
        Returns the chunks in the specified format

        Parameters
        ----------
        type : str
            The type of format to return the chunks in

        Returns
        -------
        Union[dict, list]
            The chunks in the specified format
        """
        if type == "dict":
            return self.chunks
        if type == "list_of_strings":
            chunks = []
            for chunk_id, chunk in self.chunks.items():
                chunks.append(" ".join([x for x in chunk["propositions"]]))
            return chunks

    def pretty_print_chunks(self) -> None:
        """
        Pretty prints the chunks

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        print(f"\nThere are {len(self.chunks)} chunks\n")
        for chunk_id, chunk in self.chunks.items():
            print(f"Chunk #{chunk['chunk_index']}")
            print(f"Chunk ID: {chunk_id}")
            print(f"Summary: {chunk['summary']}")
            print("Propositions:")
            pprint.pp(chunk["propositions"])
