from __future__ import annotations 
import uuid
import os
from openai import OpenAI
import json
import pprint
from typing import Union, List
from dataclasses import dataclass, field


@dataclass
class Dates:
    """
    Represents any date or description of a date within a text.

    Initializes the Date class, it should only be initialized
    with one argument.

    Attributes
    ----------
    description_of_date : str
        The text from the document that contains the description of the date.
    date : str
        The text from the document that contains the date.
    duration : str
        The text from the document that contains the duration.
    uuid : uuid.UUID
        The unique identifier of this Dates instance.
    """
    description_of_date: str = None
    date: str = None
    duration: str = None
    uuid: uuid.UUID = field(default_factory=uuid.uuid4)

    def __post_init__(self):
        non_none_count = sum(
            attr is not None for attr in [
                self.description_of_date, self.date, self.duration
            ]
        )
        if non_none_count > 1:
            raise ValueError("Only one of the attributes should be set")


@dataclass
class Location:
    """
    Represents any location of a date within a text.

    Attributes
    ----------
    address : list of str
        The text from the document that contains the address.
    district : list of str
        The text from the document that contains the district.
    city : list of str
        The text from the document that contains the city.
    country : list of str
        The text from the document that contains the country.
    continent : list of str
        The text from the document that contains the continent.
    near : list of Location
        The location that is near this location.
    uuid : uuid.UUID
        The unique identifier of this Dates instance.
    """
    address: List[str]
    district: List[str]
    city: List[str]
    country: List[str]
    continent: List[str]
    near: List[Location] = field(default_factory=list)
    uuid: uuid.UUID = field(default_factory=uuid.uuid4)


@dataclass
class Code:
    """
    Represents any code or identifier capable of uniquely identifying
    an individual within a text.

    Attributes
    ----------
    telephone_number : str
        The text from the document that contains the telephone number
    government_id_number : str
        The text from the document that contains the government ID number
    identification_number : str
        The text from the document that contains the identification number
    """
    telephone_number: str
    government_id_number: str
    identification_number: str


@dataclass
class Entity_designation:
    """
    Represents any means to refer to an individual within a text.

    Attributes
    ----------
    full_name : list of str
        The full name of the individual
    nickname_or_alias : list of str
        The nickname or alias of the individual
    abbreviation : list of str
        The abbreviation of the individual
    social_media_handle : list of str
        The social media handle of the individual
    code : Code
        The code or identifier capable of uniquely identifying individual
    """
    full_name: List[str]
    nickname_or_alias: List[str]
    abbreviation: List[str]
    social_media_handle: List[str]
    code: Code


class Individual:
    """
    Represents an individual within a text.

    Attributes
    ----------
    entity_designation : Entity_designation
        The means to refer to the individual
    demographics : Demographics
        The demographic information of the individual
    uuid : uuid.UUID
        The unique identifier of the individual
    """
    def __init__(
        self,
        entity_designation: Entity_designation,
    ):
        """
        Initializes the individual class

        Parameters
        ----------
        entity_designation : Entity_designation
            The means to refer to the individual
        """
        self.entity_designation = entity_designation
        self.demographics = Demographics()
        self.uuid = uuid.uuid4()


@dataclass
class Health:
    """
    Represents any health information of an individual within a text.

    Attributes
    ----------
    medication : list of str
        Any medication the individual is currently taking or has ever taken.
    blood_type : list of str
        Any mention of the blood type of the individual.
    medical_history : list of str
        Any medical interventions the patient has undergone.
    diagnosis : list of str
        Any illness, be it physical or psychological,
        from which the individual suffers
    vaccination_status : list of str
        Any mention of the vaccination status of the individual.
    """
    medication: List[str] = field(default_factory=list)
    blood_type: List[str] = field(default_factory=list)
    medical_history: List[str] = field(default_factory=list)
    diagnosis: List[str] = field(default_factory=list)
    vaccination_status: List[str] = field(default_factory=list)


