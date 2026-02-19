# 🧪 TESTING: Flujo Completo - Recepción hasta Venta y Entrega

Esta guía documenta el proceso completo de testing desde la recepción de mercancía hasta la venta final, incluyendo el sistema de despachos.

**Tenant de Prueba:** El Olivo (ID: 2)  
**URL Backend:** http://168.231.96.205:8001 (producción) o http://localhost:8000 (desarrollo)  
**URL Backoffice:** http://168.231.96.205:3001 (producción) o http://localhost:3001 (desarrollo)

---

## 📋 Índice del Flujo

1. [Preparación: Login y Token](#1-preparación-login-y-token)
2. [Recepción de Mercancía (Enrolamiento)](#2-recepción-de-mercancía-enrolamiento)
3. [Verificar Stock Disponible](#3-verificar-stock-disponible)
4. [Crear Pedido desde Backoffice](#4-crear-pedido-desde-backoffice)
5. [Confirmar Pedido](#5-confirmar-pedido)
6. [Asignar Despacho](#6-asignar-despacho)
7. [Proceso de Picking](#7-proceso-de-picking)
8. [Completar Despacho y Entrega](#8-completar-despacho-y-entrega)
9. [Verificación Final](#9-verificación-final)

---

## 1. 🔐 Preparación: Login y Token

### 1.1. Usuario de Prueba - El Olivo

```bash
# Usuario Admin de El Olivo
Email: admin@elolivo.cl
Password: admin123
```

### 1.2. Obtener Token (PowerShell)

```powershell
# Login
$loginResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/login" `
    -Method POST `
    -ContentType "application/x-www-form-urlencoded" `
    -Body "username=admin@elolivo.cl&password=admin123"

# Guardar token
$token = $loginResponse.access_token
Write-Host "✅ Token obtenido: $token"

# Headers para requests autenticados
$headers = @{
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json"
}
```

### 1.3. Verificar Usuario y Tenant

```powershell
# Obtener información del usuario actual
$userInfo = Invoke-RestMethod -Uri "http://localhost:8000/api/auth/me" `
    -Method GET -Headers $headers

Write-Host "Usuario: $($userInfo.nombre_completo)"
Write-Host "Tenant: $($userInfo.tenant_id)"
Write-Host "Local Default: $($userInfo.local_defecto_id)"
```

---

## 2. 🚛 Recepción de Mercancía (Enrolamiento)

### 2.1. Listar Proveedores de Carne

```powershell
# Obtener proveedores tipo CARNES
$proveedores = Invoke-RestMethod -Uri "http://localhost:8000/api/enrolamiento/proveedores-carne" `
    -Method GET -Headers $headers

$proveedores | Format-Table id, nombre, rut
```

### 2.2. Crear Enrolamiento de Vehículo

```powershell
# Datos del enrolamiento
$enrolamientoData = @{
    proveedor_id = 1  # ID del proveedor de carne
    patente = "ABCD12"
    chofer_nombre = "Juan Pérez"
    chofer_rut = "12345678-9"
    guia_despacho = "GD-2026-001"
    observaciones = "Testing flujo completo"
} | ConvertTo-Json

# Crear enrolamiento
$enrolamiento = Invoke-RestMethod -Uri "http://localhost:8000/api/enrolamiento/" `
    -Method POST -Headers $headers -Body $enrolamientoData

Write-Host "✅ Enrolamiento creado: ID $($enrolamiento.id)"
$enrolamientoId = $enrolamiento.id
```

### 2.3. Listar Productos Disponibles

```powershell
# Obtener productos del tenant
$productos = Invoke-RestMethod -Uri "http://localhost:8000/api/productos/" `
    -Method GET -Headers $headers

# Filtrar productos tipo CAJAS_VARIABLES (tipo_pedido_id = 2)
$productosCajas = $productos | Where-Object { $_.categoria_id -eq 2 }  # Ajustar según categoría
$productosCajas | Format-Table id, nombre, sku
```

### 2.4. Agregar Lotes al Enrolamiento

```powershell
# Crear lote de caja de carne
$loteData = @{
    enrolamiento_id = $enrolamientoId
    producto_id = 1  # ID del producto de carne (ajustar según tu BD)
    codigo_lote = "LOTE-2026-001"
    peso_kg = 25.5
    fecha_vencimiento = "2026-03-15"
    precio_kg = 8500
    temperatura_recepcion = -2.5
    observaciones = "Caja en buen estado"
} | ConvertTo-Json

$lote = Invoke-RestMethod -Uri "http://localhost:8000/api/enrolamiento/lotes" `
    -Method POST -Headers $headers -Body $loteData

Write-Host "✅ Lote creado: $($lote.codigo_lote) - Peso: $($lote.peso_kg) kg"
```

### 2.5. Generar QR del Lote

```powershell
# Obtener QR del lote para impresión
$qrUrl = "http://localhost:8000/api/enrolamiento/lotes/$($lote.id)/qr"
Write-Host "📱 QR disponible en: $qrUrl"

# Descargar QR
Invoke-WebRequest -Uri $qrUrl -Headers $headers -OutFile "lote_qr_$($lote.codigo_lote).png"
Write-Host "✅ QR descargado: lote_qr_$($lote.codigo_lote).png"
```

### 2.6. Finalizar Enrolamiento

```powershell
# Cambiar estado a COMPLETADO
$finalizarData = @{
    estado = "COMPLETADO"
    observaciones = "Enrolamiento finalizado correctamente"
} | ConvertTo-Json

$enrolamientoFinal = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/enrolamiento/$enrolamientoId" `
    -Method PUT -Headers $headers -Body $finalizarData

Write-Host "✅ Enrolamiento finalizado: Estado $($enrolamientoFinal.estado)"
```

---

## 3. 📦 Verificar Stock Disponible

### 3.1. Ver Lotes Disponibles para Venta

```powershell
# Obtener lotes disponibles para un producto
$productoId = 1  # Ajustar según producto usado
$lotesDisponibles = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/stock-cajas/lotes-disponibles/$productoId" `
    -Method GET -Headers $headers

Write-Host "📊 Lotes disponibles:"
$lotesDisponibles.lotes | Format-Table codigo_lote, peso_kg, precio_kg, fecha_vencimiento
```

### 3.2. Ver Resumen de Stock por Proveedor

```powershell
# Resumen de stock
$resumenStock = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/stock-cajas/resumen" `
    -Method GET -Headers $headers

$resumenStock | Format-Table proveedor_nombre, producto_nombre, cajas_disponibles, peso_total_kg
```

---

## 4. 🛒 Crear Pedido desde Backoffice

### 4.1. Listar Clientes

```powershell
# Obtener clientes del tenant
$clientes = Invoke-RestMethod -Uri "http://localhost:8000/api/clientes/" `
    -Method GET -Headers $headers

$clientes | Format-Table id, nombre, email, telefono
```

### 4.2. Crear Cliente (si no existe)

```powershell
$clienteData = @{
    nombre = "Restaurante Prueba"
    email = "restaurante@test.cl"
    telefono = "+56912345678"
    rut = "76123456-7"
    direccion = "Av. Test 123, Santiago"
    comuna = "Santiago"
} | ConvertTo-Json

$cliente = Invoke-RestMethod -Uri "http://localhost:8000/api/clientes/" `
    -Method POST -Headers $headers -Body $clienteData

Write-Host "✅ Cliente creado: ID $($cliente.id)"
$clienteId = $cliente.id
```

### 4.3. Crear Pedido con Producto de Cajas Variables

```powershell
# Crear pedido backoffice
$pedidoData = @{
    cliente_id = $clienteId
    tipo_pedido_id = 2  # CAJAS_VARIABLES
    medio_pago_id = 1   # Ajustar según medios de pago disponibles
    items = @(
        @{
            producto_id = 1
            cantidad = 1  # 1 caja
            precio_unitario = 217750  # Precio estimado (peso * precio/kg)
        }
    )
    notas = "Pedido de testing - flujo completo"
} | ConvertTo-Json -Depth 3

$pedido = Invoke-RestMethod -Uri "http://localhost:8000/api/pedidos/backoffice" `
    -Method POST -Headers $headers -Body $pedidoData

Write-Host "✅ Pedido creado: $($pedido.numero_pedido) - Total: $($pedido.total)"
$pedidoId = $pedido.pedido_id
```

---

## 5. ✅ Confirmar Pedido

### 5.1. Obtener Estados de Pedido

```powershell
# Ver estados disponibles
$estados = Invoke-RestMethod -Uri "http://localhost:8000/api/pedidos/estados" `
    -Method GET -Headers $headers

$estados | Format-Table codigo, nombre, descripcion
```

### 5.2. Confirmar Pedido (Asigna Lotes FIFO)

```powershell
# Cambiar estado a CONFIRMADO
# Esto descuenta inventario y asigna lotes específicos
$confirmarData = @{
    estado = "CONFIRMADO"
    local_despacho_id = 2  # ID del local físico de El Olivo
} | ConvertTo-Json

$pedidoConfirmado = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/pedidos/$pedidoId" `
    -Method PUT -Headers $headers -Body $confirmarData

Write-Host "✅ Pedido confirmado"
Write-Host "   Estado: $($pedidoConfirmado.estado)"
Write-Host "   Total Final: $($pedidoConfirmado.total)"
Write-Host "   Inventario Descontado: $($pedidoConfirmado.inventario_descontado)"
```

### 5.3. Verificar Lotes Asignados

```powershell
# Obtener detalle del pedido con lotes asignados
$pedidoDetalle = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/pedidos/$pedidoId" `
    -Method GET -Headers $headers

Write-Host "📦 Items del pedido con lotes:"
$pedidoDetalle.items | ForEach-Object {
    Write-Host "   - Producto: $($_.producto_nombre)"
    Write-Host "     Lote: $($_.lote_codigo)"
    Write-Host "     Peso: $($_.peso_real) kg"
    Write-Host "     Precio: $($_.precio_unitario)"
}
```

---

## 6. 🚚 Asignar Despacho

### 6.1. Listar Usuarios Despachadores

```powershell
# Obtener usuarios con rol de despachador
$usuarios = Invoke-RestMethod -Uri "http://localhost:8000/api/admin/users" `
    -Method GET -Headers $headers

$usuarios | Where-Object { $_.role_nombre -eq "despachador" } | Format-Table id, nombre_completo, email
```

### 6.2. Asignar Despacho al Pedido

```powershell
# Asignar despachador
$despachoData = @{
    despachador_user_id = 3  # ID del usuario despachador
    notas_despacho = "Despacho de testing"
    hora_estimada_entrega = "2026-02-18T16:00:00"
} | ConvertTo-Json

$despacho = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/despachos/asignar/$pedidoId" `
    -Method POST -Headers $headers -Body $despachoData

Write-Host "✅ Despacho asignado: ID $($despacho.id)"
Write-Host "   Estado: $($despacho.estado_despacho)"
Write-Host "   Despachador: $($despacho.despachador_nombre)"
$despachoId = $despacho.id
```

### 6.3. Ver Detalles del Despacho

```powershell
# Obtener despacho con picking items
$despachoDetalle = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/despachos/$despachoId" `
    -Method GET -Headers $headers

Write-Host "📋 Picking Items creados:"
$despachoDetalle.picking_items | Format-Table producto_nombre, lote_codigo, peso_solicitado, completado
```

---

## 7. 📱 Proceso de Picking

### 7.1. Iniciar Picking

```powershell
# Cambiar estado a EN_PICKING
$iniciarPickingData = @{
    ubicacion_actual = "Bodega Principal"
    notas_despacho = "Iniciando recolección de productos"
} | ConvertTo-Json

$despachoEnPicking = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/despachos/$despachoId/iniciar-picking" `
    -Method POST -Headers $headers -Body $iniciarPickingData

Write-Host "✅ Picking iniciado: Estado $($despachoEnPicking.estado_despacho)"
```

### 7.2. Escanear QR del Lote

```powershell
# Obtener el ID del picking item
$pickingItemId = $despachoDetalle.picking_items[0].id
$loteCodigoQR = $despachoDetalle.picking_items[0].lote_codigo

# Simular escaneo de QR
$escaneoData = @{
    qr_code = $loteCodigoQR
} | ConvertTo-Json

$escaneoResult = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/despachos/escanear-qr?picking_item_id=$pickingItemId" `
    -Method POST -Headers $headers -Body $escaneoData

Write-Host "✅ QR escaneado correctamente"
Write-Host "   Lote: $($escaneoResult.lote_codigo)"
Write-Host "   Producto: $($escaneoResult.producto_nombre)"
```

### 7.3. Completar Item de Picking

```powershell
# Actualizar picking item con peso real
$completarItemData = @{
    peso_real = 25.5  # Peso real de la caja
    ubicacion_picking = "Estante A-12"
    notas_picking = "Caja en condiciones óptimas"
} | ConvertTo-Json

$pickingItemActualizado = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/despachos/picking-item/$pickingItemId" `
    -Method PUT -Headers $headers -Body $completarItemData

Write-Host "✅ Item de picking completado"
```

### 7.4. Finalizar Picking

```powershell
# Completar todo el proceso de picking
$despachoPickingCompleto = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/despachos/$despachoId/completar-picking" `
    -Method POST -Headers $headers

Write-Host "✅ Picking completado: Estado $($despachoPickingCompleto.estado_despacho)"
```

---

## 8. 🚛 Completar Despacho y Entrega

### 8.1. Cambiar a EN_RUTA

```powershell
# Actualizar estado a EN_RUTA
$enRutaData = @{
    estado_despacho = "EN_RUTA"
    ubicacion_actual = "Camino a dirección del cliente"
} | ConvertTo-Json

$despachoEnRuta = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/despachos/$despachoId" `
    -Method PUT -Headers $headers -Body $enRutaData

Write-Host "✅ Despacho en ruta"
```

### 8.2. Confirmar Entrega

```powershell
# Actualizar estado a ENTREGADO
$entregadoData = @{
    estado_despacho = "ENTREGADO"
    ubicacion_actual = "Entregado en destino"
    notas_despacho = "Entrega exitosa - Cliente conforme"
} | ConvertTo-Json

$despachoEntregado = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/despachos/$despachoId" `
    -Method PUT -Headers $headers -Body $entregadoData

Write-Host "✅ Despacho ENTREGADO"
Write-Host "   Fecha entrega: $($despachoEntregado.fecha_entrega)"
```

### 8.3. Cambiar Pedido a ENTREGADO

```powershell
# Actualizar estado del pedido
$pedidoEntregadoData = @{
    estado = "ENTREGADO"
} | ConvertTo-Json

$pedidoFinal = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/pedidos/$pedidoId" `
    -Method PUT -Headers $headers -Body $pedidoEntregadoData

Write-Host "✅ Pedido ENTREGADO"
```

---

## 9. ✔️ Verificación Final

### 9.1. Ver Estado del Pedido

```powershell
$pedidoFinal = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/pedidos/$pedidoId" `
    -Method GET -Headers $headers

Write-Host "📊 RESUMEN FINAL DEL PEDIDO"
Write-Host "=============================="
Write-Host "Número: $($pedidoFinal.numero_pedido)"
Write-Host "Cliente: $($pedidoFinal.cliente.nombre)"
Write-Host "Estado: $($pedidoFinal.estado)"
Write-Host "Total: $($pedidoFinal.total)"
Write-Host "Inventario Descontado: $($pedidoFinal.inventario_descontado)"
Write-Host "=============================="
```

### 9.2. Ver Estado del Despacho

```powershell
$despachoFinal = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/despachos/$despachoId" `
    -Method GET -Headers $headers

Write-Host "📦 RESUMEN FINAL DEL DESPACHO"
Write-Host "=============================="
Write-Host "ID: $($despachoFinal.id)"
Write-Host "Estado: $($despachoFinal.estado_despacho)"
Write-Host "Despachador: $($despachoFinal.despachador_nombre)"
Write-Host "Fecha Asignación: $($despachoFinal.fecha_asignacion)"
Write-Host "Fecha Inicio Picking: $($despachoFinal.fecha_inicio_picking)"
Write-Host "Fecha Fin Picking: $($despachoFinal.fecha_fin_picking)"
Write-Host "Fecha Inicio Ruta: $($despachoFinal.fecha_inicio_ruta)"
Write-Host "Fecha Entrega: $($despachoFinal.fecha_entrega)"
Write-Host "=============================="
```

### 9.3. Verificar Lotes

```powershell
# Verificar que el lote quedó marcado como vendido
$lotesActualizados = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/stock-cajas/lotes-disponibles/$productoId" `
    -Method GET -Headers $headers

Write-Host "📊 ESTADO DE LOTES"
Write-Host "=============================="
Write-Host "Lotes disponibles: $($lotesActualizados.resumen.total_cajas_disponibles)"
Write-Host "Lotes vendidos: $($lotesActualizados.resumen.total_cajas_vendidas)"
```

### 9.4. Dashboard de Despachos

```powershell
# Ver estadísticas de despachos
$estadisticas = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/despachos/estadisticas" `
    -Method GET -Headers $headers

Write-Host "📈 ESTADÍSTICAS DE DESPACHOS"
Write-Host "=============================="
Write-Host "Total Despachos: $($estadisticas.total_despachos)"
Write-Host "Entregados Hoy: $($estadisticas.entregados_hoy)"
Write-Host "En Proceso: $($estadisticas.en_proceso)"
Write-Host "Tiempo Promedio Picking: $($estadisticas.tiempo_promedio_picking_minutos) min"
```

---

## 🎯 Script Completo de Testing

Para ejecutar todo el flujo de una vez, puedes usar este script PowerShell:

```powershell
# Ver archivo: test_flujo_completo.ps1
```

---

## 🧹 Limpiar Datos de Prueba

Cuando termines el testing, ejecuta:

```powershell
docker exec -it fme-backend python eliminar_pedidos_elolivo.py
```

Este script elimina:
- ✅ Todos los pedidos
- ✅ Items de pedidos
- ✅ Despachos asignados
- ✅ Picking items
- ✅ Restaura lotes a disponible
- ✅ Movimientos de inventario
- ✅ Movimientos de puntos

---

## 📝 Notas Importantes

1. **Orden de Estados:**
   - Pedido: PENDIENTE → CONFIRMADO → EN_PREPARACION → ENTREGADO
   - Despacho: ASIGNADO → EN_PICKING → LISTO_EMPAQUE → EN_RUTA → ENTREGADO

2. **Validaciones Automáticas:**
   - FIFO: Los lotes se asignan por fecha de vencimiento (primero los más próximos)
   - Inventario: Se descuenta automáticamente al confirmar
   - Precios: Se actualizan del estimado al real según lote asignado

3. **QR Codes:**
   - Cada lote tiene un QR único
   - Se puede escanear desde la app móvil de picking
   - Valida que el lote correcto está siendo recogido

4. **Trazabilidad Completa:**
   - Desde el enrolamiento del vehículo hasta la entrega final
   - Timestamps en cada etapa del proceso
   - Auditoría completa de movimientos

---

## 🔗 Referencias

- **API Docs:** http://localhost:8000/docs
- **Backoffice:** http://localhost:3001/admin
- **AGENTS.md Backend:** Para más detalles de la arquitectura
- **AGENTS.md Backoffice:** Para uso de la interfaz web

---

**Última Actualización:** 2026-02-18  
**Versión:** 1.0.0
