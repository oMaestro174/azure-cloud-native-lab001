import streamlit as st
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
import os
import pymssql
import uuid
import json

# Carregar variáveis de ambiente
load_dotenv()

# Variáveis de conexão
blob_connection_string = os.getenv("BLOB_CONNECTION_STRING")
blob_container_name = os.getenv("BLOB_CONTAINER_NAME")
blob_account_name = os.getenv("BLOB_ACCOUNT_NAME")

sql_server = os.getenv("SQL_SERVER")
sql_database = os.getenv("SQL_DATABASE")
sql_user = os.getenv("SQL_USER")
sql_password = os.getenv("SQL_PASSWORD")

# Título da aplicação
st.title("Cadastro de Produtos")

# Campos do formulário
product_name = st.text_input("Nome do Produto")
product_price = st.number_input("Preço do Produto", min_value=0.0, format="%.2f")
product_description = st.text_area("Descrição do Produto")
product_image = st.file_uploader("Imagem do Produto", type=["jpg", "png", "jpeg"])

# Função para subir imagem ao Azure Blob Storage
def upload_image_to_blob_storage(file):
    blob_service_client = BlobServiceClient.from_connection_string(blob_connection_string)
    container_client = blob_service_client.get_container_client(blob_container_name)
    blob_name = str(uuid.uuid4()) + "_" + file.name
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(file.read(), overwrite=True)
    image_url = f"https://{blob_account_name}.blob.core.windows.net/{blob_container_name}/{blob_name}"
    return image_url

# Função para inserir produto no banco de dados
def insert_product_to_sql(name, price, description, image_file):
    try:
        image_url = upload_image_to_blob_storage(image_file)
        conn = pymssql.connect(server=sql_server, user=sql_user, password=sql_password, database=sql_database)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO Produtos (nome, preco, descricao, imagem_url) VALUES (%s, %s, %s, %s)",
            (name, price, description, image_url)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Erro ao inserir produto no banco de dados: {e}")
        return False
    


# Função para buscar produtos do banco de dados

def get_products_from_sql():
    try:
        conn = pymssql.connect(server=sql_server, user=sql_user, password=sql_password, database=sql_database)
        cursor = conn.cursor(as_dict=True)  # <- IMPORTANTE!
        cursor.execute("SELECT * FROM Produtos")
        products = cursor.fetchall()
        conn.close()
        return products
    except Exception as e:
        st.error(f"Erro ao buscar produtos do banco de dados: {e}")
        return []
    


# Função para exibir a lista de produtos na tela   
def list_produtos_screen():
        products = get_products_from_sql()
        if products:
        # Define o número de cards por linha
            cards_por_linha = 3
            # Cria as colunas iniciais
            cols = st.columns(cards_por_linha)
            for i, product in enumerate(products):
                col = cols[i % cards_por_linha]
                with col:
                    st.markdown(f"### {product['nome']}")
                    st.write(f"**Descrição:** {product['descricao']}")
                    st.write(f"**Preço:** R$ {product['preco']:.2f}")
                    if product["imagem_url"]:
                        html_img = f'<img src="{product["imagem_url"]}" width="200" height="200" alt="Imagem do produto">'
                        st.markdown(html_img, unsafe_allow_html=True)
                    st.markdown("---")
                # A cada 'cards_por_linha' produtos, se ainda houver produtos, cria novas colunas
                if (i + 1) % cards_por_linha == 0 and (i + 1) < len(products):
                    cols = st.columns(cards_por_linha)
        else:
            st.info("Nenhum produto encontrado.")



# Ação do botão de salvar produto
if st.button('Salvar Produto'):
    if not product_name or not product_description or not product_image:
        st.warning("Preencha todos os campos e envie uma imagem.")
    else:
        success = insert_product_to_sql(product_name, product_price, product_description, product_image)
        if success:
            st.success("Produto salvo com sucesso!")

# Exibição de produtos cadastrados (botão ainda simbólico)
st.header("Produtos cadastrados")
st.write("Aqui estão os produtos cadastrados:")

if st.button("Buscar Produtos"):
    #st.info("Funcionalidade de busca ainda não implementada.")
    list_produtos_screen()
