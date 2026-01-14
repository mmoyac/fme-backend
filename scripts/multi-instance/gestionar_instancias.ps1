# Script principal para gestionar múltiples instancias del sistema ecommerce
# Ubicación: fme-backend/scripts/multi-instance/gestionar_instancias.ps1
# Uso: .\scripts\multi-instance\gestionar_instancias.ps1 -Accion [levantar|parar|estado] [-Tipo panaderia] [-Todas]

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("levantar", "parar", "estado", "logs", "rebuild", "crear", "limpiar")]
    [string]$Accion,
    
    [ValidateSet("panaderia", "carniceria", "lacteos", "retail")]
    [string]$Tipo,
    
    [switch]$Todas,
    [switch]$Forzar
)

$ErrorActionPreference = "Stop"

# Configuración de instancias disponibles
$Instancias = @("panaderia", "carniceria", "lacteos", "retail")

# Configuración de puertos por instancia
$ConfigPuertos = @{
    "panaderia" = @{ "backend" = 8000; "landing" = 3000; "backoffice" = 3001; "db" = 5432; "color" = "Brown" }
    "carniceria" = @{ "backend" = 8002; "landing" = 3002; "backoffice" = 3003; "db" = 5434; "color" = "Red" }
    "lacteos" = @{ "backend" = 8004; "landing" = 3004; "backoffice" = 3005; "db" = 5436; "color" = "Blue" }
    "retail" = @{ "backend" = 8006; "landing" = 3006; "backoffice" = 3007; "db" = 5438; "color" = "Green" }
}

# Rutas base - desde el directorio del backend
$RutaBase = Split-Path -Parent (Split-Path -Parent $PSScriptRoot) # Dos niveles arriba desde scripts/multi-instance
$RutaInstancias = Join-Path $RutaBase "_instancias_locales"

function Show-Banner {
    Write-Host "🏢 ====== GESTOR MULTI-INSTANCIA ECOMMERCE ======" -ForegroundColor Green
    Write-Host "   Repositorio: fme-backend" -ForegroundColor Gray
    Write-Host "   Acción: $($Accion.ToUpper())" -ForegroundColor Cyan
    if ($Tipo) {
        Write-Host "   Instancia: $($Tipo.ToUpper())" -ForegroundColor Cyan
    }
    if ($Todas) {
        Write-Host "   Todas las instancias" -ForegroundColor Cyan
    }
    Write-Host "" 
}

