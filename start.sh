#!/bin/bash
# Script para iniciar a Plataforma Analítica Lotus no Linux/macOS

# Navega para o diretório do backend onde o app.py está localizado
# Este script assume que você o executa a partir do diretório raiz do projeto (plataforma_clinica)

# Verifica se o diretório backend existe
if [ ! -d "backend" ]; then
    echo "Erro: Diretório 'backend' não encontrado. Execute este script a partir do diretório raiz do projeto 'plataforma_clinica'."
    exit 1
fi

# Verifica se o arquivo app.py existe
if [ ! -f "backend/app.py" ]; then
    echo "Erro: Arquivo 'backend/app.py' não encontrado."
    exit 1
fi

# Informa ao usuário que o servidor está iniciando
echo "Iniciando a Plataforma Analítica Lotus..."
echo "Por favor, aguarde alguns segundos."

# Executa a aplicação Flask
# É recomendado criar um ambiente virtual e instalar as dependências nele.
# Por exemplo:
# python3.11 -m venv venv
# source venv/bin/activate
# pip3 install Flask Flask-SQLAlchemy psycopg2-binary Werkzeug pandas openpyxl python-docx PyPDF2 matplotlib WeasyPrint
# python3.11 backend/app.py

# Comando direto para execução (assumindo que as dependências estão instaladas globalmente ou no ambiente ativo)
python3.11 backend/app.py

# Se o script terminar, pode ser devido a um erro no servidor Flask.
echo "Servidor Flask encerrado."

