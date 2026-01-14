# Script de PowerShell para deploy completo desde cero
# Uso: .\scripts\deploy_completo.ps1 -TipoNegocio "panaderia" -NombreCliente "Panadería San Juan" -EmailAdmin "admin@panaderiasanjuan.cl"

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("panaderia", "carniceria", "lacteos")]
    [string]$TipoNegocio,
    
    [Parameter(Mandatory=$true)]
    [string]$NombreCliente,
    
    [Parameter(Mandatory=$true)]
    [string]$EmailAdmin,
    
    [string]$Password = "admin123",
    
    [string]$BaseUrl = "http://localhost:8000",
    
    [switch]$Produccion
)

# Configurar URL según entorno
if ($Produccion) {
    $BaseUrl = "https://api.masasestacion.cl"
    Write-Host "🌍 MODO PRODUCCIÓN ACTIVADO - URL: $BaseUrl" -ForegroundColor Yellow
}

Write-Host "🚀 INICIANDO DEPLOY COMPLETO DESDE CERO" -ForegroundColor Green
Write-Host "   Cliente: $NombreCliente" -ForegroundColor Cyan
Write-Host "   Tipo: $TipoNegocio" -ForegroundColor Cyan
Write-Host "   Admin: $EmailAdmin" -ForegroundColor Cyan
Write-Host "   Base URL: $BaseUrl" -ForegroundColor Cyan

# Función para verificar si estamos en el directorio correcto
function Test-BackendDirectory {
    if (!(Test-Path ".\main.py") -or !(Test-Path ".\database\models.py")) {
        Write-Host "❌ Error: No estás en el directorio del backend (fme-backend)" -ForegroundColor Red
        Write-Host "   Navega al directorio fme-backend antes de ejecutar este script" -ForegroundColor Yellow
        exit 1
    }
}

# Función para verificar el entorno virtual
function Test-VirtualEnvironment {
    if (!(Test-Path ".\venv\Scripts\python.exe")) {
        Write-Host "❌ Error: Entorno virtual no encontrado en .\venv\" -ForegroundColor Red
        Write-Host "   Ejecuta: python -m venv venv" -ForegroundColor Yellow
        Write-Host "   Luego: .\venv\Scripts\python.exe -m pip install -r requirements.txt" -ForegroundColor Yellow
        exit 1
    }
}

# Función para verificar conectividad
function Test-APIConnectivity {
    param([string]$Url)
    try {
        $response = Invoke-WebRequest -Uri "$Url/docs" -Method HEAD -TimeoutSec 10
        return $true
    }
    catch {
        return $false
    }
}

# Validaciones iniciales
Test-BackendDirectory
Test-VirtualEnvironment

Write-Host "`n🔍 PASO 1: VALIDACIONES INICIALES" -ForegroundColor Blue

# Verificar conectividad con la API
Write-Host "   Verificando conectividad con $BaseUrl..." -NoNewline
if (Test-APIConnectivity -Url $BaseUrl) {
    Write-Host " ✅" -ForegroundColor Green
} else {
    Write-Host " ❌" -ForegroundColor Red
    Write-Host "   Error: No se puede conectar a la API en $BaseUrl" -ForegroundColor Red
    Write-Host "   Verificar que el backend esté ejecutándose" -ForegroundColor Yellow
    exit 1
}

# Ejecutar validación de sistema limpio
Write-Host "`n   Ejecutando validación de sistema limpio..."
$validationResult = & .\venv\Scripts\python.exe scripts\validar_deploy_limpio.py --cliente "$NombreCliente"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Error en validación del sistema" -ForegroundColor Red
    exit 1
}

Write-Host "`n📋 PASO 2: CONFIGURACIÓN DEL SISTEMA BASE" -ForegroundColor Blue

