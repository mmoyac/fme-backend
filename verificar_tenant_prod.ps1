# Script para verificar configuración del tenant en producción

$API_BASE = "https://api.masasestacion.cl"
$EMAIL = "admin@fme.cl"
$PASSWORD = "admin"

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  VERIFICACION DE TENANT EN PRODUCCION" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""

# 1. Autenticacion
Write-Host "1. Autenticando..." -ForegroundColor Yellow
$loginBody = @{
    username = $EMAIL
    password = $PASSWORD
}

try {
    $loginResponse = Invoke-RestMethod `
        -Uri "$API_BASE/api/auth/token" `
        -Method Post `
        -Body $loginBody `
        -ContentType "application/x-www-form-urlencoded"
    
    $token = $loginResponse.access_token
    $headers = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
    }
    Write-Host "   Token obtenido" -ForegroundColor Green
} catch {
    Write-Host "   ERROR: No se pudo autenticar" -ForegroundColor Red
    exit 1
}

# 2. Obtener tenants
Write-Host ""
Write-Host "2. Obteniendo configuracion de tenants..." -ForegroundColor Yellow

try {
    $tenants = Invoke-RestMethod -Uri "$API_BASE/api/tenants/" -Headers $headers
    
    Write-Host ""
    Write-Host "   ID  Codigo            Nombre              Dominio Principal         Subdomain" -ForegroundColor Cyan
    Write-Host "   --- ----------------- ------------------- ------------------------- -----------------" -ForegroundColor Cyan
    
    foreach ($tenant in $tenants) {
        $dominio = if ($tenant.dominio_principal) { $tenant.dominio_principal } else { "(sin dominio)" }
        $subdomain = if ($tenant.subdomain) { $tenant.subdomain } else { "(sin subdomain)" }
        $activo = if ($tenant.activo) { "SI" } else { "NO" }
        
        Write-Host ("   {0,-3} {1,-17} {2,-19} {3,-25} {4,-17}" -f $tenant.id, $tenant.codigo, $tenant.nombre, $dominio, $subdomain) -ForegroundColor White
        Write-Host ("       Activo: {0}" -f $activo) -ForegroundColor $(if ($tenant.activo) { "Green" } else { "Red" })
    }
} catch {
    Write-Host "   ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 3. Probar detección con diferentes hostnames
Write-Host ""
Write-Host "3. Probando deteccion de tenant..." -ForegroundColor Yellow

$hostnames = @(
    "masasestacion.cl",
    "www.masasestacion.cl",
    "admin.masasestacion.cl",
    "elolivo.masasestacion.cl"
)

foreach ($hostname in $hostnames) {
    Write-Host ""
    Write-Host "   Probando: $hostname" -ForegroundColor Cyan
    
    try {
        $response = Invoke-RestMethod `
            -Uri "$API_BASE/api/config/landing" `
            -Headers @{
                "X-Forwarded-Host" = $hostname
            }
        
        Write-Host "      Tenant detectado: $($response.tenant.nombre) (ID: $($response.tenant.id))" -ForegroundColor Green
        Write-Host "      Activo: $($response.tenant.activo)" -ForegroundColor Green
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "      ERROR: Status $statusCode" -ForegroundColor Red
        
        if ($statusCode -eq 404) {
            Write-Host "      Motivo: Tenant no encontrado para este hostname" -ForegroundColor Yellow
        } elseif ($statusCode -eq 403) {
            Write-Host "      Motivo: Tenant suspendido" -ForegroundColor Yellow
        }
    }
}

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""
