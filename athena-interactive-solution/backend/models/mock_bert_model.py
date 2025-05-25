# Placeholder for BERT model functionality
# For MVP, this uses a simplified approach to generate prompts.

def generate_prompts(edital_text, knowledge_gaps):
    """
    Generates study prompts based on edital text and user's knowledge gaps.
    MVP Implementation: Uses keyword matching and predefined prompts.
    """
    prompts = []
    # Normalize inputs for case-insensitive matching
    edital_text_lower = edital_text.lower() if edital_text else ""
    knowledge_gaps_lower = [gap.lower() for gap in knowledge_gaps] if knowledge_gaps else []

    # Example keyword-based prompt generation
    if "direito administrativo" in edital_text_lower:
        prompts.append("Estude os princípios do Direito Administrativo.")
        if "princípios" in knowledge_gaps_lower and ("direito administrativo" in knowledge_gaps_lower or any("administrativo" in gap for gap in knowledge_gaps_lower)):
             prompts.append("Revise os princípios fundamentais do Direito Administrativo: Legalidade, Impessoalidade, Moralidade, Publicidade e Eficiência.")

    if "licitações" in edital_text_lower or "lei 14.133" in edital_text_lower:
        prompts.append("Revise a Lei de Licitações e Contratos Administrativos (principalmente Lei 14.133/2021).")
        if any(lic_gap in knowledge_gaps_lower for lic_gap in ["licitações", "lei 14.133", "contratos administrativos"]):
            prompts.append("Foque nos aspectos da Lei 14.133/2021 que você tem mais dificuldade, como modalidades, fases e contratos.")

    if "controle externo" in edital_text_lower:
        prompts.append("Aprofunde-se nas competências e funcionamento do Controle Externo.")
        if "tcu" in knowledge_gaps_lower or "tribunal de contas da união" in knowledge_gaps_lower:
            prompts.append("Estude as competências específicas do Tribunal de Contas da União (TCU) no Controle Externo, conforme a Constituição Federal e sua Lei Orgânica.")
        if "cgu" in knowledge_gaps_lower or "controladoria-geral da união" in knowledge_gaps_lower:
            prompts.append("Entenda o papel da Controladoria-Geral da União (CGU) como órgão central do Sistema de Controle Interno do Poder Executivo Federal e suas interações com o Controle Externo.")

    if "direito constitucional" in edital_text_lower:
        prompts.append("Estude os tópicos de Direito Constitucional relevantes para o edital.")
        if "direitos fundamentais" in knowledge_gaps_lower:
            prompts.append("Revise os Direitos e Garantias Fundamentais (Art. 5º da Constituição Federal) e sua aplicabilidade.")
        if "organização do estado" in knowledge_gaps_lower:
            prompts.append("Aprofunde-se na Organização Político-Administrativa do Estado Brasileiro: União, Estados, Distrito Federal e Municípios.")

    if "auditoria governamental" in edital_text_lower:
        prompts.append("Entenda os conceitos, tipos e normas de Auditoria Governamental.")
        if "nbasp" in knowledge_gaps_lower or "normas de auditoria" in knowledge_gaps_lower:
            prompts.append("Estude as Normas Brasileiras de Auditoria do Setor Público (NBASP) e suas principais diretrizes.")

    if "português" in edital_text_lower or "língua portuguesa" in edital_text_lower:
        prompts.append("Revise os principais tópicos de Língua Portuguesa, como gramática, interpretação de texto e redação (se aplicável).")
        if "interpretação de texto" in knowledge_gaps_lower:
            prompts.append("Pratique a interpretação de textos de concursos anteriores.")
        if "gramática" in knowledge_gaps_lower or "pontuação" in knowledge_gaps_lower or "concordância" in knowledge_gaps_lower:
            prompts.append("Foque nos pontos de gramática que você mais erra, como concordância, regência e pontuação.")
            
    if "raciocínio lógico" in edital_text_lower or "rlm" in edital_text_lower:
        prompts.append("Pratique questões de Raciocínio Lógico-Matemático, cobrindo os tópicos do edital.")

    if "informática" in edital_text_lower:
        prompts.append("Estude os conceitos básicos de informática e os softwares mais comuns cobrados em concursos.")

    # Generic prompts based on knowledge gaps
    for gap in knowledge_gaps: # Use original case for prompts
        gap_lower = gap.lower()
        # Avoid adding very generic prompts if a more specific one already covers the gap
        gap_already_covered = False
        for prompt in prompts:
            if gap_lower in prompt.lower():
                gap_already_covered = True
                break
        if not gap_already_covered:
            prompts.append(f"Foque no tópico: {gap}, conforme o conteúdo do edital.")

    if not prompts and knowledge_gaps: # If no specific prompts were generated but there are gaps
        prompts.append("Analise o edital detalhadamente e crie um plano de estudos focado em seus pontos de dificuldade listados.")
    elif not prompts: # If no edital keywords matched and no gaps provided
        prompts.append("Comece com uma leitura geral e atenta do edital para identificar os principais temas e requisitos.")

    # Remove duplicate prompts if any
    unique_prompts = []
    seen_prompts = set()
    for p in prompts:
        if p not in seen_prompts:
            unique_prompts.append(p)
            seen_prompts.add(p)
    
    return unique_prompts

# Example usage
if __name__ == '__main__':
    sample_edital_text = """
    Edital Completo para Concurso Público - Área de Controle (TCU/CGU)
    Conhecimentos Gerais: Língua Portuguesa, Raciocínio Lógico, Informática.
    Conhecimentos Específicos: Direito Administrativo (incluindo Licitações Lei 14.133/2021), 
    Direito Constitucional (Organização do Estado e Direitos Fundamentais), 
    Controle Externo (foco no TCU e CGU), Auditoria Governamental (NBASP).
    """
    knowledge_gaps_list = ["licitações", "TCU", "interpretação de texto", "NBASP", "organização do estado"]
    
    generated_prompts_list = generate_prompts(sample_edital_text, knowledge_gaps_list)
    print("Prompts Gerados:")
    for i, p_item in enumerate(generated_prompts_list):
        print(f"{i+1}. {p_item}")

    print("\n--- Sem Lacunas de Conhecimento ---")
    generated_prompts_no_gaps = generate_prompts(sample_edital_text, [])
    for i, p_item in enumerate(generated_prompts_no_gaps):
        print(f"{i+1}. {p_item}")

    print("\n--- Edital Vazio ---")
    generated_prompts_empty_edital = generate_prompts("", ["licitações"])
    for i, p_item in enumerate(generated_prompts_empty_edital):
        print(f"{i+1}. {p_item}")

    print("\n--- Edital Simples e Lacuna Genérica ---")
    generated_prompts_simple = generate_prompts("Apenas Raciocínio Lógico.", ["Matemática"])
    for i, p_item in enumerate(generated_prompts_simple):
        print(f"{i+1}. {p_item}")
