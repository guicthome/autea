#!/bin/bash
# Script para configurar o ambiente e iniciar a Plataforma Analítica Lotus no Linux/macOS

echo "Bem-vindo ao script de configuração e execução da Plataforma Analítica Lotus!"
echo "Este script irá guiá-lo através da criação de um ambiente virtual, instalação de dependências e inicialização da aplicação."
echo "--------------------------------------------------------------------------------"

# Verifica se o Python 3.11+ está acessível
if ! command -v python3.11 &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "ERRO: Python 3 não encontrado. Por favor, instale Python 3.11 ou superior e certifique-se de que está no PATH."
    exit 1
fi

PYTHON_CMD=python3.11
if ! command -v python3.11 &> /dev/null; then
    PYTHON_CMD=python3
    echo "Aviso: python3.11 não encontrado, usando python3. Certifique-se de que é a versão 3.11+."
fi

# Navega para o diretório do script (assumindo que está na raiz do projeto)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Verifica se o diretório src existe
if [ ! -d "src" ]; then
    echo "ERRO: Diretório 'src' não encontrado. Certifique-se de que este script está na raiz do projeto 'plataforma_clinica'."
    exit 1
fi

# 1. Criação do Ambiente Virtual
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual 'venv'..."
    $PYTHON_CMD -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERRO: Falha ao criar o ambiente virtual. Verifique sua instalação do Python."
        exit 1
    fi
else
    echo "Ambiente virtual 'venv' já existe."
fi

# 2. Ativação do Ambiente Virtual
echo "Ativando ambiente virtual..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERRO: Falha ao ativar o ambiente virtual."
    exit 1
fi

# 3. Instalação das Dependências
echo "Instalando dependências Python... Isso pode levar alguns minutos."
# Lista de dependências
DEPENDENCIES=("Flask" "Flask-SQLAlchemy" "psycopg2-binary" "Werkzeug" "pandas" "openpyxl" "python-docx" "PyPDF2" "matplotlib" "WeasyPrint")

for dep in "${DEPENDENCIES[@]}"; do
    echo "Instalando $dep..."
    pip3 install "$dep"
    if [ $? -ne 0 ]; then
        echo "ERRO: Falha ao instalar $dep. Verifique sua conexão com a internet ou os logs de erro do pip."
        # Considerar não sair imediatamente para tentar instalar outras dependências
    fi

done

echo "--------------------------------------------------------------------------------"
echo "IMPORTANTE: Configuração do Banco de Dados"
echo "--------------------------------------------------------------------------------"
echo "Antes de executar a aplicação, você PRECISA configurar a conexão com o banco de dados."
echo "1. Abra o arquivo: src/app.py"
echo "2. Localize a linha: app.config["SQLALCHEMY_DATABASE_URI"] = ..."
echo "3. SUBSTITUA as credenciais e nome do seu banco de dados PostgreSQL (ou MySQL, ajustando a string e dependência)."
echo "   com as credenciais e nome do seu banco de dados PostgreSQL (ou MySQL, ajustando a string e dependência)."
echo "4. Certifique-se de que o serviço do seu banco de dados (PostgreSQL/MySQL) está em execução."
echo "--------------------------------------------------------------------------------"
read -p "Pressione [Enter] após ter configurado o banco de dados em src/app.py..."

# 4. Execução da Plataforma
echo "Iniciando a Plataforma Analítica Lotus..."
echo "A aplicação estará acessível em http://localhost:5000 ou http://0.0.0.0:5000 no seu navegador."
echo "Pressione Ctrl+C no terminal para encerrar o servidor."

$PYTHON_CMD src/app.py

# Desativa o ambiente virtual ao sair (opcional, pois o script termina)
# deactivate

echo "Servidor Flask encerrado."

