-- Obtener el QR del lote LOTE-MK2JT7E7-6GSH para testing
SELECT 
    l.id,
    l.codigo_lote,
    l.qr_propio,
    l.peso_actual,
    l.fecha_vencimiento,
    l.disponible_venta,
    l.vendido,
    p.nombre as producto
FROM lotes l
JOIN productos p ON l.producto_id = p.id
WHERE l.codigo_lote = 'LOTE-MK2JT7E7-6GSH';
