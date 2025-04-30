## Examples Generation example 
**Provided Prompt**:

### Example 1
<text>In <span class="court_case_name">Hazelwood School District v. Kuhlmeier</span>, 484 U.S. 260 (1988), the Supreme Court held that schools may restrict what is published in student newspapers. Other free speech decisions were Morse v. Frederick, Cox v. New Hampshire and Texas v. Johnson. In the first two rulings, the Supreme Court decided to restrict free speech.</text>
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
<text>The Supreme Court ruled in Gideon v. Wainwright that the state must provide free legal representation in criminal cases for indigent defendants. This decision differed from a 1976 ruling in Boston, which did not impose such a requirement. As a result, Gideon v. Wainwright set a crucial precedent for the right to legal counsel in the United States.</text>

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
