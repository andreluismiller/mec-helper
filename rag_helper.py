INSTRUCTIONS = '''
Você é um assistente especializado nos programas e ações do Ministério da Educação (MEC).
Sua tarefa é responder perguntas com base no contexto fornecido, extraído das páginas de
Dúvidas Frequentes dos programas do MEC.
Utilize o contexto para encontrar informações relevantes e forneça respostas precisas.
Responda sempre em português. Se a resposta não estiver presente no contexto,
responda com "Não encontrei essa informação nas perguntas frequentes disponíveis."
'''.strip()

PROMPT_TEMPLATE = '''
PERGUNTA: {question}
CONTEXTO:
{context}
'''.strip()

# Pesos ajustados para os campos exatos que existem no seu índice
BOOST_DICT = {
    'pergunta':    3.0,
    'nome':        2.0,
    'termos':      1.5,
    'sigla':       1.5,
    'sinonimos':   1.0,
    'resposta':    1.0,
    'agrupamento': 0.5,
}

class RAGBase:
    def __init__(
        self,
        text_index,
        llm_client,
        instructions=INSTRUCTIONS,
        prompt_template=PROMPT_TEMPLATE,
        model='llama-3.3-70b-versatile'
    ):
        # Apenas o motor de busca textual e o cliente LLM
        self.text_index = text_index
        self.llm_client = llm_client
        
        self.instructions = instructions
        self.prompt_template = prompt_template
        self.model = model

        # Rastreamento de uso para avaliação e custos
        self.usages = []
        self.last_usage = None

    def reset_usage(self):
        """Zera o contador de tokens (útil entre execuções de batch)."""
        self.usages = []
        self.last_usage = None

    def search(self, query, num_results=5):
        """Realiza a busca puramente textual no sqlitesearch."""
        return self.text_index.search(
            query,
            num_results=num_results,
            boost_dict=BOOST_DICT
        )

    def build_context(self, search_results):
        """Monta a string de contexto a partir dos campos exatos indexados."""
        lines = []
        for doc in search_results:
            if doc.get('nome'):
                lines.append(f"Nome:         {doc['nome']}")
            if doc.get('agrupamento') and doc['agrupamento'] != 'geral':
                lines.append(f"Agrupamento:  {doc['agrupamento']}")
            
            lines.append(f"P: {doc.get('pergunta', '')}")
            lines.append(f"R: {doc.get('resposta', '')}")
            lines.append('')
        return '\n'.join(lines).strip()

    def build_prompt(self, query, search_results):
        """Formata o prompt final unindo pergunta do usuário e contexto."""
        context = self.build_context(search_results)
        return self.prompt_template.format(
            question=query, context=context
        )

    def llm(self, prompt):
        """Chama o modelo via API compatível com OpenAI (Groq) e registra o uso."""
        messages = [
            {'role': 'system', 'content': self.instructions},
            {'role': 'user',   'content': prompt},
        ]
        
        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.0
        )
        
        self.last_usage = response.usage
        self.usages.append(response.usage)
        
        return response.choices[0].message.content
 
    def rag(self, query):
        """Executa o pipeline completo de RAG e retorna o texto da resposta."""
        search_results = self.search(query)
        prompt = self.build_prompt(query, search_results)
        answer = self.llm(prompt)
        return answer