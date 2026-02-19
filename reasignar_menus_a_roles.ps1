# ===================================================================
#  REASIGNAR MENUS A ROLES - Post Sincronizacion
# ===================================================================
# Al eliminar los menus, se eliminaron las asignaciones en la tabla
# intermedia role_menu_permissions (CASCADE). Este script recupera
# las asignaciones basandose en los nuevos IDs de menus.
# ===================================================================

$API_BASE = "https://api.masasestacion.cl"
$EMAIL = "admin@fme.cl"
$PASSWORD = "admin"

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  REASIGNACION DE MENUS A ROLES (POST SINCRONIZACION)" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""

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
    Write-Host "   Response: $($_.ErrorDetails.Message)" -ForegroundColor Red
    exit 1
}

# 2. Obtener menus actuales (los nuevos: 32-43)
Write-Host ""
Write-Host "2. Obteniendo menus actuales..." -ForegroundColor Yellow
$menus = Invoke-RestMethod -Uri "$API_BASE/api/admin/menu_items" -Headers $headers
Write-Host "   Total menus: $($menus.Count)" -ForegroundColor Green

# Crear mapa nombre -> id
$menuMap = @{}
foreach ($menu in $menus) {
    $menuMap[$menu.nombre] = $menu.id
    Write-Host "   - $($menu.nombre) (ID: $($menu.id))" -ForegroundColor Gray
}

# 3. Obtener roles
Write-Host ""
Write-Host "3. Obteniendo roles..." -ForegroundColor Yellow
$roles = Invoke-RestMethod -Uri "$API_BASE/api/admin/roles" -Headers $headers
Write-Host "   Total roles: $($roles.Count)" -ForegroundColor Green

# Crear mapa nombre -> id
$roleMap = @{}
foreach ($role in $roles) {
    $roleMap[$role.nombre] = $role.id
    Write-Host "   - $($role.nombre) (ID: $($role.id))" -ForegroundColor Gray
}

# 4. Configuracion de permisos (basado en sistema original)
$rolesConfig = @{
    "admin" = @("Dashboard", "Pedidos", "Productos", "Compras", "Inventario", "Precios", "Clientes", "Alertas", "Despacho", "Recepcion de Mercancias", "Produccion", "Mantenedores")
    "administrador" = @("Dashboard", "Pedidos", "Productos", "Compras", "Inventario", "Precios", "Clientes", "Alertas", "Despacho", "Recepcion de Mercancias", "Produccion", "Mantenedores")
    "vendedor" = @("Dashboard", "Pedidos", "Productos", "Inventario", "Clientes", "Despacho")
    "tesorero" = @("Dashboard", "Pedidos", "Precios", "Clientes")
    "bodeguero" = @("Dashboard", "Inventario", "Recepcion de Mercancias", "Productos")
    "despachador" = @("Dashboard", "Despacho", "Pedidos")
}

# 5. Asignar menus a roles
Write-Host ""
Write-Host "4. Asignando menus a roles..." -ForegroundColor Yellow

$exitosos = 0
$errores = 0

foreach ($roleName in $rolesConfig.Keys) {
    if (-not $roleMap.ContainsKey($roleName)) {
        Write-Host "   Rol no encontrado: $roleName" -ForegroundColor Yellow
        continue
    }

    $roleId = $roleMap[$roleName]
    $menuNames = $rolesConfig[$roleName]
    
    # Convertir nombres de menus a IDs
    $menuIds = @()
    foreach ($menuName in $menuNames) {
        if ($menuMap.ContainsKey($menuName)) {
            $menuIds += $menuMap[$menuName]
        } else {
            Write-Host "   Menu no encontrado: $menuName" -ForegroundColor Yellow
        }
    }

    # Actualizar permisos del rol
    try {
        $body = $menuIds | ConvertTo-Json
        
        $response = Invoke-RestMethod `
            -Uri "$API_BASE/api/admin/roles/$roleId/menu" `
            -Method Put `
            -Body $body `
            -Headers $headers
        
        Write-Host "   $roleName`: Asignados $($menuIds.Count) menus" -ForegroundColor Green
        $exitosos++
    } catch {
        Write-Host "   ERROR en $roleName`: $($_.Exception.Message)" -ForegroundColor Red
        $errores++
    }
}

# 6. Verificacion final
Write-Host ""
Write-Host "5. Verificando resultado..." -ForegroundColor Yellow

foreach ($roleName in $rolesConfig.Keys) {
    if (-not $roleMap.ContainsKey($roleName)) {
        continue
    }
    
    $roleId = $roleMap[$roleName]
    
    try {
        $menusAsignados = Invoke-RestMethod `
            -Uri "$API_BASE/api/admin/roles/$roleId/menu" `
            -Headers $headers
        
        Write-Host "   $roleName`: $($menusAsignados.Count) menus" -ForegroundColor Cyan
    } catch {
        Write-Host "   ERROR verificando $roleName" -ForegroundColor Red
    }
}

# Resumen final
Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  REASIGNACION COMPLETADA" -ForegroundColor Cyan
Write-Host "  Exitosos: $exitosos | Errores: $errores" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""
