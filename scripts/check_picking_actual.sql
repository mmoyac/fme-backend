-- Verificar el picking item actual
SELECT 
    pi.id,
    pi.peso_solicitado,
    pi.lote_codigo,
    ip.lote_id,
    l.peso_actual,
    l.codigo_lote,
    p.numero_pedido
FROM picking_items pi
JOIN despachos d ON pi.despacho_id = d.id
JOIN items_pedido ip ON pi.item_pedido_id = ip.id
JOIN pedidos p ON d.pedido_id = p.id
LEFT JOIN lotes l ON ip.lote_id = l.id
WHERE p.numero_pedido = 'E-2026-00017';
