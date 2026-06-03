@echo off
chcp 65001 >nul
echo ================================================
echo   Kinga Finance AI - Instalação e Execução
echo ================================================
echo.

:: Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python não encontrado!
    echo.
    echo Por favor instale o Python 3.11+ em:
    echo https://www.python.org/downloads/
    echo.
    echo Marque "Add Python to PATH" durante a instalação.
    pause
    exit /b 1
)

echo [OK] Python encontrado.
echo.

:: Instala dependências do backend
echo Instalando dependências do backend...
python -m pip install -r backend\requirements.txt -q
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependências do backend.
    pause
    exit /b 1
)
echo [OK] Backend instalado.

:: Instala dependências do dashboard
echo Instalando dependências do dashboard...
python -m pip install -r dashboard\requirements.txt -q
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependências do dashboard.
    pause
    exit /b 1
)
echo [OK] Dashboard instalado.

echo.
echo ================================================
echo   Instalação concluída!
echo ================================================
echo.
echo Para iniciar, use:
echo.
echo   1. API (backend):
echo      python run.py
echo      Acesse: http://localhost:8000/docs
echo.
echo   2. Dashboard:
echo      python run.py dashboard
echo      Acesse: http://localhost:8501
echo.
echo   3. Relatório no terminal:
echo      python run.py report
echo.
pause
