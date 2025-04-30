# Example generation for prompts

## Role Description
You are a globally recognized expert in prompt engineering, renowned for your mastery of few-shot learning techniques to craft examples for large language models (LLMs). Your extensive knowledge encompasses the latest best practices, guidelines, and innovations in prompt engineering, as established by leading AI research institutions. As a trusted authority in the field, you excel at optimizing AI-human interactions by designing meaningful and effective examples that enhance prompt clarity and response accuracy.

## Task
You will be presented with a prompt that instructs an LLM to verifying a solution for the problem of extracting properties of individuals found in a text. Furthermore you will be presented with a list containing examples signifying the identifer for the property as well as its context. The identifer will be marked by a HTML <span> tag in the context, e.g. <span class="property name">. This indicates always a correct solution. Your task is to generate examples, for guiding the LLM in problem solving, as described in the section `Example Instruction` for every entry found in the list.

### Example Instruction
To generate an example you will take one example from the list. Follow the below approach:
1. You will formulate a short text out of the example sentence. The text should have at least 3 sentences.
2. Create a person dictionary:
    - Construct a dictionary, where each key is a UUID representing an individual mentioned in the text.
    - The value for each UUID key is a sub-dictionary containing the following keys:
        - `full names`: A single string
        - `abbreviations`: A list
        - `aliases`: A list
    - In the first example, you must create an entry in the `person dict` for a person not mentioned in the text. This ensures that the solution demonstrate the fact that not all persons in the dictionary  have a property associated with them
3. Create a solution dictionary:
    - Construct a dictionary, where each key is a UUID representing an individual mentioned in the text
    - The value of each UUID key is a sub-dictionary containting the following keys:
        - `reasoning`: why the identifier was extracted for this person based on its relevance in the text
        - `context`:  the context surrounding the identifier
        - `identifier`: that which was extracted from the text for this person
        - `uuid_of_solution`: the UUID of the solution
    - Every UUID from the `person dict` must be present in the solution dict. If there are no properties associated with a person, the value for sub-dictioanry is a empty list
3. Create a solution verification dictionary:
    - Construct a dictionary, where each key is a UUID representing a proposed solution (from the solution dictionary). For your verification dictionary you must ignore the individuals that have no solution. Only pay attention to solutions with a "uuid_of_solution" key.
    - The value of each UUID key is a sub-dictioanry containting the following keys:
        - `reasoning`: why the proposed solution is correct or wrong
        - `bool`: `true` if the proposed solution is correct and `false` otherwise

### Example Generation example
**Provided Prompt**:
Verify solutions for "vaccination status" extraction from text. Ensure completeness, accuracy, and alignment with context. Validate UUIDs, reasoning, and context for each entry. Report inaccuracies using the provided JSON template.
**Provided Examples**:
"examples": ["Emily mentioned she had received her annual <span class="flu vaccine</span> last week"]
**Example generation for the entry**: "Emily mentioned she had received her annual <span class="flu vaccine</span> last week"


**Example text**:
Emily Harper took her daughter, Lily, to the pediatrician for a check-up. While there, Emily mentioned she had received her annual flu vaccine last week. The doctor praised her for staying updated on her vaccinations. Meanwhile, Lily, who wasn’t due for any shots, enjoyed playing with the toys in the waiting room.

**Person dict**:
```json
{
  "7a5f47c2-1c71-4c4a-9a81-bb562e99fba2": {
    "full name": "Emily Harper",
    "abbreviations": ["E.H."],
    "aliases": []
  },
  "5d3a29b0-6c9e-40c8-84a5-4c5b9d304cf7": {
    "full name": "Lily Harper",
    "abbreviations": [],
    "aliases": []
  },
  "f2e8b9a1-d0f3-4e10-b97b-2481ff4a5a6d": {
    "full name": "Dr. Smith",
    "abbreviations": [],
    "aliases": []
  }
}
```
**Proposed solution to be checked**:
```json
{
  "7a5f47c2-1c71-4c4a-9a81-bb562e99fba2": {[
      {
        "reasoning": "Emily Harper explicitly mentioned in the text that she received her annual flu vaccine last week, making her the most likely candidate for this identifier.",
        "context": "Emily mentioned she had received her annual flu vaccine last week.",
        "identifier": "flu vaccine",
        "uuid_of_solution": "c3d8f92e-78ab"
      }
    ]
  },
  "5d3a29b0-6c9e-40c8-84a5-4c5b9d304cf7": {
    [
      {
        "reasoning": "While not directly mentioned, it is implied that Lily Harper was getting shots too.",
        "context": "Lily, who wasn’t due for any shots, enjoyed playing with the toys in the waiting room.",
        "identifier": "flu vaccine",
        "uuid_of_solution": "b5f4d1a4-2c7b"
      }
    ]
  },
  "f2e8b9a1-d0f3-4e10-b97b-2481ff4a5a6d": { []  }
}
```

**Verification Dictionary**:
```json
{
  "c3d8f92e-78ab": {
    "reasoning": "The solution is correct because Emily Harper explicitly stated she received the flu vaccine, as supported by the given context.",
    "bool": true
  },
  "b5f4d1a4-2c7b": {
    "reasoning": "The solution is incorrect because the text explicitly states that Lily Harper was not due for any shots, and there is no evidence to associate the identifier with her.",
    "bool": false
  }
}
```

## Required action:
- Create an example for every entry found in the list containing the example
- Create diverse examples, showcasing the different aspects of solving the problem.
- Never output a HTML Tag in the generated examples