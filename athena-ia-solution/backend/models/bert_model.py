# Placeholder for BERT model functionality
# For MVP, this uses a simplified approach to generate prompts.

def generate_prompts(edital_text, knowledge_gaps):
    """
    Generates study prompts based on edital text and user's knowledge gaps.
    MVP Implementation: Uses keyword matching and predefined prompts.
    """
    prompts = []
    edital_text_lower = edital_text.lower()
    knowledge_gaps_lower = [gap.lower() for gap in knowledge_gaps]

    # Example keyword-based prompt generation
    if "direito administrativo" in edital_text_lower:
        prompts.append("Estude os princípios do Direito Administrativo.")
        if "princípios" in knowledge_gaps_lower and "direito administrativo" in knowledge_gaps_lower :
             prompts.append("Revise os princípios fundamentais do Direito Administrativo: Legalidade, Impessoalidade, Moralidade, Publicidade e Eficiência.")

    if "licitações" in edital_text_lower or "lei 14.133" in edital_text_lower:
        prompts.append("Revise a Lei de Licitações (Lei 14.133/2021).")
        if "licitações" in knowledge_gaps_lower:
            prompts.append("Foque nos aspectos da Lei 14.133/2021 que você tem mais dificuldade.")

    if "controle externo" in edital_text_lower:
        prompts.append("Aprofunde-se nas competências e funcionamento do Controle Externo.")
        if "tcu" in knowledge_gaps_lower or "tribunal de contas da união" in knowledge_gaps_lower:
            prompts.append("Estude as competências específicas do Tribunal de Contas da União (TCU) no Controle Externo.")
        if "cgu" in knowledge_gaps_lower or "controladoria-geral da união" in knowledge_gaps_lower:
            prompts.append("Entenda o papel da Controladoria-Geral da União (CGU) no sistema de controle.")

    if "direito constitucional" in edital_text_lower:
        prompts.append("Estude os tópicos de Direito Constitucional relevantes para o edital.")
        if "direitos fundamentais" in knowledge_gaps_lower:
            prompts.append("Revise os Direitos e Garantias Fundamentais na Constituição Federal.")
        if "organização do estado" in knowledge_gaps_lower:
            prompts.append("Aprofunde-se na Organização Político-Administrativa do Estado Brasileiro.")

    if "auditoria governamental" in edital_text_lower:
        prompts.append("Entenda os conceitos e normas de Auditoria Governamental.")
        if "nbasp" in knowledge_gaps_lower:
            prompts.append("Estude as Normas Brasileiras de Auditoria do Setor Público (NBASP).")

    # Generic prompts based on knowledge gaps
    for gap in knowledge_gaps:
        # Avoid adding very generic prompts if more specific ones already cover the gap
        gap_already_covered = False
        for prompt in prompts:
            if gap.lower() in prompt.lower():
                gap_already_covered = True
                break
        if not gap_already_covered:
            prompts.append(f"Foque no tópico: {gap}, conforme o conteúdo do edital.")

    if not prompts and knowledge_gaps:
        prompts.append("Analise o edital e crie um plano de estudos focado em seus pontos de dificuldade.")
    elif not prompts:
        prompts.append("Comece com uma leitura geral do edital para identificar os principais temas.")

    # Remove duplicate prompts if any (e.g. from generic and specific rules)
    unique_prompts = []
    for p in prompts:
        if p not in unique_prompts:
            unique_prompts.append(p)
    
    return unique_prompts

# Example usage (optional, can be removed or commented out)
if __name__ == '__main__':
    sample_edital = """
    Edital para Concurso Público - Área de Controle
    Conhecimentos Específicos: Direito Administrativo, Licitações (Lei 14.133/2021), Controle Externo (TCU e CGU).
    O candidato deve demonstrar conhecimento em auditoria governamental.
    """
    gaps = ["licitações", "TCU", "auditoria governamental"]
    
    generated_prompts = generate_prompts(sample_edital, gaps)
    print("Prompts Gerados:")
    for p in generated_prompts:
        print(f"- {p}")

    gaps_2 = ["Direito Administrativo"]
    generated_prompts_2 = generate_prompts(sample_edital, gaps_2)
    print("\nPrompts Gerados para 'Direito Administrativo':")
    for p in generated_prompts_2:
        print(f"- {p}")

    gaps_3 = ["finanças públicas"] # Gap not directly in keywords
    generated_prompts_3 = generate_prompts(sample_edital, gaps_3)
    print("\nPrompts Gerados para 'finanças públicas':")
    for p in generated_prompts_3:
        print(f"- {p}")

    generated_prompts_4 = generate_prompts(sample_edital, []) # No gaps
    print("\nPrompts Gerados sem lacunas específicas:")
    for p in generated_prompts_4:
        print(f"- {p}")

    generated_prompts_5 = generate_prompts("Texto vago sem palavras-chave", ["qualquer coisa"])
    print("\nPrompts Gerados com texto vago:")
    for p in generated_prompts_5:
        print(f"- {p}")
