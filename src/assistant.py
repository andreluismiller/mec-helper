import time
import os
from openai import OpenAI
from sqlitesearch import TextSearchIndex
from rag_helper import RAGBase, BOOST_DICT
from db import save_conversation
from dotenv import load_dotenv

# Carrega as variáveis de ambiente, incluindo a GROQ_API_KEY
load_dotenv()

DB_PATH = "mac_faq.db"
TEXT_FIELDS = ["nome", "pergunta", "resposta"]
KEYWORD_FIELDS = ["agrupamento", "termos", "sinonimos", "sigla"]

text_index = TextSearchIndex(
    text_fields=TEXT_FIELDS,
    keyword_fields=KEYWORD_FIELDS,
    id_field="doc_id",
    db_path=DB_PATH,
)

# O os.environ.get agora vai pegar o valor direto do seu .env
client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ.get("GROQ_API_KEY") 
)

# 2. Extensão da Classe RAGBase com Monitoramento
class AssistantRAG(RAGBase):
    def search_with_filter(self, query, sigla, num_results=5):
        # Aplica o filtro de sigla na busca FTS apenas se for selecionado
        filter_dict = {"sigla": sigla} if sigla and sigla != "None" else {}
        return self.text_index.search(
            query,
            num_results=num_results,
            boost_dict=BOOST_DICT,
            filter_dict=filter_dict
        )

    def ask(self, query, sigla="None"):
        start_time = time.time()

        # 1. Recuperação
        search_results = self.search_with_filter(query, sigla)
        
        # 2. Geração
        prompt = self.build_prompt(query, search_results)
        answer = self.llm(prompt)
        
        # 3. Métricas
        end_time = time.time()
        response_time = end_time - start_time
        
        usage = self.last_usage
        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens
        total_tokens = usage.total_tokens
        
        # Preço base Llama 3 70b na Groq (Ajuste conforme necessário)
        cost_input = (input_tokens / 1_000_000) * 0.59
        cost_output = (output_tokens / 1_000_000) * 0.79
        total_cost = cost_input + cost_output

        # 4. Salvar no Postgres (mapeando 'sigla' para a coluna 'course')
        course_value = sigla if sigla != "None" else "Geral"
        conv_id = save_conversation(
            question=query, answer=answer, course=course_value, model=self.model,
            instructions=self.instructions, prompt=prompt, 
            prompt_tokens=input_tokens, completion_tokens=output_tokens, 
            total_tokens=total_tokens, response_time=response_time, cost=total_cost
        )

        return answer, conv_id

# Instância pronta para ser importada pelo app de Chat
assistant = AssistantRAG(text_index=text_index, llm_client=client)