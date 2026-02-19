# Script PowerShell para sincronizar menús RBAC de Desarrollo a Producción
# Usa solo APIs REST

Write-Host "`n==================================================================="
Write-Host "  SINCRONIZACION DE MENUS RBAC: DESARROLLO -> PRODUCCION"
Write-Host "==================================================================="

# Menús de desarrollo (fuente de verdad)
$MENUS_DEV = @(
    @{nombre="Dashboard"; href="/admin/dashboard"; icon="HomeIcon"; orden=1},
    @{nombre="Pedidos"; href="/admin/pedidos"; icon="ShoppingCartIcon"; orden=2},
    @{nombre="Productos"; href="/admin/productos"; icon="CubeIcon"; orden=3},
    @{nombre="Compras"; href="/admin/compras"; icon="ShoppingBagIcon"; orden=4},
    @{nombre="Inventario"; href="/admin/inventario"; icon="ArchiveBoxIcon"; orden=5},
    @{nombre="Precios"; href="/admin/precios"; icon="CurrencyDollarIcon"; orden=6},
    @{nombre="Clientes"; href="/admin/clientes"; icon="UsersIcon"; orden=7},
    @{nombre="Alertas"; href="/admin/alertas"; icon="BellIcon"; orden=12},
    @{nombre="Despacho"; href="/admin/despacho"; icon="TruckIcon"; orden=13},
    @{nombre="Recepcion de Mercancias"; href="/admin/recepcion"; icon="InboxIcon"; orden=15},
    @{nombre="Produccion"; href="/admin/produccion"; icon="CogIcon"; orden=50},
    @{nombre="Mantenedores"; href="/admin/mantenedores"; icon="WrenchIcon"; orden=100}
)

# 1. Login en producción
Write-Host "`n1. Autenticando en produccion..." -ForegroundColor Yellow
$body = "username=admin@fme.cl&password=admin"
$loginResp = Invoke-RestMethod -Uri "https://api.masasestacion.cl/api/auth/token" -Method Post -Body $body -ContentType "application/x-www-form-urlencoded"
$token = $loginResp.access_token
$headers = @{"Authorization" = "Bearer $token"}
Write-Host "   Token obtenido" -ForegroundColor Green

# 2. Obtener menús actuales en producción
Write-Host "`n2. Obteniendo menus actuales en produccion..." -ForegroundColor Yellow
$menusActuales = Invoke-RestMethod -Uri "https://api.masasestacion.cl/api/admin/menu_items" -Headers $headers
Write-Host "   Total actual: $($menusActuales.Count) items" -ForegroundColor Cyan

# 3. Eliminar todos los menús existentes
Write-Host "`n3. Eliminando menus existentes..." -ForegroundColor Yellow
$eliminados = 0
$errores = 0
foreach ($menu in $menusActuales) {
    try {
        Invoke-RestMethod -Uri "https://api.masasestacion.cl/api/admin/menu_items/$($menu.id)" -Method Delete -Headers $headers | Out-Null
        Write-Host "   Eliminado: $($menu.nombre) (ID: $($menu.id))" -ForegroundColor Gray
        $eliminados++
    } catch {
        Write-Host "   Error eliminando $($menu.nombre): $_" -ForegroundColor Red
        $errores++
    }
}
Write-Host "   Eliminados: $eliminados | Errores: $errores" -ForegroundColor Green

# 4. Crear menús de desarrollo en producción
Write-Host "`n4. Creando menus de desarrollo en produccion..." -ForegroundColor Yellow
$creados = 0
$errores_crear = 0
foreach ($menu in $MENUS_DEV) {
    $body = $menu | ConvertTo-Json
    try {
        $result = Invoke-RestMethod -Uri "https://api.masasestacion.cl/api/admin/menu_items" -Method Post -Headers $headers -Body $body -ContentType "application/json"
        Write-Host "   Creado: $($menu.nombre) (orden: $($menu.orden))" -ForegroundColor Green
        $creados++
    } catch {
        Write-Host "   Error creando $($menu.nombre): $_" -ForegroundColor Red
        $errores_crear++
    }
}
Write-Host "   Creados: $creados | Errores: $errores_crear" -ForegroundColor Green

# 5. Verificar resultado final
Write-Host "`n5. Verificando resultado final..." -ForegroundColor Yellow
$menusFinal = Invoke-RestMethod -Uri "https://api.masasestacion.cl/api/admin/menu_items" -Headers $headers
Write-Host "`n   MENUS EN PRODUCCION (DESPUES DE SINCRONIZAR):" -ForegroundColor Magenta
Write-Host "   Total: $($menusFinal.Count) items`n" -ForegroundColor Cyan
$menusFinal | Select-Object id, nombre, href, orden | Sort-Object orden | Format-Table -AutoSize

Write-Host "`n==================================================================="
if ($menusFinal.Count -eq 12 -and $errores -eq 0 -and $errores_crear -eq 0) {
    Write-Host "  SINCRONIZACION COMPLETADA EXITOSAMENTE" -ForegroundColor Green
} else {
    Write-Host "  SINCRONIZACION CON ADVERTENCIAS - Revisar resultados" -ForegroundColor Yellow
}
Write-Host "==================================================================="
