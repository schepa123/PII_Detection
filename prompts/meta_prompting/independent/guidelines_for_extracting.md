- Extract both current and historical information.
- Output results in a JSON object following the specified template.
- Include contextual information by directly quoting the original text.

- Create separate entries for each information item, even if adjacent in text.

- Identifier must be a non-empty string and a verbatim substring of context.
- Copy identifiers verbatim from the text without modifications (e.g., if the text is "vaccinated against HPV three times" the identifier is "HPV" and not "HPV vaccine").
- **NEVER** break up identifiers:
    - If two identifiers are next to each other and logically belong to each other, you should extract them together; if they don't belong together you your create seperate information items, but you are **NEVER** allowed to change the wording, you must copy verbatim!
    - Examples:
        - "He violated rules 37 § 1 and 38" is one item -> PII: "rules 37 § 1 and 38"
        - "He needed to follow rule 40 and rule 30 for his income taxes" is two items -> PII: "rule 40" and "rule 30".