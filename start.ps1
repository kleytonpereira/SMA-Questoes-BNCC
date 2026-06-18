# start.ps1 — Inicia o SMA de Questoes BNCC
# Uso: .\start.ps1          (so o app local)
#      .\start.ps1 -Share   (app local + URL publica via ngrok)

param([switch]$Share)

$VENV   = "C:\Users\klues\.venvs\SMA-Questoes\Scripts"
$APP    = "$PSScriptRoot\app.py"
$PORT   = 8501

# 1. Garantir que o Ollama esta rodando
$ollamaRunning = Test-NetConnection -ComputerName 127.0.0.1 -Port 11434 -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
if (-not $ollamaRunning.TcpTestSucceeded) {
    Write-Host "Iniciando Ollama..." -ForegroundColor Cyan
    Start-Process "ollama" -ArgumentList "serve" -WindowStyle Hidden
    Start-Sleep -Seconds 3
} else {
    Write-Host "Ollama ja esta rodando." -ForegroundColor Green
}

# 2. Iniciar ngrok em background (opcional)
if ($Share) {
    $ngrok = Get-Command ngrok -ErrorAction SilentlyContinue
    if (-not $ngrok) {
        Write-Host ""
        Write-Host "ngrok nao encontrado. Instale em: https://ngrok.com/download" -ForegroundColor Yellow
        Write-Host "Apos instalar, rode: ngrok config add-authtoken <seu-token>" -ForegroundColor Yellow
        Write-Host "Continuando sem URL publica..." -ForegroundColor Yellow
    } else {
        Write-Host "Iniciando ngrok na porta $PORT..." -ForegroundColor Cyan
        Start-Process "ngrok" -ArgumentList "http $PORT" -WindowStyle Normal
        Start-Sleep -Seconds 2
        Write-Host "Acesse o painel do ngrok em http://localhost:4040 para ver a URL publica." -ForegroundColor Green
    }
}

# 3. Iniciar o Streamlit
Write-Host ""
Write-Host "Iniciando o app em http://localhost:$PORT ..." -ForegroundColor Cyan
Write-Host "Pressione Ctrl+C para encerrar." -ForegroundColor DarkGray
Write-Host ""

& "$VENV\streamlit.exe" run $APP --server.port $PORT
