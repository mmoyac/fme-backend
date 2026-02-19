-- Verificar pedido E-2026-00017
SELECT 
    p.id as pedido_id,
    p.numero_pedido,
    tp.codigo as tipo_pedido,
    d.id as despacho_id,
    d.estado_despacho
FROM pedidos p
LEFT JOIN tipos_pedido tp ON p.tipo_pedido_id = tp.id
LEFT JOIN despachos d ON d.pedido_id = p.id
WHERE p.numero_pedido = 'E-2026-00017';

-- Verificar items del pedido
SELECT 
    ip.id as item_id,
    ip.pedido_id,
    prod.nombre as producto,
    ip.cantidad,
    ip.lote_id,
    l.codigo_lote,
    l.peso_actual
FROM items_pedido ip
JOIN productos prod ON ip.producto_id = prod.id
LEFT JOIN lotes l ON ip.lote_id = l.id
WHERE ip.pedido_id = (SELECT id FROM pedidos WHERE numero_pedido = 'E-2026-00017');

-- Verificar picking items
SELECT 
    pi.id as picking_id,
    pi.despacho_id,
    pi.item_pedido_id,
    pi.cantidad_solicitada,
    pi.peso_solicitado,
    pi.lote_codigo,
    pi.completado
FROM picking_items pi
WHERE pi.despacho_id = (
    SELECT d.id FROM despachos d 
    JOIN pedidos p ON d.pedido_id = p.id 
    WHERE p.numero_pedido = 'E-2026-00017'
);