# Ejecutar scripts de seed de sistema base (solo si es necesario)
Write-Host "   Configurando tablas maestras..."
& .\venv\Scripts\python.exe scripts\seed_maestras_prod.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ⚠️ Warning: Error en seed maestras (puede ser normal si ya existen)" -ForegroundColor Yellow
}

Write-Host "   Configurando tipos de venta..."
& .\venv\Scripts\python.exe scripts\seed_tipos_venta.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ⚠️ Warning: Error en seed tipos venta" -ForegroundColor Yellow
}

Write-Host "   Configurando tipos de proveedor..."
& .\venv\Scripts\python.exe scripts\seed_tipos_proveedor.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ⚠️ Warning: Error en seed tipos proveedor" -ForegroundColor Yellow
}

Write-Host "   Configurando roles y usuarios..."
& .\venv\Scripts\python.exe scripts\seed_roles_prod.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ⚠️ Warning: Error en seed roles" -ForegroundColor Yellow
}

Write-Host "   Configurando menú del sistema..."
& .\venv\Scripts\python.exe scripts\seed_menu_rbac.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ⚠️ Warning: Error en seed menú" -ForegroundColor Yellow
}

Write-Host "`n🏪 PASO 3: DEPLOY DEL CLIENTE" -ForegroundColor Blue

# Ejecutar deploy principal
Write-Host "   Ejecutando deploy automático del cliente..."
& .\venv\Scripts\python.exe scripts\deploy_nuevo_cliente.py --tipo $TipoNegocio --nombre "$NombreCliente" --email $EmailAdmin --password $Password

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n🎉 DEPLOY COMPLETADO EXITOSAMENTE" -ForegroundColor Green
    Write-Host "`n📋 INFORMACIÓN DE ACCESO:" -ForegroundColor Cyan
    Write-Host "   🌐 Frontend Landing: " -NoNewline -ForegroundColor White
    Write-Host "$($BaseUrl.Replace('api.', '').Replace('8000', '3000'))" -ForegroundColor Yellow
    Write-Host "   🔧 Backoffice Admin: " -NoNewline -ForegroundColor White  
    Write-Host "$($BaseUrl.Replace('api.', 'admin.').Replace('8000', '3001'))" -ForegroundColor Yellow
    Write-Host "   📚 API Docs: " -NoNewline -ForegroundColor White
    Write-Host "$BaseUrl/docs" -ForegroundColor Yellow
    Write-Host "`n🔐 CREDENCIALES:" -ForegroundColor Cyan
    Write-Host "   Usuario: $EmailAdmin" -ForegroundColor White
    Write-Host "   Password: $Password" -ForegroundColor White
    
    Write-Host "`n📋 PRÓXIMOS PASOS:" -ForegroundColor Cyan
    Write-Host "   1. ✅ Verificar acceso al backoffice" -ForegroundColor White
    Write-Host "   2. 📦 Configurar inventario inicial por local" -ForegroundColor White
    Write-Host "   3. 💰 Ajustar precios si es necesario" -ForegroundColor White
    Write-Host "   4. 💳 Configurar medios de pago (MercadoPago, etc)" -ForegroundColor White
    Write-Host "   5. 🧪 Probar flujo completo de pedidos en landing" -ForegroundColor White
    
    Write-Host "`n📊 REPORTES GENERADOS:" -ForegroundColor Cyan
    Write-Host "   📄 Deploy: docs/deploy_reports/" -ForegroundColor White
    Write-Host "   🔍 Validación: docs/validation_reports/" -ForegroundColor White
    
} else {
    Write-Host "`n❌ ERROR EN EL DEPLOY" -ForegroundColor Red
    Write-Host "   Revisar los logs anteriores para identificar el problema" -ForegroundColor Yellow
    Write-Host "   Archivos de template disponibles en: docs/deploy_templates/$TipoNegocio/" -ForegroundColor Yellow
    exit 1
}

Write-Host "`n🎯 DEPLOY FINALIZADO PARA: $NombreCliente" -ForegroundColor Green