@dataclass
class Socioeconomic:
    """
    Represents any socioeconomic information of an individual within a text.

    Attributes
    ----------
    income : list of str
        Any mention of income received by the individual.
    housing : list of str
        Any specification of the individual’s housing,
        such as rental apartment or single-family home
    neighborhood : list of str
        Any specification of the residential neighborhood of the individual.
    social_class : list of str
        Any specification of the individual’s social class.
    """
    income: List[str] = field(default_factory=list)
    housing: List[str] = field(default_factory=list)
    neighborhood: List[str] = field(default_factory=list)
    social_class: List[str] = field(default_factory=list)


@dataclass
class Residence:
    """
    Represents any residence information of an individual within a text.

    Attributes
    ----------
    residing_at : Location | None
        The location where the individual resides.
    residing_since : Dates | None
        The date when the individual started residing at the location.
    """
    residing_at: Location | None = None
    residing_since: Dates | None = None


@dataclass
class Emotional_description:
    """
    Represents information about the emotional state of
    an individual within a text.

    Attributes
    ----------
    temperament : list of str
        Any mention of the temperament of the individual.
    emotions_moods : list of str
        Any mention of the emotions or moods of the individual.
    behavior : list of str
        Any mention of the behavior of the individual.
    """
    temperament: List[str] = field(default_factory=list)
    emotions_moods: List[str] = field(default_factory=list)
    behavior: List[str] = field(default_factory=list)


@dataclass
class Physical_description:
    """
    Represents any physical description of an individual within a text.

    Attributes
    ----------
    height : list of str
        Any mention of the height of the individual.
    weight : list of str
        Any mention of the body weight of the individual.
    hair_beard_style : list of str
        Any mention of the individual’s beard or hairstyle.
    hair_color : list of str
        Any mention of the individual’s hair colour.
    eye_color : list of str
        Any mention of the individual’s eye colour.
    skin_color : list of str
        Any mention of the individual’s skin colour.
    attractiveness : list of str
        Any mention of the attractiveness of the individual.
    """
    height: List[str] = field(default_factory=list)
    weight: List[str] = field(default_factory=list)
    hair_beard_style: List[str] = field(default_factory=list)
    hair_color: List[str] = field(default_factory=list)
    eye_color: List[str] = field(default_factory=list)
    skin_color: List[str] = field(default_factory=list)
    attractiveness: List[str] = field(default_factory=list)


@dataclass
class Heritage:
    """
    Represents any heritage information of an individual within a text.

    Attributes
    ----------
    childhood_description : list of str
        Any mention of how the individual experienced the childhood.
    countries_lived_in : list of str
        Any mention of a country the individual lived in.
    nationality : list of str
        Any mention of the nationality of the individual.
    ethnicity : list of str
        Any mention of the ethnicity of the individual.
    race : list of str
        Any mention of the race of the individual.
    languages_spoken : list of str
        Any mention of the languages in which the individual
        has a command of, or is able to communicate in.
    """
    childhood_description: List[str] = field(default_factory=list)
    countries_lived_in: List[str] = field(default_factory=list)
    nationality: List[str] = field(default_factory=list)
    ethnicity: List[str] = field(default_factory=list)
    race: List[str] = field(default_factory=list)
    languages_spoken: List[str] = field(default_factory=list)


@dataclass
class Relation_with_other_individuals:
    """
    Represents any relationship of an individual with
    other individuals within a text.

    Attributes
    ----------
    type_of_relationship : list of str
        The type of the relation between the individual and another one.
    person_with : Individual
        Any mention of any person the individual has any relationship with.
    """
    type_of_relationship: List[str] = field(default_factory=list)
    person_with: Individual = field(default_factory=list)


@dataclass
class Professional_life:
    """
    Represents any professional information of an individual within a text.

    Attributes
    ----------
    works_at : Membership
        Any mention of where a individual currently works
        or has worked in the past.
    """
    works_at: Membership = field(default_factory=list)


@dataclass
class Education_institute:
    """
    Represents any educational institute an individual
    has attended within a text.


    Attributes
    ----------
    studied_at : Organisation
        Any mention of any education institute the individual attended.
    enrolment_period : Dates
        The period of time the individual was enrolled in
        the education institute.
    """
    studied_at: Organisation = field(default_factory=list)
    enrolment_period: Dates = field(default_factory=list)


@dataclass
class University(Education_institute):
    """
    Represents any university information of an individual within a text.

    Attributes
    ----------
    subject_of_study : list of str
        Any mention of what subject the individual has studied.
    """
    subject_of_study: List[str] = field(default_factory=list)


