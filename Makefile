.PHONY: setup up down run logs

# Instala as dependências do projeto usando o uv
setup:
	uv pip install streamlit "psycopg[binary]>=3.3.4" python-dotenv openai sqlitesearch

# Sobe a infraestrutura (Postgres e Grafana) em background
up:
	docker-compose up -d

# Derruba a infraestrutura
down:
	docker-compose down

# Roda o aplicativo Streamlit (com configurações para o GitHub Codespaces)
run:
	uv run streamlit run src/app.py --server.enableCORS false --server.enableXsrfProtection false

# Exibe os logs dos containers
logs:
	docker-compose logs -f