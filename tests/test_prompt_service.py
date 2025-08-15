from src.services.prompt_service import load_prompt_templates, generate_prompts


def test_load_prompt_templates():
    templates = load_prompt_templates()
    assert isinstance(templates, list)
    assert len(templates) > 0


def test_generate_prompts_injects_entities():
    prompts = generate_prompts(["Acme Corp"])
    assert all("Acme Corp" in p for p in prompts)
    assert len(prompts) == len(load_prompt_templates())
