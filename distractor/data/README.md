# Authoring conventions

Every question is written from scratch. No curriculum text, no provider question is
reproduced. Follow the exam's own stem rules, because they are most of what makes a
question feel like a real one:

- Three choices, exactly. Never "all of the above" or "A and B only".
- One qualifier per stem where a judgement is involved: most likely, least likely,
  best described, most appropriate, most accurate, least appropriate, least accurate.
- Never "except", never "true" or "false", and avoid "not".
- Distractors are the common calculation slip and the common reasoning error, not
  noise. Say which slip produces each one in `distractors`.
- A question should be answerable in about 90 seconds.

## Schema

    {
      "id": "fi-004",                     unique, topic prefix
      "ref": "Modified duration",         what it tests, shown in review
      "calc": true,                       needs arithmetic
      "stem": "...",
      "choices": ["...", "...", "..."],
      "answer": 1,                        index into choices
      "solution": "Worked solution.",
      "distractors": ["why this is tempting", "", "why this is tempting"]
    }

`distractors` is index-aligned with `choices`; the correct one is an empty string.
