from neo4j import GraphDatabase
import json


class Neo4jConnection:
    def __init__(self, uri, user, pwd):
        self.__uri = uri
        self.__user = user
        self.__pwd = pwd
        self.__driver = None
        try:
            self.__driver = GraphDatabase.driver(
                self.__uri,
                auth=(self.__user, self.__pwd)
            )
        except Exception as e:
            print("Failed to create the driver:", e)

    def close(self):
        if self.__driver is not None:
            self.__driver.close()

    def query(self, query, parameters=None, db=None):
        assert self.__driver is not None, "Driver not initialized!"
        session = None
        response = None
        try:
            session = self.__driver.session(database=db) if db is not None \
                else self.__driver.session()
            response = list(session.run(query, parameters))
        except Exception as e:
            print("Query failed:", e)
        finally:
            if session is not None:
                session.close()
        return response

    def read_persons(self, doc_id: str) -> str:
        """
        Reads the persons from the database and returns them as a JSON string

        Parameters
        ----------
        doc_id : str
            The ID of the document.

        Returns
        -------
        str
            The persons as a JSON string
        """

        query = f"""
        MATCH (designation:Entity_designation)
        WHERE designation.doc = {doc_id}
        RETURN designation
        """
        result = self.query(query)

        person_dict = {}
        for person in result:
            person_dict[person["designation"].get("uuid")] = {
                "full name": person["designation"].get("full_name"),
                "abbreviations": person["designation"].get("abbreviations"),
                "aliases": person["designation"].get("aliases"),
            }

        return json.dumps(person_dict)

    def create_nodes_pii_independent(
        self,
        pii: str,
        result: dict[str, dict[str, str, str, str, str]],
        doc_id: str
    ) -> None:
        """
        Takes the results and creates nodes for each result

        Parameters
        ----------
        property : str
            The property which the nodes will be created for
        result : dict
            The result of the request to the LLM
        doc_id : str
            The ID of the document.

        Returns
        -------
        None
        """
        pii = pii.title()
        try:
            node_dict = {
                pii: [
                    {
                        "identifier": value["identifier"].lower(),
                        "context": value["context"],
                        "uuid": key
                    }
                    for result_dict in result
                    for key, value in result_dict.items()
                ]
            }
            query = f"""
                UNWIND $piis AS pii
                MERGE (p:{pii} {{uuid: pii.uuid}})
                ON CREATE SET p.uuid = pii.uuid
                SET p.identifier = pii.identifier
                SET p.context = pii.context
                SET p.doc_id = {doc_id}
            """

            self.query(
                query,
                parameters={'piis': node_dict[pii]}
            )
        except AttributeError as e:
            print(e)
            print(pii)
            print(result)
            raise AttributeError("Something went wrong.")

    def create_nodes_pii(
        self,
        pii: str,
        result: dict[str, dict[str, str, str, str, str]],
        doc_id: str
    ) -> None:
        """
        Takes the results and creates nodes for each result

        Parameters
        ----------
        property : str
            The property which the nodes will be created for
        result : dict
            The result of the request to the LLM
        doc_id : str
            The ID of the document.

        Returns
        -------
        None
        """
        pii = pii.title()
        node_dict = {
            pii: [
                {
                    "name": value["identifier"].lower()
                }
                for _, value in result.items()
            ]
        }

        query = f"""
        UNWIND $piis AS pii
        MERGE (p:{pii} {{name: pii.name}})
        SET p.doc_id = $doc_id
        """
        self.query(
            query,
            parameters={'piis': node_dict[pii], 'doc_id': doc_id}
        )

    def catch_key_exception(self, value: dict[str, str]) -> str:
        """
        Catches a key error exception and returns the value if it exists

        Parameters
        ----------
        key : str
            The key to be checked
        value : dict
            The dictionary to be checked

        Returns
        -------
        str
            The value if it exists, otherwise None
        """
        try:
            if type(value["full name"]) is list:
                if value["full name"]:
                    return value["full name"][-1]
                else:
                    return None
            else:
                return value["full name"]
        except KeyError:
            if type(value["full_name"]) is list:
                if value["full_name"]:
                    return value["full_name"][-1]
                else:
                    return None
            else:
                return value["full_name"]

    def create_nodes_individual(
        self,
        result: dict[str, dict[str, str, str, str, str]],
        doc_id: str
    ) -> None:
        """
        Takes the results and creates nodes for each individual

        Parameters
        ----------
        result : dict
            The result of the individual extraction from the LLM
        doc_id : str
            The ID of the document.

        Returns
        -------
        None
        """
        node_dict = {
            "Entity_designation": [
                {
                    "full_name": self.catch_key_exception(value),
                    "abbreviations": value["abbreviations"],
                    "aliases": value["aliases"],
                    "uuid_person": uuid,
                }
                for uuid, value in result.items()
            ]
        }
        query = """
            UNWIND $individuals AS individual
            MERGE (i:Entity_designation {uuid: individual.uuid_person})
            ON CREATE SET i.full_name = individual.full_name
            SET i.abbreviations = individual.abbreviations
            SET i.aliases = individual.aliases
            SET i.doc_id = $doc_id
        """
        self.query(
            query,
            parameters={
                'individuals': node_dict["Entity_designation"],
                'doc_id': doc_id
            }
        )

    def create_relationships(
        self,
        property: str,
        result: dict[str, dict[str, str, str, str, str]]
    ) -> None:
        """
        Takes the results and creates relationships between the nodes

        Parameters
        ----------
        property : str
            The property which the nodes represent
        result : dict
            The result of the request to the LLM

        Returns
        -------
        None
        """
        links_dict = {
            "Links": [
                {
                    "node_name": value["identifier"],
                    "context": value["context"],
                    "person_uuid": value["person_uuid"],
                }
                for _, value in result.items()
            ]
        }
        property = property.title()
        query = f"""
            UNWIND $Links as link
            MATCH (e:Entity_designation {{uuid: link.person_uuid}})
            MATCH (p:{property} {{name: link.node_name}})
            MERGE (p)-[r:HAS_{property.upper()}]->(e)
            ON CREATE SET r.context = [link.context]
            ON MATCH SET r.context = COALESCE(r.context, []) + link.context
        """

        self.query(
            query,
            parameters={"Links": links_dict["Links"]}
        )

    def drop_node_category(
        self,
        category: str,
        doc_id: str
    ) -> None:
        """
        Drops all nodes of a certain category

        Parameters
        ----------
        category : str
            The category of the nodes to be dropped
        doc_id : str
            The ID of the document.

        Returns
        -------
        None
        """
        query = f"""
        MATCH (n:{category})
        WHERE n.doc_id = {doc_id}
        DETACH DELETE n
        RETURN n
        """
        self.query(query)

    def save_nodes_as_json(
        self,
        path: str,
        doc_id: str
    ) -> None:
        """
        Saves the nodes as a JSON file

        Parameters
        ----------
        path : str
            The path to the JSON file
        doc_id : str
            The ID of the document.

        Returns
        -------
        None
        """
        query = f"""
        MATCH (n)
        WHERE n.doc_id = {doc_id}
        RETURN n
        """
        result = self.query(query)
        gathered_dict = []
        for data in result:
            gathered_dict.append(next(iter(data.data().values())))
        with open(path, 'w') as f:
            json.dump(gathered_dict, f, indent=2)
