
class Entity_designation(LLMAgent):
    """
    Class Name
    """
    def __init__(
        self,
        prompt_folder: str,
        model_name: str = None,
        api_key: str = "YOUR_API_KEY",
        port: int = 8080,
        local: bool = False
    ):
        super().__init__(
            local=local,
            prompt_folder=prompt_folder,
            model_name=model_name,
            api_key=api_key,
            port=port
        )

    # TODO: Delete
    def get_persons_in_text(
        self,
        text: str,
        prompt_subfolder: str = "recognize",
        prompt_name: str = "extract_person.md"
    ) -> dict:
        """
        Extracts the persons present in a text

        Parameters
        ----------
        text : str
            The text to extract the persons from
        prompt_subfolder : str
            The subfolder of the prompts folder
        prompt_name : str
            The name of the prompt file

        Returns
        -------
        dict
            The extracted persons
        """
        extract_person_system = self.read_prompt(
            prompt_subfolder=prompt_subfolder,
            prompt_name=prompt_name,
        )
        response = self.send_prompt_simple(
            system_prompt=extract_person_system,
            user_prompts=[text],
        )
        return self._extract_json_from_response(response)

    def get_aliases_for_person(
        self,
        response_json: dict,
        text: str,
        prompt_subfolder: str = "recognize",
        prompt_name: str = "extract_alias.xml"
    ) -> dict:
        """
        Takes a text and a list of person names and extracts the aliases
        for each person

        Parameters
        ----------
        response_json : dict
            The response from the get_persons_in_text function
        text : str
            The text to extract the aliases from
        prompt_subfolder : str
            The subfolder of the prompt
        prompt_name : str
            The name of the prompt file

        Returns
        -------
        dict
            The extracted aliases and the persons they belong to
        """
        user_prompt = """
        <user_prompt>
            <persons_list>
        """
        for person in response_json['Persons']:
            user_prompt += f"<person>{person}</person>"
        user_prompt += f"""
            </persons_list>
            <text>
                {text}
            </text>
        </user_prompt>
        """

        return self.send_prompt_simple_extract_result(
            user_prompt=[user_prompt],
            prompt_subfolder=prompt_subfolder,
            prompt_name=prompt_name
        )

    def load_person_into_database(
        self,
        conn: Neo4jConnection,
        person_alias_dict: list,
    ) -> None:
        """
        Loads the persons and alias into the database

        Parameters
        ----------
        conn : Neo4jConnection
            The connection to the Neo4j database
        person_alias_dict : list
            The list of persons and their aliases

        Returns
        -------
        None
        """
        query = """
            UNWIND $persons AS person
            MERGE (p:Entity_designation {uuid: person.uuid})
            ON CREATE SET
                p.abbrevation = person.abbrevation,
                p.nick_name_alias = person.nick_name_alias,
                p.name = person.name
        """
        person_list_temp = [
            {
                "name": person,
                "abbrevation": aliases["Abbreviation"],
                "nick_name_alias": aliases["Nickname/Alias"],
                "uuid": str(uuid.uuid4())[:18]
            }
            for person, aliases in person_alias_dict.items()
        ]
        person_dict_temp = {
            "Persons": person_list_temp
        }
        conn.query(query, parameters={'persons': person_dict_temp["Persons"]})

    def create_persons_xml(
        self,
        conn: Neo4jConnection,
    ) -> str:
        """
        Loads the persons and alias from the database into an XML string

        Parameters
        ----------
        conn : Neo4jConnection
            The connection to the Neo4j database

        Returns
        -------
        str
            The XML string containing the persons and their aliases
        """
        query = """
        MATCH (designation:Entity_designation)
        RETURN designation
        """
        result = conn.query(query)
        prompt = "<person_list>"
        for i, node in enumerate(result):
            prompt += f"""<person_{i + 1}>
            <full_name>{node["designation"].get("name")}</full_name>
            <abbrevations>
            """
            if node["designation"].get("abbrevation"):
                for abbrevation in node["designation"].get("abbrevation"):
                    prompt += f"""<abbrevation>{abbrevation}</abbrevation>
                    """
            else:
                prompt += """<abbrevation></abbrevation>
                """
            prompt += """</abbrevations>
            <nick_name_aliases>
            """
            if node["designation"].get("nick_name_alias"):
                for nickname in node["designation"].get("nick_name_alias"):
                    prompt += f"""
                <alias>{nickname}</alias>
                    """
            else:
                prompt += """<alias></alias>
                """
            prompt += f"""</nick_name_aliases>
            <uuid>{node["designation"].get("uuid")}</uuid>
        </person_{i + 1}>
            """
        prompt += "</person_list>"
        return prompt

    def extract_codes_from_text(
        self,
        conn: Neo4jConnection,
        text: str,
        prompt_subfolder: str = "recognize",
        prompt_name: str = "extract_codes.xml"
    ) -> dict:
        """
        Extracts the codes from a text

        Parameters
        ----------
        conn : Neo4jConnection
            The connection to the Neo4j database
        text : str
            The text to extract the codes from
        prompt_subfolder : str
            The subfolder of the prompts folder
        prompt_name : str
            The name of the prompt file

        Returns
        -------
        dict
            The extracted codes
        """
        persons = self.create_persons_xml(conn=conn)
        user_prompt = f"""
            <text>
                {text}
            </text>
        {persons}
        """

        return self.send_prompt_simple_extract_result(
            user_prompt=[user_prompt],
            prompt_subfolder=prompt_subfolder,
            prompt_name=prompt_name
        )

    def extract_codes_from_dict(self, codes_dict) -> Union[list, list, list]:
        """
        Extracts the codes from the codes_dict and returns them in a list.

        Parameters:
        codes_dict : dict
            A dictionary containing the codes.

        Returns
        -------
        list
            A list containing the extracted codes.
        """
        def append_data(
            data_list: list,
            person_uuid: str,
            items: list,
            item_key: str
        ) -> None:
            """
            Appends extracted data from items to a target list.

            Parameters:
            data_list : list
                The target list to append the extracted data to.
            person_uuid : str
                The UUID of the entity the data was extracted from.
            items : list
                The items to extract data from.
            item_key : str
                The key to use for the extracted data.

            Returns
            -------
            None
            """
            for item in items:
                data_list.append(
                    {
                        "person_uuid": person_uuid,
                        "identifier": item["identifier"],
                        "context": item["context"],
                        "uuid": str(uuid.uuid4())[:18]
                    }
                )

        government_ids_list, codes_list, telephone_numbers_list = [], [], []

        for person_uuid, codes in codes_dict.items():
            for key, items in codes.items():
                if not items:
                    continue
                if key == "government_ids":
                    append_data(
                        government_ids_list,
                        person_uuid,
                        items,
                        "government_id"
                    )
                elif key == "codes":
                    append_data(
                        codes_list,
                        person_uuid,
                        items,
                        "code"
                    )
                elif key == "telephone_numbers":
                    append_data(
                        telephone_numbers_list,
                        person_uuid,
                        items,
                        "telephone_number"
                    )

        return government_ids_list, codes_list, telephone_numbers_list

    def create_code_relationship(
        self,
        type_node: str,
        type_relationship: str,
        entry_list: list,
        conn: Neo4jConnection
    ) -> None:
        """
        Creates a relationship between the entity designation and the
        extracted codes.

        Parameters
        ----------
        type_node : str
            The type of node to create
        type_relationship : str
            The type of relationship to create
        entry_list : list
            The list of entities to create the relationship with
        conn : Neo4jConnection
            The connection to the Neo4j database

        Returns
        -------
        None
        """
        query = f"""
        UNWIND $ids_list AS id
        MERGE (n:{type_node} {{uuid: id.uuid}})
        ON CREATE SET
                n.identifier = id.identifier,
                n.context = id.context

        // Ensure the Entity_designation node exists only once
        MERGE (p:Entity_designation {{uuid: id.person_uuid}})

        // Create the relationship
        MERGE (n)-[:{type_relationship}]->(p)
        """
        conn.query(query, parameters={'ids_list': entry_list})

    def check_codes_for_errors(
        self,
        text: str,
        codes_dict: dict,
        conn: Neo4jConnection,
    ) -> dict:
        """
        Checks the extracted codes for errors and prompts the LLM
        to correct them.

        Parameters
        ----------
        text : str
            The text to check for errors.
        codes_dict : dict
            A dictionary containing the extracted codes.
        conn : Neo4jConnection
            The connection to the Neo4j database.

        Returns
        -------
        dict
            The response from the LLM.
        """
        government_ids_to_check = []
        codes_to_check = []
        telephone_numbers_to_check = []
        for person_uuid, values in codes_dict.items():
            government_ids_to_check.extend([
                dict(x, **{
                    "type": "government_ids",
                    "person_uuid": person_uuid
                }) for x in values['government_ids']
            ])
            codes_to_check.extend([
                dict(x, **{
                    "type": "codes",
                    "person_uuid": person_uuid
                }) for x in values['codes']
            ])
            telephone_numbers_to_check.extend([
                dict(x, **{
                    "type": "telephone_numbers",
                    "person_uuid": person_uuid}
                ) for x in values['telephone_numbers']
            ])
        final_list = (
            government_ids_to_check
            + codes_to_check
            + telephone_numbers_to_check
        )

        wrong_entries = {}
        error_number = 1
        for entry in final_list:
            x = re.search(re.escape(entry["identifier"]), text)
            if x is None:
                wrong_entries[f"error_{error_number}"] = entry
                error_number += 1

        error_xml = "<errors>"
        for key, value in wrong_entries.items():
            error_xml += f"""<{key}>
                <context>{value["context"]}</context>
                <identifier>{value["identifier"]}</identifier>
                <identifier_typ>{value["type"]}</identifier_typ>
                <person_uuid>{value["person_uuid"]}</person_uuid>
            </{key}>
            """
        error_xml += "</errors>"

        user_prompt = f"""
        {self.create_persons_xml(conn=conn)}
        {error_xml}
        <text>
            {text}
        </text>
        """
        system_prompt = self.read_prompt(
            prompt_name="recheck_wrong_found.xml",
            prompt_subfolder="recognize"
        )
        response = self.send_prompt_simple(
            system_prompt=system_prompt,
            user_prompts=[user_prompt],
        )
        return self._extract_json_from_response(response)

    def extract_codes_and_link_entities(
        self,
        conn: Neo4jConnection,
        text: str,
        prompt_subfolder: str = "recognize",
        prompt_name: str = "extract_codes.xml"
    ) -> None:
        """
        This function extracts the codes from the text and
        links them to the entities in the database.

        Parameters
        ----------
        conn : Neo4jConnection
            The connection to the Neo4j database
        text : str
            The text to extract the codes from
        prompt_subfolder : str
            The subfolder of the prompts folder
        prompt_name : str
            The name of the prompt file

        Returns
        -------
        None
        """

        codes_dict = self.extract_codes_from_text(
            conn=conn,
            text=text,
            prompt_subfolder=prompt_subfolder,
            prompt_name=prompt_name
        )

        government_ids_list, codes_list, telephone_numbers_list = (
            self.extract_codes_from_dict(codes_dict)
        )

        self.create_code_relationship(
            type_node="GovernmentID",
            type_relationship="HAS_GOVERNMENT_ID",
            entry_list=government_ids_list,
            conn=conn
        )
        self.create_code_relationship(
            type_node="Codes",
            type_relationship="HAS_CODE",
            entry_list=codes_list,
            conn=conn
        )
        self.create_code_relationship(
            type_node="Telephon_number",
            type_relationship="HAS_TELEPHONE_NUMBER",
            entry_list=telephone_numbers_list,
            conn=conn
        )

    def send_prompt_simple_extract_result(
        self,
        user_prompt: list[str],
        prompt_subfolder: str,
        prompt_name: str
    ) -> dict:
        """
        Reads and sends the prompt to extract the result

        Parameters
        ----------
        text : str
            The text to extract the result from
        prompt_subfolder : str
            The subfolder of the prompts folder
        prompt_name : str
            The name of the prompt file

        Returns
        -------
        dict
            The extracted result
        """
        system_prompt = self.read_prompt(
            prompt_subfolder=prompt_subfolder,
            prompt_name=prompt_name,
        )
        response = self.send_prompt_simple(
            system_prompt=system_prompt,
            user_prompts=user_prompt,
        )
        return self._extract_json_from_response(response)

    def extract_location(
        self,
        text: str,
        prompt_subfolder: str = "recognize",
        prompt_name: str = "extract_location.xml"
    ) -> dict:
        return self.send_prompt_simple_extract_result(
            user_prompt=[f"<text>{text}</text>"],
            prompt_subfolder=prompt_subfolder,
            prompt_name=prompt_name
        )

    def _populate_location_dict(
        self,
        category: str,
        all_location_list: list[dict],
        object_dict: dict
    ) -> None:
        """
        Populates the object_dict with the location data

        Parameters
        ----------
        category : str
            The category of the location
        all_location_list : list[dict]
            The list of all locations
        object_dict : dict
            The object dict to populate

        Returns
        -------
        None
        """
        for entry in all_location_list[category]:
            object_dict[str(uuid.uuid4())[:18]] = {
                "category": category,
                "context": entry["context"],
                "name": entry["item"]
            }

    def load_location_into_database(
        self,
        conn: Neo4jConnection,
        location_dict: dict,
    ) -> None:
        """
        Takes the location data and loads it into the database

        Parameters
        ----------
        conn : Neo4jConnection
            The connection to the Neo4j database
        location_dict : list
            The location data of different categories

        Returns
        -------
        None
        """
        categories = [
            "address", "district", "city", "area",
            "country", "continent", "landmark"
        ]

        mapping_dict = {category: {} for category in categories}

        for element in mapping_dict.keys():
            self._populate_location_dict(
                category=element,
                all_location_list=location_dict,
                object_dict=mapping_dict[element]
            )

        list_of_dicts = [d for d in mapping_dict.values()]

        combined_dicts = {k: v for d in list_of_dicts for k, v in d.items()}
        person_dict_temp = {
            "Locations": [
                {
                    "name": location_values["name"],
                    "context": location_values["context"],
                    "category": location_values["category"],
                    "uuid": location
                }
                for location, location_values in combined_dicts.items()
            ]
        }

        query = """
            UNWIND $locations AS location
            MERGE (l:Location {uuid: location.uuid})
            ON CREATE SET
                l.name = location.name,
                l.context = location.context,
                l.category = location.category
        """

        conn.query(
            query,
            parameters={'locations': person_dict_temp["Locations"]}
        )

    def create_location_xml(
        self,
        conn: Neo4jConnection,
    ) -> str:
        """
        Creates an XML string containing the location data

        Parameters
        ----------
        conn : Neo4jConnection
            The connection to the Neo4j database

        Returns
        -------
        str
            The XML string containing the location data
        """
        query = """
        MATCH (location:Location)
        RETURN location
        """
        result = conn.query(query)
        prompt = "<location_list>"
        for i, node in enumerate(result):
            prompt += f"""<location_{i + 1}>
            <name>{node["location"].get("name")}</name>
            <category>{node["location"].get("category")}</category>
            <context>{node["location"].get("context")}</context>
            <uuid>{node["location"].get("uuid")}</uuid>
            </location_{i + 1}>"""

        prompt += "</location_list>"
        return prompt

    def extract_links_individual_with_location(
        self,
        conn: Neo4jConnection,
        text: str,
        prompt_subfolder: str = "link",
        prompt_name: str = "link_location_to_person.xml"
    ) -> dict:
        """
        This function extracts the links between the persons and the locations

        Parameters
        ----------
        conn : Neo4jConnection
            The connection to the Neo4j database
        text : str
            The text to extract the links from
        prompt_subfolder : str
            The subfolder of the prompts folder
        prompt_name : str
            The name of the prompt file

        Returns
        -------
        dict
            The extracted links
        """
        person_xml = self.create_persons_xml(conn=conn)
        location_xml = self.create_location_xml(conn=conn)

        user_prompt = f"""
        <text>{text}</text>
        {person_xml}
        {location_xml}
        """

        return self.send_prompt_simple_extract_result(
            user_prompt=[user_prompt],
            prompt_subfolder=prompt_subfolder,
            prompt_name=prompt_name
        )

    def load_links_individual_with_location_into_database(
        self,
        conn: Neo4jConnection,
        linkage_dict: dict,
    ) -> None:
        """
        Loads the links between the persons and the locations into the database

        Parameters
        ----------
        conn : Neo4jConnection
            The connection to the Neo4j database
        location_dict : dict
            The dictionary containing the links between the persons
            and the locations

        Returns
        -------
        None
        """
        query = """
            UNWIND $Links AS link
            MATCH (p:Entity_designation {uuid: link.person_uuid})
            MATCH (l:Location {uuid: link.location_uuid})
            MERGE (l)-[r:HAS_LOCATION]->(p)
            ON CREATE SET r.context = link.context
        """
        linkage_dict_temp = {
            "Links": [
                {
                    "person_uuid": key,
                    "location_uuid": val["uuid"],
                    "context": val["context"]
                }
                for key, value in linkage_dict.items() for val in value
            ]
        }

        conn.query(query, parameters={'Links': linkage_dict_temp["Links"]})

    def extract_health_information(
        self,
        conn: Neo4jConnection,
        text: str,
        prompt_subfolder: str = "recognize",
        prompt_name: str = "extract_health.xml"
    ):
        """
        This function extracts the health information about individuals
        from the text

        Parameters
        ----------
        conn : Neo4jConnection
            The connection to the Neo4j database
        text : str
            The text to extract the links from
        prompt_subfolder : str
            The subfolder of the prompts folder
        prompt_name : str
            The name of the prompt file

        Returns
        -------
        dict
            The extracted links
        """
        person_xml = self.create_persons_xml(conn=conn)

        user_prompt = f"""
        <text>{text}</text>
        {person_xml}
        """

        return self.send_prompt_simple_extract_result(
            user_prompt=[user_prompt],
            prompt_subfolder=prompt_subfolder,
            prompt_name=prompt_name
        )
