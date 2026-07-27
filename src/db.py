import os
import psycopg
from datetime import datetime, timezone
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env para o ambiente
load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

def get_connection():
    return psycopg.connect(**DB_CONFIG)

def save_conversation(question, answer, course, model, instructions, prompt, 
                      prompt_tokens, completion_tokens, total_tokens, response_time, cost):
    
    # O Psycopg 3 permite gerenciar a conexão e o cursor diretamente com "with"
    with get_connection() as conn:
        with conn.cursor() as cursor:
            query = """
                INSERT INTO conversations 
                (question, answer, course, model, instructions, prompt, prompt_tokens, 
                 completion_tokens, total_tokens, response_time, cost, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """
            timestamp = datetime.now(timezone.utc)
            
            cursor.execute(query, (question, answer, course, model, instructions, prompt,
                                   prompt_tokens, completion_tokens, total_tokens, response_time, cost, timestamp))
            
            conv_id = cursor.fetchone()[0]
            
            # O commit ainda é necessário para efetivar a transação de escrita
            conn.commit()
            
    return conv_id

def save_feedback(conversation_id, source, relevance, explanation, score):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            query = """
                INSERT INTO feedback 
                (conversation_id, source, relevance, explanation, score, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s);
            """
            timestamp = datetime.now(timezone.utc)
            
            cursor.execute(query, (conversation_id, source, relevance, explanation, score, timestamp))
            conn.commit()