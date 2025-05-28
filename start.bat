@echo off
REM Script para iniciar a Plataforma Analítica Lotus no Windows

REM Navega para o diretório do backend onde o app.py está localizado
REM Este script assume que você o executa a partir do diretório raiz do projeto (plataforma_clinica)

REM Verifica se o diretório backend existe
IF NOT EXIST "backend" (
    echo Erro: Diretorio 'backend' nao encontrado. Execute este script a partir do diretorio raiz do projeto 'plataforma_clinica'.
    pause
    exit /b 1
)

REM Verifica se o arquivo app.py existe
IF NOT EXIST "backend\app.py" (
    echo Erro: Arquivo 'backend\app.py' nao encontrado.
    pause
    exit /b 1
)

REM Informa ao usuário que o servidor está iniciando
echo Iniciando a Plataforma Analitica Lotus...
echo Por favor, aguarde alguns segundos.

REM Executa a aplicação Flask
REM É recomendado criar um ambiente virtual e instalar as dependências nele.
REM Por exemplo:
REM python -m venv venv
REM .\venv\Scripts\activate
REM pip install Flask Flask-SQLAlchemy psycopg2-binary Werkzeug pandas openpyxl python-docx PyPDF2 matplotlib WeasyPrint
REM python backend\app.py

REM Comando direto para execução (assumindo que python está no PATH e as dependências estão instaladas)
python backend\app.py

REM Se o script terminar, pode ser devido a um erro no servidor Flask.
echo Servidor Flask encerrado.
pause

