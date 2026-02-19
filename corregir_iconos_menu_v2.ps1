# ===================================================================
#  CORREGIR ICONOS DE MENU (Convertir nombres a emojis)
# ===================================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$API_BASE = "https://api.masasestacion.cl"
$EMAIL = "admin@fme.cl"
$PASSWORD = "admin"

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  CORRECCION DE ICONOS DE MENU (Nombres -> Emojis)" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""

# Array de mapeos (usando unicode escapes)
$iconMappings = @(
    @{name="HomeIcon"; emoji=[char]::ConvertFromUtf32(0x1F4CA)},  # 📊
    @{name="ShoppingCartIcon"; emoji=[char]::ConvertFromUtf32(0x1F6D2)},  # 🛒
    @{name="CubeIcon"; emoji=[char]::ConvertFromUtf32(0x1F4E6)},  # 📦
    @{name="ShoppingBagIcon"; emoji=[char]::ConvertFromUtf32(0x1F6CD) + [char]::ConvertFromUtf32(0xFE0F)},  # 🛍️
    @{name="ArchiveBoxIcon"; emoji=[char]::ConvertFromUtf32(0x1F4C8)},  # 📈
    @{name="CurrencyDollarIcon"; emoji=[char]::ConvertFromUtf32(0x1F4B0)},  # 💰
    @{name="UsersIcon"; emoji=[char]::ConvertFromUtf32(0x1F465)},  # 👥
    @{name="BellIcon"; emoji=[char]::ConvertFromUtf32(0x1F514)},  # 🔔
    @{name="TruckIcon"; emoji=[char]::ConvertFromUtf32(0x1F69B)},  # 🚛
    @{name="InboxIcon"; emoji=[char]::ConvertFromUtf32(0x1F4E5)},  # 📥
    @{name="CogIcon"; emoji=[char]::ConvertFromUtf32(0x2699) + [char]::ConvertFromUtf32(0xFE0F)},  # ⚙️
    @{name="WrenchIcon"; emoji=[char]::ConvertFromUtf32(0x1F527)}  # 🔧
)

# Crear HashTable para búsquedas rápidas
$iconMap = @{}
foreach ($mapping in $iconMappings) {
    $iconMap[$mapping.name] = $mapping.emoji
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
        "Content-Type" = "application/json; charset=utf-8"
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
    
    # Si el icono esta en el mapa, necesita actualizacion
    if ($iconMap.ContainsKey($iconActual)) {
        $nuevoIcono = $iconMap[$iconActual]
        
        Write-Host "   $($menu.nombre): $iconActual -> emoji" -ForegroundColor Yellow
        
        try {
            $updateBody = @{
                nombre = $menu.nombre
                href = $menu.href
                icon = $nuevoIcono
                orden = $menu.orden
            } | ConvertTo-Json -Depth 10
            
            $response = Invoke-RestMethod `
                -Uri "$API_BASE/api/admin/menu_items/$($menu.id)" `
                -Method Put `
                -Body ([System.Text.Encoding]::UTF8.GetBytes($updateBody)) `
                -Headers $headers
            
            Write-Host "      Actualizado" -ForegroundColor Green
            $actualizados++
        } catch {
            Write-Host "      ERROR: $($_.Exception.Message)" -ForegroundColor Red
            $errores++
        }
    }
    # Si ya es corto (probablemente emoji), esta bien
    elseif ($iconActual.Length -le 4) {
        Write-Host "   $($menu.nombre): OK" -ForegroundColor Gray
        $sinCambios++
    }
    # Si es otro texto largo, advertir
    else {
        Write-Host "   $($menu.nombre): $iconActual (sin mapeo)" -ForegroundColor Yellow
        $sinCambios++
    }
}

# 4. Verificacion final
Write-Host ""
Write-Host "4. Verificando resultado..." -ForegroundColor Yellow

$menusFinales = Invoke-RestMethod -Uri "$API_BASE/api/admin/menu_items" -Headers $headers | Sort-Object -Property orden

Write-Host ""
Write-Host "   Nombre                     Icono  Orden" -ForegroundColor Cyan
Write-Host "   ------                     -----  -----" -ForegroundColor Cyan

foreach ($menu in $menusFinales) {
    Write-Host ("   {0,-26} {1,-6} {2}" -f $menu.nombre, $menu.icon, $menu.orden) -ForegroundColor White
}

# Resumen final
Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  CORRECCION COMPLETADA" -ForegroundColor Cyan
Write-Host "  Actualizados: $actualizados | Sin cambios: $sinCambios | Errores: $errores" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""
