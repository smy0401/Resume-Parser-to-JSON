def build_user_prompt(
    raw_sections, heuristics, schema_path="src/models/schema/cv.schema.json"
):
    """Builds user prompt string from CV blocks + heuristics."""
    with open("src/models/prompts/user_prompt_template.txt") as f:
        user_prompt_template = f.read()

    with open(schema_path) as f:
        schema_json = f.read()

    # Format sections into a nice string
    formatted_sections = "\n".join(
        [f"{i+1}. {text} (offset: {pos})" for i, (text, pos) in enumerate(raw_sections)]
    )

    return user_prompt_template.format(
        raw_sections=formatted_sections,
        emails=heuristics.get("emails", []),
        phones=heuristics.get("phones", []),
        date_candidates=heuristics.get("dates", []),
        schema_json=schema_json,
    )


if __name__ == "__main__":
    # Demo run
    raw_sections = [
        ("John Doe", 0),
        ("Email: johndoe@example.com", 1),
        ("Education: BSc Computer Science, 2018 - 2022", 2),
    ]
    heuristics = {
        "emails": ["johndoe@example.com"],
        "phones": [],
        "dates": ["2018", "2022"],
    }

    prompt = build_user_prompt(raw_sections, heuristics)
    print(prompt)
