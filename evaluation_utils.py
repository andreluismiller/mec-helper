import time
import json
from tqdm.auto import tqdm


def calc_price(usage):
    input_price_per_million = 0.05
    output_price_per_million = 0.08

    input_cost = (usage.prompt_tokens / 1_000_000) * input_price_per_million
    output_cost = (usage.completion_tokens / 1_000_000) * output_price_per_million
    total_cost = input_cost + output_cost

    return {
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost,
    }

def calc_total_price(usages):
    return sum(calc_price(u)["total_cost"] for u in usages)

def llm_structured(client, instructions, user_prompt, model="llama3-8b-8192"):
    """
    Usa a API da Groq/OpenAI para retornar um objeto JSON estruturado.
    A instrução DEVE pedir explicitamente para retornar em formato JSON.
    """
    messages = [
        {"role": "system", "content": instructions},
        {"role": "user", "content": user_prompt}
    ]

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.0 # Temperatura zerada para avaliação consistente
    )

    # Faz o parse da string JSON retornada pelo modelo
    parsed_output = json.loads(response.choices[0].message.content)
    
    return parsed_output, response.usage

def llm_structured_retry(client, instructions, user_prompt, model="llama3-8b-8192", max_retries=3):
    for attempt in range(max_retries):
        try:
            return llm_structured(client, instructions, user_prompt, model=model)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2 ** attempt)

def map_progress(pool, seq, f):
    results = []
    with tqdm(total=len(seq)) as progress:
        futures = []
        for el in seq:
            future = pool.submit(f, el)
            future.add_done_callback(lambda p: progress.update())
            futures.append(future)

        for future in futures:
            results.append(future.result())
    return results