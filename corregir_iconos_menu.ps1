# ===================================================================
#  CORREGIR ICONOS DE MENU (Convertir nombres a emojis)
# ===================================================================

$API_BASE = "https://api.masasestacion.cl"
$EMAIL = "admin@fme.cl"
$PASSWORD = "admin"

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  CORRECCION DE ICONOS DE MENU (Nombres -> Emojis)" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""

# Mapeo de nombres de componentes a emojis
$iconMap = @{
    "HomeIcon" = "📊"
    "ShoppingCartIcon" = "🛒"
    "CubeIcon" = "📦"
    "ShoppingBagIcon" = "🛍️"
    "ArchiveBoxIcon" = "📈"
    "CurrencyDollarIcon" = "💰"
    "UsersIcon" = "👥"
    "BellIcon" = "🔔"
    "TruckIcon" = "🚛"
    "InboxIcon" = "📥"
    "CogIcon" = "⚙️"
    "WrenchIcon" = "🔧"
}

# 1. Autenticacion
Write-Host "1. Autenticando en produccion..." -ForegroundColor Yellow
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
    Write-Host "   Mensaje: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 2. Obtener menus actuales
Write-Host ""
Write-Host "2. Obteniendo menus actuales..." -ForegroundColor Yellow
$menus = Invoke-RestMethod -Uri "$API_BASE/api/admin/menu_items" -Headers $headers
Write-Host "   Total menus: $($menus.Count)" -ForegroundColor Green

# 3. Actualizar iconos
Write-Host ""
Write-Host "3. Actualizando iconos..." -ForegroundColor Yellow

$actualizados = 0
$sinCambios = 0
$errores = 0

foreach ($menu in $menus) {
    $iconActual = $menu.icon
    
    # Si el icono está en el mapa, necesita actualización
    if ($iconMap.ContainsKey($iconActual)) {
        $nuevoIcono = $iconMap[$iconActual]
        
        Write-Host "   $($menu.nombre): $iconActual -> $nuevoIcono" -ForegroundColor Yellow
        
        try {
            $updateBody = @{
                nombre = $menu.nombre
                href = $menu.href
                icon = $nuevoIcono
                orden = $menu.orden
            } | ConvertTo-Json
            
            $response = Invoke-RestMethod `
                -Uri "$API_BASE/api/admin/menu_items/$($menu.id)" `
                -Method Put `
                -Body $updateBody `
                -Headers $headers
            
            Write-Host "      Actualizado" -ForegroundColor Green
            $actualizados++
        } catch {
            Write-Host "      ERROR: $($_.Exception.Message)" -ForegroundColor Red
            $errores++
        }
    }
    # Si ya es un emoji (1-2 caracteres), está bien
    elseif ($iconActual.Length -le 2) {
        Write-Host "   $($menu.nombre): $iconActual (OK)" -ForegroundColor Gray
        $sinCambios++
    }
    # Si es otro texto largo, advertir
    else {
        Write-Host "   $($menu.nombre): $iconActual (sin mapeo definido)" -ForegroundColor Yellow
        $sinCambios++
    }
}

# 4. Verificacion final
Write-Host ""
Write-Host "4. Verificando resultado..." -ForegroundColor Yellow

$menusFinales = Invoke-RestMethod -Uri "$API_BASE/api/admin/menu_items" -Headers $headers | Sort-Object -Property orden

Write-Host ""
Write-Host "   nombre                     icono  href" -ForegroundColor Cyan
Write-Host "   ------                     -----  ----" -ForegroundColor Cyan

foreach ($menu in $menusFinales) {
    Write-Host ("   {0,-26} {1,-6} {2}" -f $menu.nombre, $menu.icon, $menu.href) -ForegroundColor White
}

# Resumen final
Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  CORRECCION COMPLETADA" -ForegroundColor Cyan
Write-Host "  Actualizados: $actualizados | Sin cambios: $sinCambios | Errores: $errores" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""
