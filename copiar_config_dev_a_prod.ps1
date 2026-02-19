# Script para copiar configuración de landing: desarrollo → producción

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  COPIAR CONFIGURACION LANDING: DESARROLLO -> PRODUCCION" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""

$API_DEV = "http://localhost:8000"
$API_PROD = "https://api.masasestacion.cl"
$EMAIL = "admin@fme.cl"
$PASSWORD = "admin"

# 1. Autenticar en desarrollo
Write-Host "1. Obteniendo configuracion de DESARROLLO..." -ForegroundColor Yellow

try {
    $loginDev = Invoke-RestMethod `
        -Uri "$API_DEV/api/auth/token" `
        -Method Post `
        -Body @{username=$EMAIL; password=$PASSWORD} `
        -ContentType "application/x-www-form-urlencoded"
    
    $headersDev = @{
        "Authorization" = "Bearer $($loginDev.access_token)"
        "Content-Type" = "application/json; charset=utf-8"
    }
    
    $configDev = Invoke-RestMethod `
        -Uri "$API_DEV/api/admin/configuracion-landing/1" `
        -Headers $headersDev
    
    Write-Host "   Config obtenida de desarrollo" -ForegroundColor Green
    Write-Host "   Nombre comercial: $($configDev.nombre_comercial)" -ForegroundColor White
    
} catch {
    Write-Host "   ERROR en desarrollo: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   Asegurate que Docker este corriendo: docker-compose up -d" -ForegroundColor Yellow
    exit 1
}

# 2. Autenticar en producción
Write-Host ""
Write-Host "2. Autenticando en PRODUCCION..." -ForegroundColor Yellow

try {
    $loginProd = Invoke-RestMethod `
        -Uri "$API_PROD/api/auth/token" `
        -Method Post `
        -Body @{username=$EMAIL; password=$PASSWORD} `
        -ContentType "application/x-www-form-urlencoded"
    
    $headersProd = @{
        "Authorization" = "Bearer $($loginProd.access_token)"
        "Content-Type" = "application/json; charset=utf-8"
    }
    
    Write-Host "   Token obtenido" -ForegroundColor Green
    
} catch {
    Write-Host "   ERROR: No se pudo autenticar en produccion" -ForegroundColor Red
    exit 1
}

# 3. Preparar datos (remover campos readonly)
Write-Host ""
Write-Host "3. Preparando datos para crear/actualizar..." -ForegroundColor Yellow

# Crear objeto sin campos readonly (id, created_at, updated_at)
$configData = @{
    tenant_id = $configDev.tenant_id
    nombre_comercial = $configDev.nombre_comercial
    logo_url = $configDev.logo_url
    favicon_url = $configDev.favicon_url
    colores = $configDev.colores
    hero_titulo = $configDev.hero_titulo
    hero_subtitulo = $configDev.hero_subtitulo
    hero_imagen_url = $configDev.hero_imagen_url
    hero_cta_texto = $configDev.hero_cta_texto
    hero_cta_link = $configDev.hero_cta_link
    hero_badges = $configDev.hero_badges
    beneficios = $configDev.beneficios
    telefono = $configDev.telefono
    email = $configDev.email
    direccion = $configDev.direccion
    redes_sociales = $configDev.redes_sociales
    texto_footer_descripcion = $configDev.texto_footer_descripcion
    texto_copyright = $configDev.texto_copyright
    meta_title = $configDev.meta_title
    meta_description = $configDev.meta_description
    mostrar_precios = $configDev.mostrar_precios
    mostrar_stock = $configDev.mostrar_stock
    habilitar_carrito = $configDev.habilitar_carrito
} | ConvertTo-Json -Depth 10

# 4. Verificar si ya existe en producción
Write-Host ""
Write-Host "4. Verificando si ya existe en produccion..." -ForegroundColor Yellow

$existeConfig = $false
try {
    $configExistente = Invoke-RestMethod `
        -Uri "$API_PROD/api/admin/configuracion-landing/1" `
        -Headers $headersProd
    
    $existeConfig = $true
    Write-Host "   Ya existe configuracion (ID: $($configExistente.id))" -ForegroundColor Yellow
    Write-Host "   Se actualizara..." -ForegroundColor Yellow
    
} catch {
    Write-Host "   No existe configuracion, se creara nueva..." -ForegroundColor Yellow
}

# 5. Crear o actualizar
Write-Host ""
if ($existeConfig) {
    Write-Host "5. Actualizando configuracion en produccion..." -ForegroundColor Yellow
    
    try {
        $response = Invoke-RestMethod `
            -Uri "$API_PROD/api/admin/configuracion-landing/1" `
            -Method Put `
            -Body ([System.Text.Encoding]::UTF8.GetBytes($configData)) `
            -Headers $headersProd
        
        Write-Host "   ACTUALIZADO exitosamente" -ForegroundColor Green
        
    } catch {
        Write-Host "   ERROR: $($_.ErrorDetails.Message)" -ForegroundColor Red
        exit 1
    }
    
} else {
    Write-Host "5. Creando configuracion en produccion..." -ForegroundColor Yellow
    
    try {
        $response = Invoke-RestMethod `
            -Uri "$API_PROD/api/admin/configuracion-landing/" `
            -Method Post `
            -Body ([System.Text.Encoding]::UTF8.GetBytes($configData)) `
            -Headers $headersProd
        
        Write-Host "   CREADO exitosamente (ID: $($response.id))" -ForegroundColor Green
        
    } catch {
        Write-Host "   ERROR: $($_.ErrorDetails.Message)" -ForegroundColor Red
        exit 1
    }
}

# 6. Verificar acceso público
Write-Host ""
Write-Host "6. Verificando acceso publico en produccion..." -ForegroundColor Yellow

Start-Sleep -Seconds 2

try {
    $testResponse = Invoke-RestMethod `
        -Uri "$API_PROD/api/config/landing" `
        -Headers @{"X-Forwarded-Host" = "www.masasestacion.cl"}
    
    Write-Host "   EXITO! Landing funcionando correctamente" -ForegroundColor Green
    Write-Host ""
    Write-Host "   Tenant: $($testResponse.tenant.nombre)" -ForegroundColor White
    Write-Host "   Nombre: $($testResponse.branding.nombre_comercial)" -ForegroundColor White
    Write-Host "   Hero: $($testResponse.hero.titulo)" -ForegroundColor White
    
} catch {
    Write-Host "   ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  COPIA COMPLETADA" -ForegroundColor Cyan
Write-Host "  Prueba ahora en tu navegador: www.masasestacion.cl" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""
