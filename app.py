import os
import streamlit as st
from PyPDF2 import PdfReader
from groq import Groq
import pandas as pd

# Instanciando o cliente da LLM
cliente_llm = Groq(api_key=os.getenv('GROQ_API_KEY'))

def extrair_texto_pdf(arquivo):
    """Função para extrair texto de um arquivo PDF."""
    try:
        # Cria um objeto PdfReader para ler o arquivo PDF
        leitor = PdfReader(arquivo)
        texto = '' # Variável para armazenar o texto extraído das páginas
        # Itera sobre todas as páginas do PDF
        for pagina in leitor.pages:
            # Extraí o texto de cada página e adiciona à variável 'texto'
            texto += pagina.extract_text()
        return texto # Retorna o texto concatenado de todas as páginas
    except Exception as e:
        # Caso ocorra um erro durante a extração, retorna uma mensagem de erro
        return f'Erro ao processar o arquivo {arquivo.name}: {e}'

# Função para extrair informações específicas da nota fiscal utilizando a API da LLM
def extrair_informacoes(texto_pdf):
    """Função para extrair informações específicas do texto do PDF usando a API da LLM."""
    # Criando o prompt com interpolação de texto usando o método format()
    prompt = (
        "Você é um assistente especializado em extrair dados de notas fiscais. "
        "A partir do texto fornecido abaixo, extraia as seguintes informações e retorne apenas no formato JSON com as seguintes chaves: "
        "'data_de_emissao', 'valor_total', 'numero_da_nota_fiscal' e 'cpf_cnpj_do_prestador'. "
        "Se alguma dessas informações não for encontrada, substitua por 'null'. "
        "Não retorne explicações nem nenhum outro texto, apenas o conteúdo JSON da resposta.\n\n"
        "Texto da nota fiscal:\n{texto_pdf}"
    ).format(texto_pdf=texto_pdf)  # Interpolando o conteúdo do texto extraído do PDF

    # Chamada à API para processar o prompt e gerar a resposta
    try:
        resposta = cliente_llm.chat.completions.create(
            model='llama-3.3-70b-versatile', # Modelo de linguagem
            messages=[{'role': 'user', 'content': prompt}], # Texto do prompt que contém a nota fiscal
            temperature=0.0 # Ajusta para resposta mais determinística
        )
        conteudo = resposta.choices[0].message.content

        # Remover qualquer formatação de markdown (` ```json ... ``` `)
        conteudo_limpo = conteudo.replace("```json", "").replace("```", "").strip()

        # Retorna o JSON gerado pelo modelo
        return conteudo_limpo
    except Exception as e:
        return f'Erro ao consultar a API: {e}'

    return prompt

def main():
    # Configuração da página
    st.set_page_config(page_title='Extrator de PDFs de notas fiscais', page_icon=':books:', layout='centered')

    # Seleção de arquivos PDF
    arquivos_pdf = st.file_uploader(
        'Selecione os arquivos PDF que deseja processar',
        type=['pdf'],
        accept_multiple_files=True
    )

    # Lista para armazenar todas as informações extraídas
    todas_informacoes = []

    # Verifica se há arquivos selecionados
    if arquivos_pdf:
        # Botão para iniciar o processamento
        if st.button('Iniciar Processamento'):
            # Exibe um spinner enquanto processa os PDFs
            with st.spinner('Processando arquivos, por favor, aguarde...'):
                for arquivo_pdf in arquivos_pdf:
                    # Extrai o texto do PDF
                    # st.text_area(f'Texto extraído de {arquivo_pdf.name}', texto_extraido, height=200)
                    texto_extraido = extrair_texto_pdf(arquivo_pdf)

                    # Extrai as informações da nota fiscal
                    informacoes = extrair_informacoes(texto_extraido)

                    # Converte o JSON string para dicionário
                    dic_informacoes = eval(informacoes)

                    # Adiciona o nome do arquivo processado
                    dic_informacoes['nome_arquivo'] = arquivo_pdf.name

                    # Adiciona as informações à lista
                    todas_informacoes.append(dic_informacoes)

                    # Mostra as informações extraídas na interface
                    # st.json(informacoes)

                    # Mensagem indicando o progresso
                    st.write(f"Arquivo '{arquivo_pdf.name}' processado com sucesso.")

                # Criar DataFrame com todas as informações
                df = pd.DataFrame(todas_informacoes)

                # Converter DataFrame para CSV
                csv = df.to_csv(index=False, sep=';', encoding='latin1')

                # Botão para download do CSV
                st.download_button(
                    label='Download CSV',
                    data=csv,
                    file_name='notas_fiscais.csv',
                    mime='text/csv'
                )

            st.success('Processamento concluído!')
    else:
        st.info('Por favor, selecione ao menos um arquivo PDF para habilitar o processamento.')

if __name__ == '__main__':
    main()