## What I have done

I used the instructions you provided me to instruct the expert `{{expert}}` to do:
<previous_step>{{previous_step}}</previous_step>.

I received the following response:
<response>{{response}}</response>

No its your turn again!

## What you should do

**Assess the Current State**:
- Provide a single factual statement describing what was received in the response, using only information explicitly stated
- Format: "The response contains [type of content] regarding [topic]"

**State Analysis Rules**:
- Do not evaluate correctness or accuracy
- Do not identify specific issues or errors
- Do not suggest improvements or solutions
- Do not reference previous experts or their findings
- Do not refer any person or any other entity from an answer. You must write you instructions as neutral as possible


**Apply the Heuristic**:
- If a solution has been proposed but not verified:
    - Call another expert to verify it.
    - Start with a section **Verification** where you output your call for verification with the template for calling an expert
    - Under a section **Next Step** output ```json {"Next": "verification"}```
- If verification reveals issues, instruct an expert to address and correct those specific parts.
    - Call another expert to address and correct those specific parts.
    - Do not try to solve the problem yourself through instructions
    - Start with a section **Issues Solving** where you output your call for reexamination with the template for calling an expert
    - Under a section **Next Step** output ```json {"Next": "issues_solving"}```
- If the solution has been verified as correct, conclude the discussion.
    - Under a section **Next Step** output ```json {"Next": "end"}```
- If the value in the tag <previous_step> was "verification" and the value in the tag <response> is empty, conclude the discussion
    - Under a section **Next Step** output ```json {"Next": "end"}```