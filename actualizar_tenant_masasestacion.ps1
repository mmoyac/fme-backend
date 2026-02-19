# Script para actualizar configuración del tenant Masas Estación

$API_BASE = "https://api.masasestacion.cl"
$EMAIL = "admin@fme.cl"
$PASSWORD = "admin"

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  ACTUALIZAR TENANT MASAS ESTACION" -ForegroundColor Cyan
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
        "Content-Type" = "application/json; charset=utf-8"
    }
    Write-Host "   Token obtenido" -ForegroundColor Green
} catch {
    Write-Host "   ERROR: No se pudo autenticar" -ForegroundColor Red
    exit 1
}

# 2. Obtener tenant actual
Write-Host ""
Write-Host "2. Obteniendo tenant actual..." -ForegroundColor Yellow

try {
    $tenant = Invoke-RestMethod -Uri "$API_BASE/api/tenants/1" -Headers $headers
    
    Write-Host "   ID: $($tenant.id)" -ForegroundColor White
    Write-Host "   Codigo: $($tenant.codigo)" -ForegroundColor White
    Write-Host "   Nombre: $($tenant.nombre)" -ForegroundColor White
    Write-Host "   Dominio actual: $($tenant.dominio_principal)" -ForegroundColor White
    Write-Host "   Subdomain actual: $($tenant.subdomain)" -ForegroundColor White
    Write-Host "   Activo: $($tenant.activo)" -ForegroundColor White
} catch {
    Write-Host "   ERROR: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 3. Actualizar configuración
Write-Host ""
Write-Host "3. Actualizando configuracion..." -ForegroundColor Yellow

$updateData = @{
    nombre = "Masas Estacion"
    dominio_principal = "masasestacion.cl"
    subdomain = "masasestacion"
    activo = $true
} | ConvertTo-Json -Depth 10

Write-Host "   Datos a actualizar:" -ForegroundColor Cyan
Write-Host "   - Nombre: Masas Estacion" -ForegroundColor White
Write-Host "   - Dominio: masasestacion.cl" -ForegroundColor White
Write-Host "   - Subdomain: masasestacion" -ForegroundColor White
Write-Host "   - Activo: true" -ForegroundColor White

try {
    $response = Invoke-RestMethod `
        -Uri "$API_BASE/api/tenants/1" `
        -Method Put `
        -Body ([System.Text.Encoding]::UTF8.GetBytes($updateData)) `
        -Headers $headers
    
    Write-Host ""
    Write-Host "   Actualizado exitosamente" -ForegroundColor Green
} catch {
    Write-Host "   ERROR: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "   Detalles: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
    exit 1
}

# 4. Verificar actualización
Write-Host ""
Write-Host "4. Verificando actualizacion..." -ForegroundColor Yellow

try {
    $tenantActualizado = Invoke-RestMethod -Uri "$API_BASE/api/tenants/1" -Headers $headers
    
    Write-Host "   Dominio: $($tenantActualizado.dominio_principal)" -ForegroundColor Green
    Write-Host "   Subdomain: $($tenantActualizado.subdomain)" -ForegroundColor Green
} catch {
    Write-Host "   ERROR al verificar" -ForegroundColor Red
}

# 5. Probar detección nuevamente
Write-Host ""
Write-Host "5. Probando deteccion con masasestacion.cl..." -ForegroundColor Yellow

Start-Sleep -Seconds 2

try {
    $testResponse = Invoke-RestMethod `
        -Uri "$API_BASE/api/config/landing" `
        -Headers @{
            "X-Forwarded-Host" = "masasestacion.cl"
        }
    
    Write-Host "   EXITO! Tenant detectado: $($testResponse.tenant.nombre)" -ForegroundColor Green
} catch {
    Write-Host "   AUN HAY ERROR: Status $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
}

# 6. Probar con www
Write-Host ""
Write-Host "6. Probando deteccion con www.masasestacion.cl..." -ForegroundColor Yellow

try {
    $testResponse = Invoke-RestMethod `
        -Uri "$API_BASE/api/config/landing" `
        -Headers @{
            "X-Forwarded-Host" = "www.masasestacion.cl"
        }
    
    Write-Host "   EXITO! Tenant detectado: $($testResponse.tenant.nombre)" -ForegroundColor Green
} catch {
    Write-Host "   ERROR: Status $($_.Exception.Response.StatusCode.value__)" -ForegroundColor Red
    Write-Host "   NOTA: www.masasestacion.cl NO matchea. Necesita configuracion adicional." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  COMPLETADO" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""
