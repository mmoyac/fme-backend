-- Verificar el pedido completo
SELECT 
    p.id as pedido_id,
    p.numero_pedido,
    p.tipo_pedido_id,
    tp.codigo as tipo_pedido,
    ip.id as item_id,
    ip.lote_id,
    ip.cantidad,
    prod.nombre as producto
FROM pedidos p
JOIN tipos_pedido tp ON p.tipo_pedido_id = tp.id
JOIN items_pedido ip ON ip.pedido_id = p.id
JOIN productos prod ON ip.producto_id = prod.id
WHERE p.numero_pedido = 'E-2026-00017';

-- Buscar lotes disponibles para Punta Picana
SELECT 
    l.id,
    l.codigo_lote,
    l.peso_actual,
    l.disponible_venta,
    l.vendido,
    p.nombre as producto
FROM lotes l
JOIN productos p ON l.producto_id = p.id
WHERE p.nombre LIKE '%Punta%Picana%'
ORDER BY l.fecha_vencimiento ASC;
