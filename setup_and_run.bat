@echo off
REM Script para configurar o ambiente e iniciar a Plataforma Analítica Lotus no Windows

echo Bem-vindo ao script de configuracao e execucao da Plataforma Analitica Lotus!
echo Este script ira guia-lo atraves da criacao de um ambiente virtual, instalacao de dependencias e inicializacao da aplicacao.
echo --------------------------------------------------------------------------------

REM Verifica se o Python está acessível
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo ERRO: Python nao encontrado. Por favor, instale Python 3.11 ou superior e adicione-o ao PATH.
    pause
    exit /b 1
)

REM Navega para o diretório do script (assumindo que está na raiz do projeto)
cd /D "%~dp0"

REM Verifica se o diretório backend existe
IF NOT EXIST "src" (
    echo ERRO: Diretorio 'src' nao encontrado. Certifique-se de que este script esta na raiz do projeto 'plataforma_clinica'.
    pause
    exit /b 1
)

REM 1. Criação do Ambiente Virtual
IF NOT EXIST "venv" (
    echo Criando ambiente virtual 'venv'...
    python -m venv venv
    IF %ERRORLEVEL% NEQ 0 (
        echo ERRO: Falha ao criar o ambiente virtual. Verifique sua instalacao do Python.
        pause
        exit /b 1
    )
) ELSE (
    echo Ambiente virtual 'venv' ja existe.
)

REM 2. Ativação do Ambiente Virtual
echo Ativando ambiente virtual...
CALL .\venv\Scripts\activate.bat
IF %ERRORLEVEL% NEQ 0 (
    echo ERRO: Falha ao ativar o ambiente virtual.
    pause
    exit /b 1
)

REM 3. Instalação das Dependências
echo Instalando dependencias Python... Isso pode levar alguns minutos.
REM Lista de dependências
SET DEPENDENCIES=Flask Flask-SQLAlchemy psycopg2-binary Werkzeug pandas openpyxl python-docx PyPDF2 matplotlib WeasyPrint

echo Instalando: %DEPENDENCIES%
pip install %DEPENDENCIES%
IF %ERRORLEVEL% NEQ 0 (
    echo AVISO: Ocorreu um erro durante a instalacao de uma ou mais dependencias. Verifique sua conexao com a internet ou os logs de erro do pip.
    REM Considerar não sair imediatamente para permitir que o usuário veja a mensagem
)

echo --------------------------------------------------------------------------------
echo IMPORTANTE: Configuracao do Banco de Dados
echo --------------------------------------------------------------------------------
echo Antes de executar a aplicacao, voce PRECISA configurar a conexao com o banco de dados.
echo 1. Abra o arquivo: src\app.py
echo 2. Localize a linha: app.config["SQLALCHEMY_DATABASE_URI"] = ...
echo 3. SUBSTITUA as credenciais e nome do seu banco de dados PostgreSQL (ou MySQL, ajustando a string e dependencia).
echo    com as credenciais e nome do seu banco de dados PostgreSQL (ou MySQL, ajustando a string e dependencia).
echo 4. Certifique-se de que o servico do seu banco de dados (PostgreSQL/MySQL) esta em execucao.
echo --------------------------------------------------------------------------------
pause

REM 4. Execução da Plataforma
echo Iniciando a Plataforma Analitica Lotus...
echo A aplicacao estara acessivel em http://localhost:5000 ou http://0.0.0.0:5000 no seu navegador.
echo Pressione Ctrl+C na janela do servidor para encerrar.

python src\app.py

REM Desativa o ambiente virtual ao sair (opcional, pois o script termina)
REM CALL .\venv\Scripts\deactivate.bat

echo Servidor Flask encerrado.
pause

