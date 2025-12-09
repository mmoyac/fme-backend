# Script para ejecutar tests en PowerShell
Write-Host "🧪 Ejecutando tests del backend..." -ForegroundColor Cyan
Write-Host ""

# Navegar al directorio del backend
Set-Location -Path "D:\ProyectosAI\Masas_Estacion\fme-backend"

# Activar entorno virtual si existe
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "Activando entorno virtual..." -ForegroundColor Yellow
    & .venv\Scripts\Activate.ps1
} else {
    Write-Host "⚠️  Entorno virtual no encontrado. Usando Python global." -ForegroundColor Yellow
}

# Ejecutar tests
Write-Host "Ejecutando suite de tests..." -ForegroundColor Green
pytest tests/ -v --tb=short

Write-Host ""
Write-Host "✅ Tests completados!" -ForegroundColor Green
