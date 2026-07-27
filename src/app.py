import streamlit as st
from assistant import assistant
from db import save_feedback

# Configuração da Página
st.set_page_config(page_title="Chat MEC FAQ", page_icon="🎓")

# Cabeçalho Estático
st.title("MEC FAQ Assistant")
st.markdown("""
    **Bem-vindo ao assistente virtual dos programas do Ministério da Educação.**  
    Selecione a sigla do programa desejado (opcional) e digite sua dúvida abaixo.
    Nosso assistente buscará na base oficial de perguntas frequentes para te responder.
""")
st.divider()

# Formulário de Interação
# Adicione ou remova as siglas de acordo com o seu dataset
# Lista completa de programas atualizada
SIGLAS_PERMITIDAS = [
    "None", "CNTM", "INOVALAB", "PBA", "PBAEJA", "PDDE", "PECS", "PEMM", 
    "PJE", "PNEEI", "PNEEI-TEE", "PNEERQ", "PNEI", "PNEPT", "PNIPI", 
    "PNLD", "PNRA", "PPF", "PRAEMA", "PRILEI", "PRODITEC", "PROEC", 
    "PROJOVEM", "PROLEEI", "PRONATEC"
]

sigla = st.selectbox("Sigla do Programa:", SIGLAS_PERMITIDAS)
question = st.text_input("Sua dúvida:")

if st.button("Enviar") and question:
    with st.spinner("Buscando informações e gerando resposta..."):
        # Executa o RAG e pega a resposta + ID da conversa
        answer, conv_id = assistant.ask(question, sigla)
        
        # Salva no session state para o UI não resetar
        st.session_state['last_answer'] = answer
        st.session_state['last_conv_id'] = conv_id
        st.session_state['feedback_given'] = False

# Exibição da Resposta e Coleta de Feedback
if 'last_answer' in st.session_state:
    st.info(st.session_state['last_answer'])
    
    if not st.session_state.get('feedback_given', False):
        st.write("Esta resposta foi útil?")
        col1, col2, _ = st.columns([1, 1, 8])
        
        with col1:
            if st.button("👍 Sim"):
                save_feedback(
                    conversation_id=st.session_state['last_conv_id'],
                    source="streamlit_app", relevance="positivo", explanation="", score=1
                )
                st.session_state['feedback_given'] = True
                st.success("Obrigado pelo feedback!")
                st.rerun()
                
        with col2:
            if st.button("👎 Não"):
                save_feedback(
                    conversation_id=st.session_state['last_conv_id'],
                    source="streamlit_app", relevance="negativo", explanation="", score=-1
                )
                st.session_state['feedback_given'] = True
                st.error("Obrigado pelo feedback! Analisaremos o caso.")
                st.rerun()