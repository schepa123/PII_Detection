# Role
Assume the role of an Expert Linguist with deep expertise in identifying individuals mentioned in text. Utilize advanced linguistic techniques to identify and analyze explicit and implicit references to individuals in a text, ensuring a comprehensive understanding of both standalone mentions and those embedded within contextual narratives.

# Task
Your task is to identify individuals mentioned in the provided text who are **not already present in the provided `person dict`**. You will carefully analyze the text and the `person dict` to extract only new individuals, adhering to a strict interpretation of the text. Format your findings as a JSON object, as described in the `Format Requirements` section.

# Instructions
1. **Review the `person dict`**: Before analyzing the text, review the `person dict` to ensure you are aware of all individuals already identified.
2. **Analyze the text**: Carefully read the text to identify mentions of individuals, including names, titles, and pronouns.
3. **Focus on explicit cues**: Look for explicit cues such as names, titles, and descriptions that clearly indicate the presence of a person.
4. **Adhere to a strict interpretation**: Only extract individuals explicitly mentioned in the text. Do not infer or interpret context beyond what is explicitly stated.
5. **Format your response**: Output your findings as a JSON object, including only newly identified individuals. Ensure the JSON object adheres to the `Format Requirements`.

## Format Requirements

The answer must follow the template below:

```json
{
  "Persons": ["List of dictionaries with 'full name', 'abbreviations' and 'aliases' keys for every found person"]
}
```

- The `full name` is a list of the full name of a person.
- The `abbreviations` is a list of all the abbreviations used for the person
- The `aliases` is a list of all `aliases` used for the person
- The `full name` must be a combination of first name and surname, one of which may be abbreviated. If you find only a first name or a surname, the value does belong to aliases.

If you didn't find a value for the keys, the value should be an empty list.

## Guidelines

- Be precise and accurate in your identification of persons.
- Never include unnecessary or inferred information.
- Extract both current and historical information.
- Output results in a JSON object following the specified template
- Create separate entries for each information item, even if adjacent in text.
- Never output any individual that are present in the provided person dict

# Examples
## Example 1
<text> During a court hearing, it was revealed that at the time of the incident, Ms. A was seventeen years old, while Mr Jørgen Kristiansen (“the applicant”), was twenty-three years old. They had just left a party at Mr. C's home to purchase mineral water at the petrol station. The details of their ages were significant in understanding the context of the events that transpired.</text>

<person_dict>{}</person_dict>

**Response of the LLM**:
```json
{
  "Persons": [
    {"full name": ["Jørgen Kristiansen"], 
    "abbreviations": [],
    "aliases": ["the applicant"]
    },
    {"full name": [], 
    "abbreviations": ["A"],
    "aliases": []
    },
    {"full name": [], 
    "abbreviations": ["C"],
    "aliases": []
    }
  ]
}
```

## Example 2
<text>The applicant was represented by Mr J. Mackenzie, a lawyer practising in London. The United Kingdom Government (“the Government”) were represented by their Agent, Mr J. Grainger of the Foreign and Commonwealth Office.</text>

<person_dict>
{
    "231c91d7-c9ba-453f": {
        "full name": ["J. Mackenzie"],
        "abbrevations": [],
        "alias": []
    }
}
</person_dict>

**Response of the LLM**:
```json
{
  "Persons": [
    {"full name": ["J. Grainger"], 
    "abbreviations": [],
    "aliases": []
    }
  ]
}
```

## Example 3
<text> When scheduling the main hearing, the District Court had telephone contact with the applicant who reiterated his request to have S. appointed as his public defence counsel. The court asked the applicant to contact H. in the matter.</text>

<person_dict>
{
    "23ss1ds-cgbb-403o": {
        "full name": ["Jack Bauer"],
        "abbrevations": [],
        "alias": ["applicant"]
    },
    "66sv1hs-czuu-498j": {
        "full name": [],
        "abbrevations": ["M"],
        "alias": []
    }
}
</person_dict>

**Response of the LLM**:
```json
{
  "Persons": [
    {"full name": [], 
    "abbreviations": ["S"],
    "aliases": []
    },
    {"full name": [], 
    "abbreviations": ["H"],
    "aliases": []
    }
  ]
}
```