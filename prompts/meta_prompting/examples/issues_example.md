# Examples
## Example 1

The following shows an example for the property `Nationality` of an individual.
### Query
<text>
Yanagimachi was born in Japan. He made many important contributions to the study of mammalian fertilisation. He worked with Min Chueh Chang, a scientist working in the USA. Although Chang's parents were born in China, he received citizenship of the country where he worked for most of his career in the 1950s.</text>
<person dict>{"f37d4464-9j81-4363": {"full name": "Ryuzo Yanagimachi", "abbrevations": ["R.Y"], "alias": ["Cloning Master"]},
"d7410ba2-9880-4c46": {"full name": "Mileva Maric", "abbrevations": [], "alias": ["Mili"]},
"45102262-4ea3-4a1c": {"full name": "Min Chueh Chang", "abbrevations": ["M.C. Chang"], "alias": []}}</person dict>
<correct solution>["Japanese"]</correct solution>
<wrong solution>
{"a15c0b3e": {"identifier": "Chinese",
"reason_why_false": "The proposed solution incorrectly identifies Min Chueh Chang as a Chinese citizen. While his parents were born in China, the text explicitly states that he acquired citizenship in the country where he worked for most of his career—the USA. The solution overlooks this critical detail, leading to an inaccurate conclusion.",
"context": "he received citizenship of the country where he worked for most of his career.",
"uuid_person": "45102262-4ea3-4a1c"}}
</wrong solution>

### Response of the LLM
```json
{
  "45102262-4ea3-4a1c": [
    {
      "reasoning": "The text states that Min Chueh Chang received citizenship in the country where he worked for most of his career, which is the USA. Although his parents were born in China, this does not determine his citizenship. Therefore, the identifier should reflect his acquired citizenship, not his heritage",
      "context": "he received citizenship of the country where he worked for most of his career in the 1950s.",
      "identifier": "American"
    }
  ]
}
```
## Example 2

The following shows an example for the property `Social Class` of an individual.
### Query
<text>
Tom was sometimes bullied by his classmates at Dartmouth Academy. With tuition costing £100,000 a year, all of his classmates had been brought up in the upper classes, while he was brought up in the lower. As a result, he sometimes felt like an outsider among his friends.
</text>
<person dict>{"9ce7b0b7-313b-4c": {"full name": "Tom Biddle", "abbrevations": [], "alias": ["Coldemort"]},
"ca3d265c-8f04-40": {"full name": "James Kotter", "abbrevations": [], "alias": ["J.K"]}}</person dict>
<correct solution>[]</correct solution>
<wrong solution>
{"a99ckb32": {"identifier": "upper class",
"reason_why_false": "The proposed solution inaccurately assigns an upper-class upbringing to Tom, contradicting the explicit statement in the text that he was raised in the lower class. The solution fails to consider the contrasting clause, which clearly distinguishes Coldemort's upbringing from that of his upper-class classmates",
"uuid_person": "9ce7b0b7-313b-4c"}}
</wrong solution>

### Response of the LLM
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
## Example 3
The following shows an example for the property `Diagnosis` of an individual.
### Query
<text>
Dr Vranitzky discussed Mark Cutter's diagnosis of sepsis with him. Dr Vranitzky, who has treated many patients with this diagnosis, shared his experience with sepsis. He reassured Mr Cutter not to worry, that he was in very good hands at St Peter's Hospital.
</text>
<person dict>
{"99cd653c-b829-47": {"full name": "August Vranitzky", "abbrevations": [Dr Vranitzky], "alias": []},
"1e274ec0-4be2-4f": {"full name": "Mark Cutter", "abbrevations": [], "alias": []},
"91b4ca8a-2ba4-43": {"full name": "Jack Smith", "abbrevations": [J.S.], "alias": []}}
</person dict>
<correct solution>["sepsis"]</correct solution>
<wrong solution>
{"a61zzb6k": {"identifier": "sepsis",
"reason_why_false": "
The proposed solution incorrectly attributes the diagnosis of sepsis to Dr. Vranitzky. While the text confirms that Mark Cutter was diagnosed with sepsis, it clearly states that Dr. Vranitzky discussed his experience treating the condition, not suffering from it. The solution misinterprets the context, leading to an erroneous conclusion.",
"uuid_person": "99cd653c-b829-47"}}
</wrong solution>

### Response of the LLM
```json
{"99cd653c-b829-47": []}
```