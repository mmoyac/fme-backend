-- Asignar el lote correcto al item_pedido y recrear picking
BEGIN;

-- 1. Asignar el lote FIFO disponible al item_pedido
UPDATE items_pedido
SET lote_id = 37  -- LOTE-MK2JT7E7-6GSH (17.710 kg)
WHERE id = 92;

-- 2. Eliminar el despacho actual
DELETE FROM picking_items WHERE despacho_id IN (
    SELECT d.id FROM despachos d 
    JOIN pedidos p ON d.pedido_id = p.id 
    WHERE p.numero_pedido = 'E-2026-00017'
);

DELETE FROM despachos WHERE pedido_id IN (
    SELECT id FROM pedidos WHERE numero_pedido = 'E-2026-00017'
);

-- 3. Volver el pedido a CONFIRMADO para poder reasignar despacho
UPDATE pedidos 
SET estado_id = (SELECT id FROM estados_pedido WHERE codigo = 'CONFIRMADO')
WHERE numero_pedido = 'E-2026-00017';

COMMIT;

SELECT 'Item actualizado con lote, despacho eliminado, pedido en CONFIRMADO' as resultado;
