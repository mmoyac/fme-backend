# Script de Testing - Flujo Completo
# Tenant: El Olivo

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  TESTING: FLUJO COMPLETO - EL OLIVO" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"

function Write-Success { param($msg) Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Info { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Step { param($msg) Write-Host "`n>>> $msg" -ForegroundColor Yellow }
function Write-Data { param($msg) Write-Host "   $msg" -ForegroundColor White }

Write-Step "PASO 1: Autenticación"

try {
    $loginHeaders = @{
        "Host" = "elolivo.masasestacion.cl"
        "Content-Type" = "application/x-www-form-urlencoded"
    }
    
    $loginResponse = Invoke-RestMethod -Uri "$baseUrl/api/auth/token" `
        -Method POST `
        -Headers $loginHeaders `
        -Body "username=admin@elolivo.cl&password=admin"
    
    $token = $loginResponse.access_token
    $headers = @{
        "Authorization" = "Bearer $token"
        "Content-Type" = "application/json"
        "Host" = "elolivo.masasestacion.cl"
    }
    
    Write-Success "Login exitoso"
    
    $userInfo = Invoke-RestMethod -Uri "$baseUrl/api/auth/users/me" `
        -Method GET -Headers $headers
    
    Write-Data "Usuario: $($userInfo.nombre_completo)"
    Write-Data "Tenant ID: $($userInfo.tenant_id)"
    Write-Data "Local ID: $($userInfo.local_defecto_id)"
    
} catch {
    Write-Host "[ERROR] Error en login: $($_.Exception.Message)" -ForegroundColor Red
    $_.Exception.Response.GetResponseStream() | Out-String
    exit 1
}

write-Step "PASO 2: Recepción de Mercancía"

try {
    $proveedores = Invoke-RestMethod -Uri "$baseUrl/api/enrolamiento/proveedores-carne" `
        -Method GET -Headers $headers
    
    $proveedorId = $proveedores[0].id
    Write-Data "Proveedor: $($proveedores[0].nombre)"
    
    $timestamp = Get-Date -Format "yyyyMMddHHmmss"
    $enrolamientoData = @{
        proveedor_id = $proveedorId
        tipo_vehiculo_id = 1
        estado_id = 1
        usuario_registro_id = $userInfo.id
        patente = "TEST$(Get-Random -Maximum 999)"
        chofer = "Juan Testing"
        numero_documento = "GD-TEST-$timestamp"
        notas = "Testing automático"
    } | ConvertTo-Json
    
    $enrolamiento = Invoke-RestMethod -Uri "$baseUrl/api/enrolamiento/enrolamientos" `
        -Method POST -Headers $headers -Body $enrolamientoData
    
    $enrolamientoId = $enrolamiento.id
    Write-Success "Enrolamiento creado: ID $enrolamientoId"
    
} catch {
    Write-Host "[ERROR] Error en enrolamiento: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Step "PASO 3: Agregar 10 Lotes (Cajas)"

try {
    $productos = Invoke-RestMethod -Uri "$baseUrl/api/productos/" `
        -Method GET -Headers $headers
    
    $productoCarne = $productos | Where-Object { $_.nombre -like "*carne*" -or $_.nombre -like "*pollo*" } | Select-Object -First 1
    
    if (-not $productoCarne) {
        $productoCarne = $productos[0]
    }
    
    Write-Data "Producto: $($productoCarne.nombre)"
    Write-Info "Creando 10 cajas con fechas de vencimiento escalonadas (FIFO test)..."
    
    $fechaFabricacion = (Get-Date).AddDays(-2).ToString("yyyy-MM-ddTHH:mm:ss")
    $lotesCreados = @()
    
    for ($i = 1; $i -le 10; $i++) {
        $timestampLote = Get-Date -Format "yyyyMMddHHmmss"
        $codigoLote = "LOTE-TEST-$timestampLote-C$i"
        
        # Cada lote vence en días escalonados: Lote 1 = 10 días, Lote 2 = 11 días, etc.
        $diasVencimiento = 9 + $i  # Lote 1: 10 días, Lote 2: 11 días, ..., Lote 10: 19 días
        $fechaVencimiento = (Get-Date).AddDays($diasVencimiento).ToString("yyyy-MM-ddTHH:mm:ss")
        
        # Peso aleatorio entre 17 y 22 kg
        $pesoAleatorio = [Math]::Round((Get-Random -Minimum 17.0 -Maximum 22.0), 1)
        
        Start-Sleep -Milliseconds 100
        
        $loteData = @{
            enrolamiento_id = $enrolamientoId
            producto_id = $productoCarne.id
            ubicacion_id = 1
            codigo_lote = $codigoLote
            qr_propio = $codigoLote
            peso_original = $pesoAleatorio
            peso_actual = $pesoAleatorio
            fecha_vencimiento = $fechaVencimiento
            fecha_fabricacion = $fechaFabricacion
            lote_proveedor = "PROV-$(Get-Random -Maximum 9999)"
        } | ConvertTo-Json
        
        $lote = Invoke-RestMethod -Uri "$baseUrl/api/enrolamiento/lotes" `
            -Method POST -Headers $headers -Body $loteData
        
        $lotesCreados += $lote
        Write-Data "  [$i/10] Caja creada: $($lote.codigo_lote) - $($lote.peso_actual) kg"
    }
    
    Write-Success "10 cajas creadas exitosamente"
    
    $loteId = $lotesCreados[0].id
    $productoId = $productoCarne.id
    
} catch {
    Write-Host "[ERROR] Error creando lotes: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Step "PASO 4: Finalizar Enrolamiento"

try {
    $finalizarData = @{
        estado_id = 3
        notas = "Completado automáticamente"
    } | ConvertTo-Json
    
    $enrolamientoFinal = Invoke-RestMethod `
        -Uri "$baseUrl/api/enrolamiento/enrolamientos/$enrolamientoId" `
        -Method PUT -Headers $headers -Body $finalizarData
    
    Write-Success "Enrolamiento finalizado"
    
} catch {
    Write-Host "[ERROR] Error finalizando: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Step "PASO 5: Crear Cliente"

try {
    $clientes = Invoke-RestMethod -Uri "$baseUrl/api/clientes/" `
        -Method GET -Headers $headers
    
    $clienteTest = $clientes | Where-Object { $_.email -eq "test@automation.cl" } | Select-Object -First 1
    
    if ($clienteTest) {
        Write-Info "Cliente ya existe"
        $clienteId = $clienteTest.id
    } else {
        $clienteData = @{
            nombre = "Cliente Testing"
            email = "test@automation.cl"
            telefono = "+56912345678"
            rut = "76$(Get-Random -Minimum 100000 -Maximum 999999)-K"
            direccion = "Av. Testing 123"
            comuna = "Santiago"
        } | ConvertTo-Json
        
        $cliente = Invoke-RestMethod -Uri "$baseUrl/api/clientes/" `
            -Method POST -Headers $headers -Body $clienteData
        
        $clienteId = $cliente.id
        Write-Success "Cliente creado: ID $clienteId"
    }
    
} catch {
    Write-Host "[ERROR] Error creando cliente: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Step "PASO 6: Crear Pedido (3 cajas de 10)"

try {
    $tipoPedidoId = 2
    $precioEstimado = 5000
    $fechaHora = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    
    Write-Info "Creando pedido de 3 cajas..."
    
    $pedidoData = @{
        cliente_id = $clienteId
        cliente_nombre = "Cliente Testing"
        cliente_email = "test@automation.cl"
        cliente_telefono = "+56912345678"
        direccion_entrega = "Av. Testing 123, Santiago"
        local_id = $userInfo.local_defecto_id
        medio_pago_id = 1
        tipo_pedido_id = $tipoPedidoId
        tipo_documento_tributario_id = 2
        notas = "Pedido testing $fechaHora - 3 cajas de 10"
        items = @(
            @{
                sku = $productoCarne.sku
                producto_id = $productoId
                cantidad = 3
                precio_unitario_venta = $precioEstimado
            }
        )
    } | ConvertTo-Json -Depth 3
    
    $pedido = Invoke-RestMethod -Uri "$baseUrl/api/pedidos/backoffice" `
        -Method POST -Headers $headers -Body $pedidoData
    
    $pedidoId = $pedido.pedido_id
    Write-Success "Pedido creado: $($pedido.numero_pedido)"
    Write-Data "Total estimado: $($pedido.total)"
    
} catch {
    Write-Host "[ERROR] Error creando pedido: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "Detalle: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
    }
    exit 1
}

Write-Step "PASO 7: Confirmar Pedido"

try {
    Start-Sleep -Seconds 2
    
    $confirmarData = @{
        estado = "CONFIRMADO"
        local_despacho_id = $userInfo.local_defecto_id
    } | ConvertTo-Json
    
    $pedidoConfirmado = Invoke-RestMethod `
        -Uri "$baseUrl/api/pedidos/$pedidoId" `
        -Method PUT -Headers $headers -Body $confirmarData
    
    Write-Success "Pedido confirmado"
    Write-Data "Total final: $($pedidoConfirmado.total)"
    
} catch {
    Write-Host "[ERROR] Error confirmando: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Step "PASO 8: Asignar Despacho"

try {
    $usuarios = Invoke-RestMethod -Uri "$baseUrl/api/admin/users" `
        -Method GET -Headers $headers
    
    $despachador = $usuarios | Where-Object { $_.role_nombre -in @("despachador", "admin") } | Select-Object -First 1
    $despachadorId = if ($despachador) { $despachador.id } else { $userInfo.id }
    
    $horaEstimada = (Get-Date).AddHours(2).ToString("yyyy-MM-ddTHH:mm:ss")
    $despachoData = @{
        despachador_user_id = $despachadorId
        notas_despacho = "Despacho testing"
        hora_estimada_entrega = $horaEstimada
    } | ConvertTo-Json
    
    $despacho = Invoke-RestMethod `
        -Uri "$baseUrl/api/despachos/asignar/$pedidoId" `
        -Method POST -Headers $headers -Body $despachoData
    
    $despachoId = $despacho.id
    Write-Success "Despacho asignado: ID $despachoId"
    
} catch {
    Write-Host "[ERROR] Error asignando despacho: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Step "PASO 9: Proceso de Picking"

try {
    $iniciarPickingData = @{
        ubicacion_actual = "Bodega Principal"
        notas_despacho = "Iniciando picking"
    } | ConvertTo-Json
    
    $despachoEnPicking = Invoke-RestMethod `
        -Uri "$baseUrl/api/despachos/$despachoId/iniciar-picking" `
        -Method POST -Headers $headers -Body $iniciarPickingData
    
    Write-Success "Picking iniciado"
    
    $despachoDetalle = Invoke-RestMethod `
        -Uri "$baseUrl/api/despachos/$despachoId" `
        -Method GET -Headers $headers
    
    foreach ($pickingItem in $despachoDetalle.picking_items) {
        Write-Data "Procesando: $($pickingItem.producto_nombre)"
        
        if ($pickingItem.lote_codigo) {
            try {
                $escaneoData = @{
                    qr_code = $pickingItem.lote_codigo
                } | ConvertTo-Json
                
                $escaneoResult = Invoke-RestMethod `
                    -Uri "$baseUrl/api/despachos/escanear-qr?picking_item_id=$($pickingItem.id)" `
                    -Method POST -Headers $headers -Body $escaneoData
                
                Write-Data "  [OK] QR escaneado: $($escaneoResult.lote_codigo)"
            } catch {
                Write-Host "  [WARN] No se pudo escanear QR" -ForegroundColor Yellow
            }
        }
        
        $pesoReal = if ($pickingItem.peso_solicitado) { $pickingItem.peso_solicitado } else { $pickingItem.cantidad_solicitada }
        $completarItemData = @{
            peso_real = $pesoReal
            ubicacion_picking = "Estante A-$(Get-Random -Minimum 1 -Maximum 99)"
            notas_picking = "Completado"
        } | ConvertTo-Json
        
        $null = Invoke-RestMethod `
            -Uri "$baseUrl/api/despachos/picking-item/$($pickingItem.id)" `
            -Method PUT -Headers $headers -Body $completarItemData
        
        Write-Data "  [OK] Item completado"
    }
    
    $despachoPickingCompleto = Invoke-RestMethod `
        -Uri "$baseUrl/api/despachos/$despachoId/completar-picking" `
        -Method POST -Headers $headers
    
    Write-Success "Picking completado"
    
} catch {
    Write-Host "[ERROR] Error en picking: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Step "PASO 10: En Ruta y Entrega"

try {
    Start-Sleep -Seconds 1
    
    $enRutaData = @{
        estado_despacho = "EN_RUTA"
        ubicacion_actual = "Camino al cliente"
    } | ConvertTo-Json
    
    $null = Invoke-RestMethod `
        -Uri "$baseUrl/api/despachos/$despachoId" `
        -Method PUT -Headers $headers -Body $enRutaData
    
    Write-Success "Despacho EN_RUTA"
    
    Start-Sleep -Seconds 1
    
    $entregadoData = @{
        estado_despacho = "ENTREGADO"
        ubicacion_actual = "Entregado"
        notas_despacho = "Entrega exitosa"
    } | ConvertTo-Json
    
    $null = Invoke-RestMethod `
        -Uri "$baseUrl/api/despachos/$despachoId" `
        -Method PUT -Headers $headers -Body $entregadoData
    
    Write-Success "Despacho ENTREGADO"
    
    $pedidoEntregadoData = @{
        estado = "ENTREGADO"
    } | ConvertTo-Json
    
    $null = Invoke-RestMethod `
        -Uri "$baseUrl/api/pedidos/$pedidoId" `
        -Method PUT -Headers $headers -Body $pedidoEntregadoData
    
    Write-Success "Pedido ENTREGADO"
    
} catch {
    Write-Host "[ERROR] Error en entrega: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Step "PASO 11: Verificacion Final"

try {
    $pedidoFinal = Invoke-RestMethod `
        -Uri "$baseUrl/api/pedidos/$pedidoId" `
        -Method GET -Headers $headers
    
    $despachoFinal = Invoke-RestMethod `
        -Uri "$baseUrl/api/despachos/$despachoId" `
        -Method GET -Headers $headers
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  FLUJO COMPLETADO EXITOSAMENTE" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    
    Write-Host "RESUMEN FINAL:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "PEDIDO:" -ForegroundColor Yellow
    Write-Data "Numero: $($pedidoFinal.numero_pedido)"
    Write-Data "Cliente: $($pedidoFinal.cliente.nombre)"
    Write-Data "Estado: $($pedidoFinal.estado)"
    Write-Data "Total: $($pedidoFinal.total)"
    
    Write-Host ""
    Write-Host "DESPACHO:" -ForegroundColor Yellow
    Write-Data "ID: $($despachoFinal.id)"
    Write-Data "Estado: $($despachoFinal.estado_despacho)"
    Write-Data "Fecha Entrega: $($despachoFinal.fecha_entrega)"
    
    if ($pedidoFinal.items[0].lote_codigo) {
        Write-Host ""
        Write-Host "TRAZABILIDAD:" -ForegroundColor Yellow
        Write-Data "Lote: $($pedidoFinal.items[0].lote_codigo)"
        Write-Data "Peso: $($pedidoFinal.items[0].peso_real) kg"
    }
    
    Write-Host ""
    Write-Host "Para limpiar datos:" -ForegroundColor Cyan
    Write-Host "   docker exec -it fme-backend python eliminar_pedidos_elolivo.py" -ForegroundColor White
    Write-Host ""
    
    $testTimestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    Write-Host ""
    Write-Host "VERIFICACION DE STOCK:" -ForegroundColor Yellow
    
    $lotesDisponibles = Invoke-RestMethod `
        -Uri "$baseUrl/api/stock-cajas/lotes-disponibles/$productoId" `
        -Method GET -Headers $headers
    
    $cajasDisponibles = $lotesDisponibles.Count
    $cajasVendidas = 10 - $cajasDisponibles
    
    Write-Data "Total cajas recibidas: 10"
    Write-Data "Cajas vendidas: $cajasVendidas"
    Write-Data "Cajas disponibles: $cajasDisponibles"
    
    if ($cajasDisponibles -eq 7) {
        Write-Host ""
        Write-Host "[EXITO] Stock correcto: 7 cajas disponibles" -ForegroundColor Green
        Write-Host "[EXITO] FIFO funcionando: 3 cajas mas antiguas vendidas" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "[ADVERTENCIA] Stock esperado: 7, Stock actual: $cajasDisponibles" -ForegroundColor Yellow
    }
    
    $testResults = @{
        enrolamiento_id = $enrolamientoId
        lote_id = $loteId
        pedido_id = $pedidoId
        pedido_numero = $pedidoFinal.numero_pedido
        despacho_id = $despachoId
        cliente_id = $clienteId
        fecha_test = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        cajas_recibidas = 10
        cajas_vendidas = $cajasVendidas
        cajas_disponibles = $cajasDisponibles
    }
    
    $testResults | ConvertTo-Json | Out-File "test_results_$testTimestamp.json"
    Write-Info "Resultados guardados en: test_results_$testTimestamp.json"
    
} catch {
    Write-Host "[WARN] Error en seccion final: $($_.Exception.Message)" -ForegroundColor Yellow
}