@dataclass
class Research:
    """
    Represents any research information of an individual within a text.

    Attributes
    ----------
    research_interest : list of str
        Any mention of the individual's research interests.
    inventions : list of str
        Any mention of involvement in a scientific paper,
        either by citation or publication.
    involved_in_paper : list of str
        Any mention of an invention or patent by the individual.
    """
    research_interest: List[str] = field(default_factory=list)
    inventions: List[str] = field(default_factory=list)
    involved_in_paper: List[str] = field(default_factory=list)


@dataclass
class Worldview:
    """
    Represents any worldview information of an individual within a text.

    Attributes
    ----------
    religion : list of str
        Any mention of the religion to which the individual belongs.
    political_stance : list of str
        Any mention of the political stance of the individual.
    """
    religion: List[str] = field(default_factory=list)
    political_stance: List[str] = field(default_factory=list)


@dataclass
class Gender_sexual_orientation:
    """
    Represents any information about the gender or sexual orientation
    of an individual within a text.

    Attributes
    ----------
    gender : list of str
        Any mention of the gender of the individual.
    sexual_orientation : list of str
        Any mention of the sexual orientation of the individual.
    """
    gender: List[str] = field(default_factory=list)
    sexual_orientation: List[str] = field(default_factory=list)


@dataclass
class Family:
    """
    Represents any family information of an individual within a text.

    Attributes
    ----------
    marital_status : list of str
        Any mention of the marital status of the individual.
    family_size : list of str
        Any mention of the size of the individual's family.
    """
    marital_status: List[str] = field(default_factory=list)
    family_size: List[str] = field(default_factory=list)


@dataclass
class Age:
    """
    Represents any age information of an individual within a text.

    Attributes
    ----------
    age : list of str
        Any mention of the age of the individual as a number.
    birth_date : Dates | None = None
        Any mention of the individual's date of birth,
        even if this is not given in full
    birthplace : Location | None = None
        Any mention of the location where the individual was born.
    """
    age: List[str] = field(default_factory=list)
    birth_date: Dates | None = None
    birthplace: Location | None = None


class Demographics:
    """
    Represents any demographic information of an individual within a text.

    Attributes
    ----------
    health : Health
        Represents any health information of an individual within a text.
    socioeconomic : Socioeconomic
        Represents any socioeconomic information of an individual
        within a text.
    residence : Residence
        Represents any residence information of an individual within a text.
    emotional_description : Emotional_description
        Represents information about the emotional state of an individual
        within a text.
    member_of : list of Membership
        Represents any membership to an organisation of an individual
        within a text.
    physical_description : Physical_description
        Represents any physical description of an individual within a text.
    heritage : Heritage
        Represents any heritage information of an individual within a text.
    relation_with_other_individuals : list of Relation__individuals
        Represents any relationship of an individual with other individuals
        within a text.
    professional_life : list of Professional_life
        Represents any professional information of an individual within a text.
    research : Research
        Represents any research information of an individual within a text.
    school : list of Education_institute
        Represents any school an individual has attended within a text.
    university : list of University
        Represents any university information of an individual within a text.
    worldview : Worldview
        Represents any worldview information of an individual within a text.
    gender_sexual_orientation : Gender_sexual_orientation
        Represents any information about the gender or sexual orientation
        of an individual within a text.
    family : Family
        Represents any family information of an individual within a text.
    age : Age
        Represents any age information of an individual within a text.
    """
    def __init__(
        self
    ):
        self.health = Health()
        self.socioeconomic = Socioeconomic()
        self.residence = Residence()
        self.emotional_description = Emotional_description()
        self.member_of = []
        self.physical_description = Physical_description()
        self.heritage = Heritage()
        self.relation_with_other_individuals = []
        self.professional_life = []
        self.research = Research()
        self.school = []
        self.university = []
        self.worldview = Worldview()
        self.gender_sexual_orientation = Gender_sexual_orientation
        self.family = Family()
        self.age = Age()


