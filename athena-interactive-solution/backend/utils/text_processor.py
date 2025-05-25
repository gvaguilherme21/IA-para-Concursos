import re
from collections import Counter

# Basic list of Portuguese stopwords
PORTUGUESE_STOPWORDS = set([
    'de', 'a', 'o', 'que', 'e', 'do', 'da', 'em', 'um', 'para', 'com', 'não', 'uma', 'os', 'no', 'na', 'por', 'mais',
    'as', 'dos', 'como', 'mas', 'ao', 'ele', 'das', 'à', 'seu', 'sua', 'ou', 'quando', 'muito', 'nos', 'já', 'eu',
    'também', 'só', 'pelo', 'pela', 'até', 'isso', 'ela', 'entre', 'depois', 'sem', 'mesmo', 'aos', 'seus', 'quem',
    'nas', 'me', 'esse', 'eles', 'você', 'essa', 'num', 'nem', 'suas', 'meu', 'às', 'minha', 'numa', 'pelos',
    'elas', 'qual', 'nós', 'lhe', 'deles', 'essas', 'esses', 'pelas', 'este', 'dele', 'tu', 'te', 'vocês', 'vos',
    'lhes', 'meus', 'minhas', 'teu', 'tua', 'teus', 'tuas', 'nosso', 'nossa', 'nossos', 'nossas', 'dela', 'delas',
    'esta', 'estes', 'estas', 'aquele', 'aquela', 'aqueles', 'aquelas', 'isto', 'aquilo', 'estou', 'está', 'estamos',
    'estão', 'estive', 'esteve', 'estivemos', 'estiveram', 'estava', 'estávamos', 'estavam', 'estivera', 'estivéramos',
    'esteja', 'estejamos', 'estejam', 'estivesse', 'estivéssemos', 'estivessem', 'estiver', 'estivermos', 'estiverem',
    'hei', 'há', 'havemos', 'hão', 'houve', 'houvemos', 'houveram', 'houvera', 'houvéramos', 'haja', 'hajamos',
    'hajam', 'houvesse', 'houvéssemos', 'houvessem', 'houver', 'houvermos', 'houverem', 'houverei', 'houverá',
    'houveremos', 'houverão', 'houveria', 'houveríamos', 'houveriam', 'sou', 'somos', 'são', 'era', 'éramos', 'eram',
    'fui', 'foi', 'fomos', 'foram', 'fora', 'fôramos', 'seja', 'sejamos', 'sejam', 'fosse', 'fôssemos', 'fossem',
    'for', 'formos', 'forem', 'serei', 'será', 'seremos', 'serão', 'seria', 'seríamos', 'seriam', 'tenho', 'tem',
    'temos', 'têm', 'tinha', 'tínhamos', 'tinham', 'tive', 'teve', 'tivemos', 'tiveram', 'tivera', 'tivéramos',
    'tenha', 'tenhamos', 'tenham', 'tivesse', 'tivéssemos', 'tivessem', 'tiver', 'tivermos', 'tiverem', 'terei',
    'terá', 'teremos', 'terão', 'teria', 'teríamos', 'teriam'
])

def tokenize_text(text):
    """Tokenizes text into words, converts to lowercase, and removes punctuation."""
    text = text.lower()
    words = re.findall(r'\b\w+\b', text) # Finds words, handles accents correctly by default in Python 3 regex
    return words

def remove_stopwords(words):
    """Removes stopwords from a list of words."""
    return [word for word in words if word not in PORTUGUESE_STOPWORDS]

def extract_topics(edital_text, num_topics=10):
    """
    Extracts potential topics from edital_text using word frequency.
    Returns a list of the most frequent words (excluding stopwords) as topics.
    """
    if not edital_text:
        return []

    tokens = tokenize_text(edital_text)
    words_without_stopwords = remove_stopwords(tokens)

    if not words_without_stopwords:
        return []

    word_counts = Counter(words_without_stopwords)
    most_common_words = word_counts.most_common(num_topics)

    topics = [word for word, count in most_common_words]
    return topics

# Example usage (optional, can be removed or commented out for production)
if __name__ == '__main__':
    sample_edital = """
    Artigo 1: O concurso público visa o provimento de cargos vagos.
    Direito Administrativo é fundamental. Licitações e contratos.
    Controle Externo pelo Tribunal de Contas da União (TCU).
    O candidato deverá conhecer a Lei de Licitações.
    A prova avaliará conhecimentos de Informática e Português.
    """
    print(f"Original: {sample_edital}")
    topics = extract_topics(sample_edital, num_topics=5)
    print(f"Tópicos Extraídos (top 5): {topics}")

    sample_edital_2 = "Conhecimentos em Contabilidade Pública e Auditoria."
    print(f"Original 2: {sample_edital_2}")
    topics_2 = extract_topics(sample_edital_2, num_topics=3)
    print(f"Tópicos Extraídos 2 (top 3): {topics_2}")
