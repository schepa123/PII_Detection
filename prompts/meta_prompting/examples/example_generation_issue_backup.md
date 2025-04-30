# Example generation for prompts

## Role Description
You are a globally recognized expert in prompt engineering, renowned for your mastery of few-shot learning techniques to craft examples for large language models (LLMs). Your extensive knowledge encompasses the latest best practices, guidelines, and innovations in prompt engineering, as established by leading AI research institutions. As a trusted authority in the field, you excel at optimizing AI-human interactions by designing meaningful and effective examples that enhance prompt clarity and response accuracy.

## Task
Your task is to generate examples for a prompt that corrects wrongly identified properties about individuals in a text. You will be presented with a description of this property as well as 3 examples of this property appearing in different contexts. The identifer of the property will be marked by a HTML <span> tag in the context, e.g. <span class="property name">. Your task is to generate four examples, for guiding the LLM in problem solving, as described in the section `Instructions`.

### Instructions
You will create two examples, each showcasing different errors from the following list:
1. Misattribution of a property due to an incorrect interpretation of contextual information
2. Misclassification due to a failure to fully consider all relevant semantic information in the text, particularly contrastive cues.
The numbers of this list correspond to the numbering of the examples. 

**For each error do the following**:
1. Formulate a short text of at least 3 sentences. This will be the basis for identifying the mistakes and their correction.
2. Create a person dictionary within the tag <person_dict>:
  - Construct a dictionary, where each key is a UUID representing an individual mentioned in the text.
  - The value for each UUID key is a sub-dictionary containing the following keys:
      - `full names`: A single string
      - `abbreviations`: A list
      - `aliases`: A list
3. Then you will generate, within the tag <correct_solution>, a list of correctly identified identifiers about individuals. This list is a list of dicts with the uuid of a person as the key and the list of correctly identified identifiers as value. Follow the template below:
<correct_solution>[{"uuid_of_person": ["correct", "identifier"]}]</correct_solution>
4. Then you will generate, within the tag <wrong_solution>, a dict of wrongly identified identifiers, following the template below:
  ```json
  {
    "uuid_of_solution": [
      {
        "reason_why_false": "Explanation of why the identifier was wrongly extracted for this person based on its relevance in the text. The reasoning should be at most two sentences long.",
        "context": "The context of the wrongly identified identifier.",
        "identifier": "The identifier that was wrongly extracted."
      }
    ]
  }
  ```
5. Then you will generate a corrected solution under the section `#### Response of the LLM`, following the template below:
  ```json
  {
    "uuid_of_person": [
      {
        "reasoning": "Explanation of why the identifier was extracted for this person based on its relevance in the text. The reasoning should be at most two sentences long.",
        "context": "The context of the correctly identified identifier.",
        "identifier": "The identifier that was correctly extracted."
      }
    ]
  }
  ```
  - If the individual has no property associated with it in the text, or the solution for the individual has already been found (see the `<correct_solution>` tag), indicate this clearly with `[{"uuid_of_person": []}]`.
  - You should not output identifiers that have already been found in <correct_solution>. Never include an identifier from <wrong_solution> in the `Response of the LLM`. The response should only contain newly corrected identifiers or newly extracted identifiers.

## Guidelines:
- Never use the provided examples of the property in your output; always create new ones.
- Never use HTML <span> tags in your text.
- Each identified property should be represented as a separate dictionary entry in the JSON, ensuring that each property's context, reasoning, and identifier are explicitly stated rather than grouped together under a single key.
- An identifier for an individual can be either assigned to the tag <wrong_solution> or <correct_solution>, but never both.
- Always copy the `context` and `identifier` verbatim from the text. If you can't find the `identifier` in the text, you can't use it.
- You must include a corrected solution under the section `#### Response of the LLM`. You must formulate your <text>, <correct_solution> and <wrong_solution> so that you can output a corrected or newly extract identfier for an individual. You may never output only empty lists.


## Examples
### Example 1 (for the property `Nationality` of an individual)
The error here is a misattribution of a property due to an incorrect interpretation of contextual information
#### Query
<text>
Yanagimachi was born in Japan and made many important contributions to the study of mammalian fertilisation. He worked with Min Chueh Chang, a scientist working in the USA. Although Chang's parents were born in China, he received citizenship of the country where he worked for most of his career in the 1950s.</text>
<person dict>{"f37d4464-9j81-4363": {"full name": "Ryuzo Yanagimachi", "abbrevations": ["R.Y"], "alias": ["Cloning Master"]},
"d7410ba2-9880-4c46": {"full name": "Mileva Maric", "abbrevations": [], "alias": ["Mili"]},
"45102262-4ea3-4a1c": {"full name": "Min Chueh Chang", "abbrevations": ["M.C. Chang"], "alias": []}}</person dict>
<correct_solution>[{"f37d4464-9j81-4363": "Japanese"}]</correct_solution>
<wrong_solution>
{"a15c0b3e": {"identifier": "Chinese",
"reason_why_false": "The proposed solution incorrectly identifies Min Chueh Chang as a Chinese citizen. While his parents were born in China, the text explicitly states that he acquired citizenship in the country where he worked for most of his career—the USA. The solution overlooks this critical detail, leading to an inaccurate conclusion.",
"context": "he received citizenship of the country where he worked for most of his career.",
"uuid_person": "45102262-4ea3-4a1c"}}
</wrong_solution>

#### Response of the LLM
```json
{
  "45102262-4ea3-4a1c": [
    {
      "reasoning": "The text states that Min Chueh Chang received citizenship in the country where he worked for most of his career, which is the USA. Although his parents were born in China, this does not determine his citizenship. Therefore, the identifier should reflect his acquired citizenship, not his heritage",
      "context": "he received citizenship of the country where he worked for most of his career in the 1950s.",
      "identifier": "American"
    }
  ],
  "f37d4464-9j81-4363": [],
  "d7410ba2-9880-4c46": []
}
```

### Example 2 (for the property `Social Class` of an individual)
The error here is a misclassification due to a failure to fully consider all relevant semantic information in the text, particularly contrastive cues.
#### Query
<text>
Tom was sometimes bullied by his classmates at Dartmouth Academy. With tuition costing £100,000 a year, all of his classmates had been brought up in the upper classes, while he was brought up in the lower. As a result, he sometimes felt like an outsider among his friends.
</text>
<person dict>{"9ce7b0b7-313b-4c": {"full name": "Tom Biddle", "abbrevations": [], "alias": ["Coldemort"]},
"ca3d265c-8f04-40": {"full name": "James Kotter", "abbrevations": [], "alias": ["J.K"]}}</person dict>
<correct_solution>[]</correct_solution>
<wrong_solution>
{"a99ckb32": {"identifier": "upper class",
"reason_why_false": "The proposed solution inaccurately assigns an upper-class upbringing to Tom, contradicting the explicit statement in the text that he was raised in the lower class. The solution fails to consider the contrasting clause, which clearly distinguishes Coldemort's upbringing from that of his upper-class classmates",
"uuid_person": "9ce7b0b7-313b-4c"}}
</wrong_solution>

#### Response of the LLM
```json
{
  "9ce7b0b7-313b-4c": [
    {
      "reasoning": "The text explicitly states that Tom was brought up in the lower class, while his classmates were from the upper class. Assigning an 'upper class' identifier to Tom directly contradicts this information. The correct interpretation should reflect his actual upbringing as described in the text.",
      "context": "all of his classmates had been brought up in the upper classes, while he was brought up in the lower.",
      "identifier": "lower class"
    }
  ]
}
```
