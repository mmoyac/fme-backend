-- Eliminar despacho simple
DELETE FROM picking_items WHERE despacho_id IN (
    SELECT d.id FROM despachos d 
    JOIN pedidos p ON d.pedido_id = p.id 
    WHERE p.numero_pedido = 'E-2026-00017'
);

DELETE FROM despachos WHERE pedido_id IN (
    SELECT id FROM pedidos WHERE numero_pedido = 'E-2026-00017'
);

UPDATE pedidos 
SET estado_id = (SELECT id FROM estados_pedido WHERE codigo = 'CONFIRMADO')
WHERE numero_pedido = 'E-2026-00017';

SELECT 'Despacho eliminado y pedido vuelto a CONFIRMADO' as resultado;
