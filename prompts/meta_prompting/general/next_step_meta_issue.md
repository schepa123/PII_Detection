## What I have done

I used the instructions you provided me to instruct the expert `{{expert}}` to do:
<previous_step>{{previous_step}}</previous_step>.

I received the following response:
<response>{{response}}</response>

No its your turn again!

## What you should do
**Apply the Heuristic**
- If <previous_step> was "extracting" or "issues_solving" -> Call an expert for verification.
    - Output:
        - **Instructions** section with the `Expert Template`
        - **Next Step** section: ```json {"Next": "verification"}```
- If <previous_step> was "verification":
    - If `"bool": false` exists in <response> -> Call an expert to fix issues.
        - Output:
            - **Instructions** section with the `Expert Template`
            - **Next Step**: ```json {"Next": "issues_solving"}```
    - If no issues found ->  Conclude discussion.
        - Output: - **Next Step**: ```json {"Next": "end"}```
- If <response> is empty -> Conclude discussion.
    - Output: - **Next Step**: ```json {"Next": "end"}```

You must follow these exact formatting rules when generating your response:

1. Your response **must** contain **two sections**:
   - **"Instructions"**: This section must include a JSON object with `"job description"` and `"instructions"`.
   - **"Next step"**: This section must include a JSON object with `"Next"` that specifies the next action.

### **Response Example:**
## Instructions
```json
"Instructions": {
    "job description": "job description",
    "instructions": ["List", "of", "instructions"]
}```
## Next Step
```json
"Next step": {"Next": "issues_solving"}``` 