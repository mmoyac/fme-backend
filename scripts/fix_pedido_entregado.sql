-- Actualizar el pedido E-2026-00017 a ENTREGADO
UPDATE pedidos 
SET estado_id = (SELECT id FROM estados_pedido WHERE codigo = 'ENTREGADO')
WHERE numero_pedido = 'E-2026-00017';

-- Verificar el cambio
SELECT 
    p.id,
    p.numero_pedido,
    ep.codigo as estado,
    d.estado_despacho,
    d.fecha_entrega
FROM pedidos p
JOIN estados_pedido ep ON p.estado_id = ep.id
LEFT JOIN despachos d ON d.pedido_id = p.id
WHERE p.numero_pedido = 'E-2026-00017';
