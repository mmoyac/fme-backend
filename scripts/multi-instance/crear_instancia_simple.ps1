# Script simplificado para crear instancia retail
param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("panaderia", "carniceria", "lacteos", "retail")]
    [string]$Tipo
)

$ErrorActionPreference = "Stop"

# Configuración de puertos por instancia
$ConfigPuertos = @{
    "panaderia" = @{ "backend" = 8000; "landing" = 3000; "backoffice" = 3001; "db" = 5432 }
    "carniceria" = @{ "backend" = 8002; "landing" = 3002; "backoffice" = 3003; "db" = 5434 }
    "lacteos" = @{ "backend" = 8004; "landing" = 3004; "backoffice" = 3005; "db" = 5436 }
    "retail" = @{ "backend" = 8006; "landing" = 3006; "backoffice" = 3007; "db" = 5438 }
}

# Rutas base
$RutaBase = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$RutaInstancias = Join-Path $RutaBase "_instancias_locales"
$RutaTemplates = Join-Path $RutaBase "docs\multi-instance-templates\$Tipo"

Write-Host "Creando instancia: $($Tipo.ToUpper())" -ForegroundColor Green

# Crear directorio de instancias si no existe
if (!(Test-Path $RutaInstancias)) {
    Write-Host "Creando directorio de instancias: $RutaInstancias" -ForegroundColor Blue
    New-Item -ItemType Directory -Path $RutaInstancias -Force | Out-Null
    
    # Crear .gitignore
    Set-Content -Path (Join-Path $RutaInstancias ".gitignore") -Value "# Instancias locales`n*`n!.gitkeep`n!README.md"
    New-Item -ItemType File -Path (Join-Path $RutaInstancias ".gitkeep") -Force | Out-Null
    Set-Content -Path (Join-Path $RutaInstancias "README.md") -Value "# Instancias Locales"
}

# Crear instancia específica
$rutaInstancia = Join-Path $RutaInstancias $Tipo

if (Test-Path $rutaInstancia) {
    Write-Host "ADVERTENCIA: Instancia $Tipo ya existe" -ForegroundColor Yellow
} else {
    Write-Host "Verificando template: $RutaTemplates" -ForegroundColor Blue
    
    if (!(Test-Path $RutaTemplates)) {
        Write-Host "ERROR: Template no encontrado en $RutaTemplates" -ForegroundColor Red
        exit 1
    }
    
    # Crear directorios
    New-Item -ItemType Directory -Path $rutaInstancia -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $rutaInstancia "data") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $rutaInstancia "volumes") -Force | Out-Null
    
    # Copiar templates
    Copy-Item -Path "$RutaTemplates\*" -Destination $rutaInstancia -Recurse -Force
    
    Write-Host "EXITO: Instancia $Tipo creada en: $rutaInstancia" -ForegroundColor Green
    Write-Host "Archivos copiados desde template" -ForegroundColor Green
}

Write-Host "Puertos configurados para $Tipo :" -ForegroundColor Cyan
Write-Host "  Backend:    $($ConfigPuertos[$Tipo]['backend'])" -ForegroundColor Gray
Write-Host "  Landing:    $($ConfigPuertos[$Tipo]['landing'])" -ForegroundColor Gray
Write-Host "  Backoffice: $($ConfigPuertos[$Tipo]['backoffice'])" -ForegroundColor Gray
Write-Host "  Database:   $($ConfigPuertos[$Tipo]['db'])" -ForegroundColor Gray

Write-Host ""
Write-Host "Siguiente paso: Llenar CSVs en: $rutaInstancia\data\" -ForegroundColor Yellow