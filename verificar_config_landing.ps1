# Script para verificar y crear configuración de landing en producción

$API_BASE = "https://api.masasestacion.cl"
$EMAIL = "admin@fme.cl"
$PASSWORD = "admin"

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  VERIFICAR CONFIGURACION DE LANDING" -ForegroundColor Cyan
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

# 2. Verificar tenant
Write-Host ""
Write-Host "2. Verificando tenant..." -ForegroundColor Yellow

try {
    $tenant = Invoke-RestMethod -Uri "$API_BASE/api/tenants/1" -Headers $headers
    Write-Host "   Tenant: $($tenant.nombre)" -ForegroundColor Green
    Write-Host "   Dominio: $($tenant.dominio_principal)" -ForegroundColor Green
    Write-Host "   Activo: $($tenant.activo)" -ForegroundColor Green
} catch {
    Write-Host "   ERROR al obtener tenant" -ForegroundColor Red
    exit 1
}

# 3. Intentar obtener configuración de landing (autenticado)
Write-Host ""
Write-Host "3. Verificando configuracion de landing..." -ForegroundColor Yellow

try {
    $config = Invoke-RestMethod `
        -Uri "$API_BASE/api/admin/configuracion-landing" `
        -Headers $headers
    
    Write-Host "   EXISTE: Configuracion encontrada" -ForegroundColor Green
    Write-Host "   Nombre comercial: $($config.nombre_comercial)" -ForegroundColor White
    
} catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Write-Host "   ERROR: Status $statusCode" -ForegroundColor Red
    
    if ($statusCode -eq 404) {
        Write-Host ""
        Write-Host "   La configuracion NO EXISTE" -ForegroundColor Yellow
        Write-Host "   Necesitas crearla desde el backoffice en:" -ForegroundColor Yellow
        Write-Host "   https://admin.masasestacion.cl/admin/configuracion-landing" -ForegroundColor Cyan
    }
}

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""
