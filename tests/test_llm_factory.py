from agents.llm_factory import make_llm

def test_make_llm_configura_modelo_e_temperatura():
    llm = make_llm("qwen2.5:7b", 0.7)
    assert llm.model == "qwen2.5:7b"
    assert llm.temperature == 0.7
