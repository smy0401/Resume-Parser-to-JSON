from src.extract.skills_links import extract_skills_and_links


def test_dictionary_extraction():
    text = "I know Python and ReactJS"
    out = extract_skills_and_links(text)
    skills = out["skills"]

    # Comes from skills.txt (not hardcoded in code)
    assert "python" in skills
    assert "reactjs" in skills


def test_link_classification():
    text = "My GitHub is https://github.com/test and LinkedIn is https://linkedin.com/in/test"
    out = extract_skills_and_links(text)

    links = {link["type"] for link in out["links"]}
    assert "github" in links
    assert "linkedin" in links


def test_llama_fallback():
    text = "Experienced in Docker and Kubernetes orchestration"
    out = extract_skills_and_links(text)

    # Skills not in dictionary should still appear via fallback
    skills = out["skills"]
    assert "docker" in skills or "kubernetes" in skills
