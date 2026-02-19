-- Eliminar despacho del pedido E-2026-00017
BEGIN;

-- Obtener el ID del despacho
DO $$
DECLARE
    v_despacho_id INTEGER;
    v_pedido_id INTEGER;
BEGIN
    -- Encontrar el pedido
    SELECT id INTO v_pedido_id FROM pedidos WHERE numero_pedido = 'E-2026-00017';
    
    IF v_pedido_id IS NULL THEN
        RAISE NOTICE 'Pedido E-2026-00017 no encontrado';
        RETURN;
    END IF;
    
    -- Encontrar el despacho
    SELECT id INTO v_despacho_id FROM despachos WHERE pedido_id = v_pedido_id;
    
    IF v_despacho_id IS NULL THEN
        RAISE NOTICE 'No hay despacho para este pedido';
        RETURN;
    END IF;
    
    -- Eliminar picking items
    DELETE FROM picking_items WHERE despacho_id = v_despacho_id;
    RAISE NOTICE 'Picking items eliminados';
    
    -- Eliminar despacho
    DELETE FROM despachos WHERE id = v_despacho_id;
    RAISE NOTICE 'Despacho eliminado: ID=%', v_despacho_id;
    
    -- Volver el pedido a CONFIRMADO
    UPDATE pedidos 
    SET estado_id = (SELECT id FROM estados_pedido WHERE codigo = 'CONFIRMADO')
    WHERE id = v_pedido_id;
    RAISE NOTICE 'Pedido vuelto a estado CONFIRMADO';
END$$;

COMMIT;