class Organisation:
    """
    Represents an organisation within a text.

    Attributes
    ----------
    name : str
        The name of the organisation.
    address : list of Location
        The location of the organisation.
    characteristics : Organisation_characteristics
        Represents any characteristics of an organisation within a text.
    regulatory_compliance : Regulatory_compliance
        Represents any regulatory compliance information of an
        organisation within a text.
    aim_of_operations : Aim_of_operations
        Represents any aim of operations of an organisation within a text.
    customer_base : Customer_base
        Represents any customer base information of an organisation
        within a text.
    relation_with_other_organisations : list of Relation_with_other_organisations
        Represents any relationship of an organisation with other organisations
    technology_used : list of Technology_used
        Represents any technology used by an organisation within a text.
    financial : Finiancial
        Represents any financial information of an organisation within a text.
    departments : list of Department
        Represents any department of an organisation within a text.
    members : list of Membership
        Represents any membership to an organisation of an individual
        within a text.
    uuid : uuid.UUID
        The unique identifier of this Dates instance.
    """
    def __init__(
        self,
        name: Entity_designation,
        address: List[Location] = [],
    ):
        self.name = name
        self.name = address
        self.characteristics = Organisation_characteristics()
        self.regulatory_compliance = Regulatory_compliance()
        self.aim_of_operations = Aim_of_operations()
        self.customer_base = Customer_base()
        self.relation_with_other_organisations = []
        self.technology_used = []
        self.financial = Finiancial()
        self.departments = []
        self.members = []
        self.uuid = uuid.uuid4()


@dataclass
class Organisation_characteristics:
    """
    Represents any characteristics of an organisation within a text.

    Attributes
    ----------
    public_or_private : list of str
        Any mention of the public or private nature of
        the organisation.
    industry : list of str
        Any mention of industry the organisation is is active in.
    age : list of Dates
        Any mention of the age of the organisation.
    size : list of str
        Any mention of the size of the organisation.
    active_in_region : list of Location
        Any mention of the regions and/or locations where
        the organisation is active.
    prestige : list of str
        Any mention of the perceived prestige of the organisation.
    """
    public_or_private: List[str] = field(default_factory=list)
    industry: List[str] = field(default_factory=list)
    age: List[Dates] = field(default_factory=list)
    size: List[str] = field(default_factory=list)
    active_in_region: List[Location] = field(default_factory=list)
    prestige: List[str] = field(default_factory=list)


@dataclass
class Regulatory_compliance:
    """
    Represents any regulatory compliance information of an
    organisation within a text.

    Attributes
    ----------
    follows_regulations : list of str
        Any mention of a regulation to which an organisation
        is subject or with which it must comply
    has_certifications : list of str
        Any mention of a certificate that the organisation already
        has or tries to acquire.

    """
    follows_regulations: List[str] = field(default_factory=list)
    has_certifications: List[str] = field(default_factory=list)


@dataclass
class Aim_of_operations:
    """
    Represents any aim of operations of an organisation within a text.

    Attributes
    ----------
    goal : list of str
        Any mention of financial, educational, political or
        other goals that the organisation may have.
    end_product : list of str
        Any mention of end products produced by the organisation,
            whether tangible or intangible.
    primary_activities : list of str
        Any mention of the primary Activities of the organisation.
    """
    goal: List[str] = field(default_factory=list)
    end_product: List[str] = field(default_factory=list)
    primary_activities: List[str] = field(default_factory=list)


@dataclass
class Customer_base:
    """
    Represents any customer base information of an organisation within a text.

    Attributes
    ----------
    b2b_or_b2c : list of str
        Any mention of whether the company's main activity is B2B or B2C.
    income : list of str
        Any mention of the income level of the customer
        that the organisation is trying to target.
    gender : list of str
        Any mention of the gender of the customer that
        the organisation is trying to target.
    age : list of str
        Any mention of the age of the customer that
        the organisation is trying to target.
    """
    b2b_or_b2c: List[str] = field(default_factory=list)
    income: List[str] = field(default_factory=list)
    gender: List[str] = field(default_factory=list)
    age: List[str] = field(default_factory=list)


