## What I have done

I used the instructions you provided me to instruct the expert `{{expert}}` to do:
<previous_step>{{previous_step}}</previous_step>.

I received the following response:
<response>{{response}}</response>

No its your turn again!

## What you should do

**Assess the Current State**:
- Summarize the response in one factual statement:
    Format: "The response contains [type of content] regarding [topic]."
- Do not evaluate, identify specific issues or errors, suggest improvements, reference past experts, or mention any entities.

**Apply the Heuristic**
- If <previous_step> was "extracting" or "issues_solving" -> Call an expert for verification.
    - Output:
        - **Instructions** section with the `Expert Template`
        - Next Step section: ```json {"Next": "verification"}```
- If <previous_step> was "verification":
    - If `"bool": false` exists in <response> -> Call an expert to fix issues.
        - Output:
            - **Instructions** section with the `Expert Template`
            - Next Step: ```json {"Next": "issues_solving"}```
    - If no issues found ->  Conclude discussion.
        - Output: ```json {"Next": "end"}```
- If <response> is empty -> Conclude discussion.
    - Output: ```json {"Next": "end"}```

## Required Actions
- If the <previous_step> was either "extracting", "issues_solving" or "verification" you must always output two sections:
    - **Instructions**
    - **Next step**
- You musst enclose your instruction and next step JSON in three backticks ```, i.e.
    - ```json {"Next": "next_step} ``` 
