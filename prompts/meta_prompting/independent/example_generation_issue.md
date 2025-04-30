# Example generation for prompts

## Role Description
You are a globally recognized expert in prompt engineering, renowned for your ability to craft, analyze, and optimize prompts for large language models (LLMs). Your expertise spans natural language processing, cognitive psychology, linguistics, and human-computer interaction. You have an in-depth understanding of prompt engineering best practices, guidelines, and state-of-the-art techniques developed by leading AI research institutions. You are the foremost authority in designing precise, effective, and structured prompts that optimize AI-human interaction.

## Task
You will be presented with a prompt that instructs an LLM to correct wrongly identified personally identifiable information (PII) in European Court of Human Rights case documents. The PII is not linked to a particular individual but instead denotes an attribute inherent to the court document. You will be presented with a description of this PII  as well as examples of this PII appearing in different contexts. The identifer of the property will be marked by a HTML <span> tag in the context, e.g. <span class="property name">. Your task is to generate examples, for guiding the LLM in problem solving, as described in the section `Example Instruction` for every entry found in the list.

### Example Instruction
Follow the below approach:
1. Formulate a short text of at least 3 sentences. This will be the basis for identifying the mistakes and their correction.
2. Generate, within the tag <correct_solution>, a list of correctly identified PII. Follow the template below:
<correct_solution>[{`uuid_of_solution`: `identifier`}]</correct_solution>
3. Then you will generate, within the tag <wrong_solution>, a dict of wrongly identified identifiers, following the template below:
```json
  {
    "uuid_of_solution": [
      {
        "reason_why_false": "Explanation of why the identifier was wrongly extracted based on its relevance in the text. The reasoning should be at most two sentences long.",
        "context": "The context of the wrongly identified identifier.",
        "identifier": "The identifier that was wrongly extracted."
      }
    ]
  }
```
4. Then you will generate a corrected solution under the section `#### Response of the LLM`. Here you should only extract new identifiers, and never repeat identifiers only found in <correct_solution>. Following the template below:
  ```json
  {
    "extracted_information": ["List of dictionaries with 'reasoning', 'context' and 'identifier' keys for PII"]
  }
  ```
  - The `reasoning` should explain why the identifier for the PII was extracted based on its relevance in the text. The reasoning should be two sentences long.
  - The `context` should be the surrounding text of the identifier, copied verbatim from the text
  - The `identifier` should be the PII, copied from the text
  - The first and third example musn't have an empty list as a value for the key `extracted_information`


### Required Actions
  - Your first and third example must not contain dict with an empty list of the key `extracted_information`. Only the second example should have an empty list.


## Examples Generation example 
You are an Expert Issues Solver tasked with reviewing extraction results. Identify the context of the incorrect extraction and clarify the correct extraction process for numerical values in similar contexts. Provide feedback on how to improve the extraction process to ensure accuracy in future attempts.
**Provided Examples**:
"examples": ["The Supreme Court ruled in <span class="court_case_name">Gideon v. Wainwright</span> that the state must provide free legal representation in criminal cases for the indigent, in contrast to the 1976 rulingin Boston that made no such requirement.", "In <span class="court_case_name">Hazelwood School District v. Kuhlmeier</span>, 484 U.S. 260 (1988), the Supreme Court held that schools may restrict what is published in student newspapers."]


### Example 1
**Example generation for the entry**:
"In <span class="court_case_name">Hazelwood School District v. Kuhlmeier</span>, 484 U.S. 260 (1988), the Supreme Court held that schools may restrict what is published in student newspapers."
**Example text**:
In <span class="court_case_name">Hazelwood School District v. Kuhlmeier</span>, 484 U.S. 260 (1988), the Supreme Court held that schools may restrict what is published in student newspapers. Other free speech decisions were Morse v. Frederick, Cox v. New Hampshire and Texas v. Johnson. In the first two rulings, the Supreme Court decided to restrict free speech.
<correct_solution>[{"7a5sf7c9-9h58": "Hazelwood School District v. Kuhlmeier"}]</correct_solution>
<wrong_solution>
```json
  {
    "49c74e9a-1885-46'": [
      {
        "reason_why_false": "Morse v. Frederick, Cox v. New Hampshire are two different court rulings and were wrongly grouped together",
        "context": "Other free speech decisions were Morse v. Frederick, Cox v. New Hampshire",
        "identifier": "Morse v. Frederick, Cox v. New Hampshire"
      }
    ]
  }
```</wrong_solution>
#### Response of the LLM
```json
{
  "extracted_information": [
    {
      "reasoning": "The text mentions 'Morse v. Frederick', a famous ruling that the First Amendment allows the prohibition or punishment of student speech that could reasonably be viewed as promoting illegal drug use.",
      "context": "Other free speech decisions were Morse v. Frederick, Cox v. New Hampshire",
      "identifier": "Morse v. Frederick"
    },
    {
      "reasoning": "The text mentions 'Cox v. New Hampshire', a ruling on the right of assembly.",
      "context": "Other free speech decisions were Morse v. Frederick, Cox v. New Hampshire",
      "identifier": "Cox v. New Hampshire"
    },
    {
      "reasoning": "The text mentions 'Texas v. Johnson' a ruling allowing the burning of objects, specifically the flag of the USA.",
      "context": "and Texas v. Johnson. In the first two rulings",
      "identifier": "Texas v. Johnson"
    }
  ]
}
```

### Example 2
**Example generation for the entry**: "The Supreme Court ruled in <span class="court_case_name">Gideon v. Wainwright</span> that the state must provide free legal representation in criminal cases for the indigent, in contrast to the 1976 ruling in Boston that made no such requirement"

**Example text**:
The Supreme Court ruled in Gideon v. Wainwright that the state must provide free legal representation in criminal cases for indigent defendants. This decision differed from a 1976 ruling in Boston, which did not impose such a requirement. As a result, Gideon v. Wainwright set a crucial precedent for the right to legal counsel in the United States.

<correct_solution>[{"7a5f47c2-1c71": "Gideon v. Wainwright"}]</correct_solution>
<wrong_solution>
```json
  {
    "5148b359-2fb2-4c": [
      {
        "reason_why_false": "The phrase '1976 ruling in Boston' is too vague to be considered a clear identifier of a specific legal case. It lacks a formal case name or citation",
        "context": "differed from a 1976 ruling in Boston",
        "identifier": "1976 ruling in Boston"
      }
    ]
  }
```
</wrong_solution>
#### Response of the LLM
```json
{
  "extracted_information": []
}
```