@dataclass
class Relation_with_other_organisations:
    """
    Represents any relationship of an organisation with other organisations

    Attributes
    ----------
    volume : list of str
        Any mention of the volume of any kind by the
        organisation with another organisation
    frequency : list of str
        Any mention of the frequency of the relation
        by the organisation with another organisation.
    relation_with : Organisation
        The external organisation the organisation has contact with.
    object_of_relation : list of str
        Any mention of the object of the relationship between
        the organisation and the external one.
    quality_of_relation : list of str
        Any mention of the quality of the relationship between
        the organisation and the external one.
    """
    relation_with: Organisation
    volume: List[str] = field(default_factory=list)
    frequency: List[str] = field(default_factory=list)
    object_of_relation: List[str] = field(default_factory=list)
    quality_of_relation: List[str] = field(default_factory=list)


@dataclass
class Technology_used:
    """
    Represents any technology used by an organisation within a text.

    Attributes
    ----------
    technology_sourced_from : Organisation | None
        Any mention of where the technology was sourced from.
    technology_category : list of str
        Any mention of the general category of the technology.
    technology_name : list of str
        Any mention of names used to refer to this category.
    introduced_in : Dates
        Any mention of the date the technology was introduced
        in the organisation
    """
    technology_sourced_from: Organisation | None = None
    technology_category: List[str] = field(default_factory=list)
    technology_name: List[str] = field(default_factory=list)
    introduced_in: Dates | None = None


@dataclass
class Finiancial:
    """
    Represents any financial information of an organisation within a text.

    Attributes
    ----------
    funding_sources : list of str
        Any mention of where the organisation's funding comes from.
    revenue: list of str
        Any mention of the revenue of the organisation.
    debt : list of str
        Any mention of the debt of the organisation.
    assets : list of str
        Any mention of any assets of the organisation.
    liabilities : list of str
        Any mention of any liabilities of the organisation.
    financial_health : list of str
        Any mention of the financial health of an organisation.
    """
    funding_sources: List[str] = field(default_factory=list)
    revenue: List[str] = field(default_factory=list)
    profit_margins: List[str] = field(default_factory=list)
    debt: List[str] = field(default_factory=list)
    assets: List[str] = field(default_factory=list)
    liabilities: List[str] = field(default_factory=list)
    financial_health: List[str] = field(default_factory=list)


@dataclass
class Department:
    """
    Represents any department of an organisation within a text.

    Attributes
    ----------
    department_name : list of str
        Any mention of any department of the organisation.
    head_of_department : Individual | None
        Any mention of the head of the department.
    member_of_department : list of Individual
        Any mention of any member of the department.
    sub_department : list of Department
        Any mention of a sub department of the department.
    """
    department_name: List[str]
    head_of_department: Individual | None = None
    member_of_department: List[Individual] = field(default_factory=list)
    sub_department: List[Department] = field(default_factory=list)


@dataclass
class Membership:
    """
    Represents any membership to an organisation of
    an individualwithin a text.

    Attributes
    ----------
    organisation : Organisation
        The organisation of which the individual is a member of.
    individual : Individual
        The individual in question.
    active_at_site : Location | None
        The location where the individual is mainly active
        for the organisation.
    subordinates : list of Individual
        The person to which the individual is subordinate.
    active_since : Dates | None
        How long the individual has been active for this organisation.
    role : list of str
        The role the individual has in the the organisation.
    member_of_department : list of Department
        The department of the organisation the individual is a member of.
    organisation_in_contact_to : list of Organisation
        Any mention of an organisation with which the individual is in
        contact through the organisation of which he is a member.
    person_in_contact_to : list of Individual
        Any mention of an person with which the individual is in contact
        through the organisation of which he is a member.
    uuid : uuid.UUID
        The unique identifier of this Dates instance.
    """
    organisation: Organisation
    individual: Individual
    # TODO: Das musst du anpassen, sie Diagramm
    active_at_site: Location | None = None
    # TODO: Überlegen ob das wirklich eine Liste von Individuen sein soll
    subordinates: List[Individual] = field(default_factory=list)
    active_since: Dates | None = None
    role: List[str] = field(default_factory=list)
    member_of_department: List[Department] = field(default_factory=list)
    organisation_in_contact_to: List[Organisation] = field(
        default_factory=list
    )
    person_in_contact_to: List[Individual] = field(default_factory=list)
    uuid: uuid.UUID = field(default_factory=uuid.uuid4)
