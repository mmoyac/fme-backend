# Script PowerShell para sincronizar menús RBAC de Desarrollo a Producción
# Usa solo APIs REST

Write-Host "`n===================================================================" -ForegroundColor Cyan;
Write-Host "  SINCRONIZACIÓN DE MENÚS RBAC: DESARROLLO → PRODUCCIÓN" -ForegroundColor Cyan;
Write-Host "===================================================================" -ForegroundColor Cyan;

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
    @{nombre="Recepción de Mercancías"; href="/admin/recepcion"; icon="InboxIcon"; orden=15},
    @{nombre="Producción"; href="/admin/produccion"; icon="CogIcon"; orden=50},
    @{nombre="Mantenedores"; href="/admin/mantenedores"; icon="WrenchIcon"; orden=100}
);

# 1. Login en producción
Write-Host "`n1️⃣  Autenticando en producción..." -ForegroundColor Yellow;
$body = "username=admin@fme.cl&password=admin";
$loginResp = Invoke-RestMethod -Uri "https://api.masasestacion.cl/api/auth/token" -Method Post -Body $body -ContentType "application/x-www-form-urlencoded";
$token = $loginResp.access_token;
$headers = @{"Authorization" = "Bearer $token"};
Write-Host "   ✓ Token obtenido" -ForegroundColor Green;

# 2. Obtener menús actuales en producción
Write-Host "`n2️⃣  Obteniendo menús actuales en producción..." -ForegroundColor Yellow;
$menusActuales = Invoke-RestMethod -Uri "https://api.masasestacion.cl/api/admin/menu_items" -Headers $headers;
Write-Host "   📊 Total actual: $($menusActuales.Count) items" -ForegroundColor Cyan;

# 3. Eliminar todos los menús existentes
Write-Host "`n3️⃣  Eliminando menús existentes..." -ForegroundColor Yellow;
$eliminados = 0;
$errores = 0;
foreach ($menu in $menusActuales) {
    try {
        Invoke-RestMethod -Uri "https://api.masasestacion.cl/api/admin/menu_items/$($menu.id)" -Method Delete -Headers $headers | Out-Null;
        Write-Host "   🗑️  Eliminado: $($menu.nombre) (ID: $($menu.id))" -ForegroundColor Gray;
        $eliminados++;
    } catch {
        Write-Host "   ❌ Error eliminando $($menu.nombre): $_" -ForegroundColor Red;
        $errores++;
    }
}
$colorElim = if ($errores -eq 0) { "Green" } else { "Yellow" }
Write-Host "   ✓ Eliminados: $eliminados | Errores: $errores" -ForegroundColor $colorElim

# 4. Crear menús de desarrollo en producción
Write-Host "`n4️⃣  Creando menús de desarrollo en producción..." -ForegroundColor Yellow;
$creados = 0;
$errores_crear = 0;
foreach ($menu in $MENUS_DEV) {
    $body = $menu | ConvertTo-Json;
    try {
        $result = Invoke-RestMethod -Uri "https://api.masasestacion.cl/api/admin/menu_items" -Method Post -Headers $headers -Body $body -ContentType "application/json";
        Write-Host "   ✨ Creado: $($menu.nombre) (orden: $($menu.orden))" -ForegroundColor Green;
        $creados++;
    } catch {
        Write-Host "   ❌ Error creando $($menu.nombre): $_" -ForegroundColor Red;
        $errores_crear++;
    }
}
$colorCrear = if ($errores_crear -eq 0) { "Green" } else { "Yellow" }
Write-Host "   ✓ Creados: $creados | Errores: $errores_crear" -ForegroundColor $colorCrear

# 5. Verificar resultado final
Write-Host "`n5️⃣  Verificando resultado final..." -ForegroundColor Yellow;
$menusFinal = Invoke-RestMethod -Uri "https://api.masasestacion.cl/api/admin/menu_items" -Headers $headers;
Write-Host "`n   📊 MENÚS EN PRODUCCIÓN (DESPUÉS DE SINCRONIZAR):" -ForegroundColor Magenta;
$colorFinal = if ($menusFinal.Count -eq 12) { "Green" } else { "Yellow" }
Write-Host "   Total: $($menusFinal.Count) items`n" -ForegroundColor $colorFinal
$menusFinal | Select-Object id, nombre, href, orden | Sort-Object orden | Format-Table -AutoSize;

Write-Host "`n===================================================================" -ForegroundColor Cyan;
if ($menusFinal.Count -eq 12 -and $errores -eq 0 -and $errores_crear -eq 0) {
    Write-Host "  ✅ SINCRONIZACIÓN COMPLETADA EXITOSAMENTE" -ForegroundColor Green;
} else {
    Write-Host "  ⚠️  SINCRONIZACIÓN CON ADVERTENCIAS - Revisar resultados" -ForegroundColor Yellow;
}
Write-Host "===================================================================" -ForegroundColor Cyan;