function Initialize-InstancesDirectory {
    if (!(Test-Path $RutaInstancias)) {
        Write-Host "📁 Creando directorio de instancias en: $RutaInstancias" -ForegroundColor Blue
        New-Item -ItemType Directory -Path $RutaInstancias -Force | Out-Null
        
        # Crear .gitignore para excluir instancias locales
        $gitignoreContent = "# Instancias locales de desarrollo - no versionar`n*`n!.gitkeep`n!README.md"
        Set-Content -Path (Join-Path $RutaInstancias ".gitignore") -Value $gitignoreContent
        
        # Crear README explicativo
        $readmeContent = "# Instancias Locales de Desarrollo`n`nEste directorio contiene las instancias locales del sistema multi-negocio.`n**No se versiona en Git** - solo existe en tu maquina local.`n`n## Estructura Generada:`n_instancias_locales/"
├── panaderia/
│   ├── docker-compose.yml
│   ├── .env.local
│   ├── data/
│   └── volumes/
├── carniceria/
└── lacteos/
\`\`\`

## Crear Instancias:
\`\`\`bash
# Desde el directorio del backend
.\scripts\multi-instance\gestionar_instancias.ps1 -Accion crear -Tipo panaderia
\`\`\`
"@
        Set-Content -Path (Join-Path $RutaInstancias "README.md") -Value $readmeContent
        
        # Crear archivo .gitkeep
        New-Item -ItemType File -Path (Join-Path $RutaInstancias ".gitkeep") -Force | Out-Null
    }
}

function Get-InstancesToProcess {
    if ($Todas) {
        return $Instancias
    } elseif ($Tipo) {
        return @($Tipo)
    } else {
        Write-Host "❌ Error: Debe especificar -Tipo o -Todas" -ForegroundColor Red
        exit 1
    }
}

function Test-InstanceExists {
    param([string]$Instance)
    $rutaInstancia = Join-Path $RutaInstancias $Instance
    return Test-Path (Join-Path $rutaInstancia "docker-compose.yml")
}

function New-Instance {
    param([string]$Instance)
    
    Write-Host "🏗️ Creando nueva instancia: $($Instance.ToUpper())" -ForegroundColor Green
    
    $rutaInstancia = Join-Path $RutaInstancias $Instance
    $rutaTemplates = Join-Path $PSScriptRoot "..\..\docs\multi-instance-templates\$Instance"
    
    if (!(Test-Path $rutaTemplates)) {
        throw "Template para '$Instance' no encontrado en: $rutaTemplates"
    }
    
    # Crear directorio de la instancia
    New-Item -ItemType Directory -Path $rutaInstancia -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $rutaInstancia "data") -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $rutaInstancia "volumes") -Force | Out-Null
    
    # Copiar templates
    Copy-Item -Path "$rutaTemplates\*" -Destination $rutaInstancia -Recurse -Force
    
    Write-Host "   ✅ Instancia $Instance creada en: $rutaInstancia" -ForegroundColor Green
    Write-Host "   📋 Archivos copiados desde templates" -ForegroundColor Green
    Write-Host "   📁 Directorios data/ y volumes/ creados" -ForegroundColor Green
}

function Get-InstanceStatus {
    param([string]$Instance)
    
    if (!(Test-InstanceExists $Instance)) {
        return "NO_CREADA"
    }
    
    $rutaInstancia = Join-Path $RutaInstancias $Instance
    Push-Location $rutaInstancia
    try {
        $containers = docker-compose ps -q 2>$null
        if (!$containers) {
            return "PARADA"
        }
        
        $running = 0
        $total = 0
        foreach ($container in $containers) {
            $total++
            $status = docker inspect -f '{{.State.Status}}' $container 2>$null
            if ($status -eq "running") {
                $running++
            }
        }
        
        if ($running -eq $total) {
            return "EJECUTANDOSE"
        } elseif ($running -gt 0) {
            return "PARCIAL"
        } else {
            return "PARADA"
        }
    } finally {
        Pop-Location
    }
}

function Show-InstancesStatus {
    Write-Host "📊 ESTADO DE TODAS LAS INSTANCIAS:" -ForegroundColor Blue
    Write-Host "   Ruta base: $RutaInstancias" -ForegroundColor Gray
    Write-Host ""
    
    foreach ($instance in $Instancias) {
        $status = Get-InstanceStatus $instance
        $puertos = $ConfigPuertos[$instance]
        
        $statusIcon = switch ($status) {
            "EJECUTANDOSE" { "[OK]" }
            "PARCIAL" { "[!]" }
            "PARADA" { "[X]" }
            "NO_CREADA" { "[-]" }
        }
        
        $statusColor = switch ($status) {
            "EJECUTANDOSE" { "Green" }
            "PARCIAL" { "Yellow" }
            "PARADA" { "Red" }
            "NO_CREADA" { "Gray" }
        }
        
        Write-Host "   $statusIcon $($instance.ToUpper())" -NoNewline -ForegroundColor $statusColor
        Write-Host " - $status" -ForegroundColor $statusColor
        
        if ($status -eq "EJECUTANDOSE") {
            Write-Host "      🌐 Backend: http://localhost:$($puertos.backend)/docs" -ForegroundColor Gray
            Write-Host "      🔧 Backoffice: http://localhost:$($puertos.backoffice)" -ForegroundColor Gray
            Write-Host "      🛒 Landing: http://localhost:$($puertos.landing)" -ForegroundColor Gray
        } elseif ($status -eq "NO_CREADA") {
            Write-Host "      💡 Crear con: -Accion crear -Tipo $instance" -ForegroundColor Gray
        }
        Write-Host ""
    }
}

function Execute-ActionOnInstance {
    param([string]$Instance, [string]$Action)
    
    $rutaInstancia = Join-Path $RutaInstancias $Instance
    $instanceUpper = $Instance.ToUpper()
    
    if ($Action -eq "crear") {
        if (Test-InstanceExists $Instance) {
            Write-Host "⚠️ Instancia $instanceUpper ya existe" -ForegroundColor Yellow
        } else {
            New-Instance $Instance
        }
        return
    }
    
    if (!(Test-InstanceExists $Instance)) {
        Write-Host "❌ Instancia $instanceUpper no existe. Crear primero con -Accion crear" -ForegroundColor Red
        return
    }
    
    Push-Location $rutaInstancia
    try {
        switch ($Action) {
            "levantar" {
                Write-Host "🚀 Levantando $instanceUpper..." -ForegroundColor Green
                docker-compose down -q 2>$null
                docker-compose up -d
            }
            "parar" {
                Write-Host "🛑 Parando $instanceUpper..." -ForegroundColor Yellow
                docker-compose down
            }
            "rebuild" {
                Write-Host "🔄 Rebuilding $instanceUpper..." -ForegroundColor Blue
                docker-compose down
                docker-compose build --no-cache
                docker-compose up -d
            }
            "logs" {
                Write-Host "📋 Logs de $instanceUpper..." -ForegroundColor Blue
                docker-compose logs -f
            }
            "limpiar" {
                Write-Host "🗑️ Limpiando $instanceUpper..." -ForegroundColor Red
                if ($Forzar) {
                    docker-compose down --rmi all --volumes
                    Remove-Item -Recurse -Force "volumes" -ErrorAction SilentlyContinue
                } else {
                    docker-compose down --rmi local
                }
            }
        }
    } finally {
        Pop-Location
    }
}

# MAIN EXECUTION
Show-Banner
Initialize-InstancesDirectory

if ($Accion -eq "estado") {
    Show-InstancesStatus
    exit 0
}

$instanciasToProcess = Get-InstancesToProcess

foreach ($instance in $instanciasToProcess) {
    try {
        Execute-ActionOnInstance $instance $Accion
        Write-Host "✅ $($instance.ToUpper()) - $($Accion.ToUpper()) completado" -ForegroundColor Green
    } catch {
        Write-Host "❌ $($instance.ToUpper()) - Error en $($Accion.ToUpper()): $_" -ForegroundColor Red
    }
    
    if ($instanciasToProcess.Count -gt 1) {
        Write-Host "----------------------------------------" -ForegroundColor Gray
    }
}

Write-Host "
🎉 OPERACIÓN COMPLETADA" -ForegroundColor Green
Write-Host "💡 Ver estado: .\scripts\multi-instance\gestionar_instancias.ps1 -Accion estado" -ForegroundColor Cyan