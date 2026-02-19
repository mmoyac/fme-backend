# Script para crear configuración de landing en producción

$API_BASE = "https://api.masasestacion.cl"
$EMAIL = "admin@fme.cl"
$PASSWORD = "admin"

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  CREAR CONFIGURACION DE LANDING - MASAS ESTACION" -ForegroundColor Cyan
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

# 2. Crear configuración de landing
Write-Host ""
Write-Host "2. Creando configuracion de landing..." -ForegroundColor Yellow

$configData = @{
    tenant_id = 1
    nombre_comercial = "Masas Estación"
    logo_url = "/logo-masas-estacion.png"
    favicon_url = "/favicon.ico"
    
    colores = @{
        primario = "#5EC8F2"
        secundario = "#45A29A"
        acento = "#F7A072"
        fondo_hero_inicio = "#1a1a2e"
        fondo_hero_fin = "#16213e"
    }
    
    hero_titulo = "Masas Frescas y Deliciosas"
    hero_subtitulo = "Hechas con amor y los mejores ingredientes"
    hero_imagen_url = "/hero-masas.jpg"
    hero_cta_texto = "Ver Productos"
    hero_cta_link = "#catalogo"
    hero_badges = @(
        @{icono = "check-circle"; texto = "Ingredientes Naturales"},
        @{icono = "truck"; texto = "Despacho Gratis"},
        @{icono = "clock"; texto = "Horneado Diario"}
    )
    
    beneficios = @(
        @{
            icono = "check-circle"
            titulo = "Calidad Garantizada"
            descripcion = "Solo usamos ingredientes premium seleccionados"
        },
        @{
            icono = "truck"
            titulo = "Delivery Rápido"
            descripcion = "Entrega el mismo día en toda la región"
        },
        @{
            icono = "heart"
            titulo = "Hecho con Amor"
            descripcion = "Recetas tradicionales de generación en generación"
        }
    )
    
    telefono = "+56912345678"
    email = "contacto@masasestacion.cl"
    direccion = "Santiago, Chile"
    
    redes_sociales = @{
        facebook = "https://facebook.com/masasestacion"
        instagram = "https://instagram.com/masasestacion"
        whatsapp = "+56912345678"
    }
    
    texto_footer_descripcion = "Masas Estación - Tradición y calidad en cada producto"
    texto_copyright = "© 2026 Masas Estación. Todos los derechos reservados."
    
    meta_title = "Masas Estación - Masas Frescas y Deliciosas"
    meta_description = "Compra las mejores masas artesanales en línea. Delivery rápido y productos frescos horneados diariamente."
    
    mostrar_precios = $true
    mostrar_stock = $true
    habilitar_carrito = $true
} | ConvertTo-Json -Depth 10

try {
    $response = Invoke-RestMethod `
        -Uri "$API_BASE/api/admin/configuracion-landing/" `
        -Method Post `
        -Body ([System.Text.Encoding]::UTF8.GetBytes($configData)) `
        -Headers $headers
    
    Write-Host "   EXITO! Configuracion creada" -ForegroundColor Green
    Write-Host "   ID: $($response.id)" -ForegroundColor White
    Write-Host "   Tenant: $($response.tenant_id)" -ForegroundColor White
} catch {
    $errorMsg = $_.ErrorDetails.Message
    Write-Host "   ERROR: $errorMsg" -ForegroundColor Red
    
    if ($errorMsg -like "*ya existe*") {
        Write-Host ""
        Write-Host "   La configuracion ya existe. Probando actualizar..." -ForegroundColor Yellow
        
        # Intentar UPDATE en lugar de CREATE
        try {
            $updateResponse = Invoke-RestMethod `
                -Uri "$API_BASE/api/admin/configuracion-landing/1" `
                -Method Put `
                -Body ([System.Text.Encoding]::UTF8.GetBytes($configData)) `
                -Headers $headers
            
            Write-Host "   EXITO! Configuracion actualizada" -ForegroundColor Green
        } catch {
            Write-Host "   ERROR al actualizar: $($_.ErrorDetails.Message)" -ForegroundColor Red
        }
    }
}

# 3. Verificar acceso público
Write-Host ""
Write-Host "3. Probando acceso publico..." -ForegroundColor Yellow

Start-Sleep -Seconds 2

try {
    $testResponse = Invoke-RestMethod `
        -Uri "$API_BASE/api/config/landing" `
        -Headers @{"X-Forwarded-Host" = "www.masasestacion.cl"}
    
    Write-Host "   EXITO! Landing cargada correctamente" -ForegroundColor Green
    Write-Host "   Tenant: $($testResponse.tenant.nombre)" -ForegroundColor White
    Write-Host "   Nombre comercial: $($testResponse.branding.nombre_comercial)" -ForegroundColor White
} catch {
    Write-Host "   ERROR: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  COMPLETADO" -ForegroundColor Cyan
Write-Host "  Prueba ahora en: www.masasestacion.cl" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""
