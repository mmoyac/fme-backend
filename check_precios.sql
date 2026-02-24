-- Verificar precios por local (Tenant 1)
SELECT 
    l.id as local_id,
    l.nombre as local_nombre,
    l.codigo as local_codigo,
    COUNT(p.id) as total_precios
FROM locales l
LEFT JOIN precios p ON l.id = p.local_id
WHERE l.tenant_id = 1
GROUP BY l.id, l.nombre, l.codigo
ORDER BY l.id;

-- Total de productos
SELECT COUNT(*) as total_productos FROM productos WHERE tenant_id = 1;

-- Productos sin precio en ningún local
SELECT 
    COUNT(DISTINCT pr.id) as productos_sin_precio
FROM productos pr
WHERE pr.tenant_id = 1
AND pr.id NOT IN (SELECT DISTINCT producto_id FROM precios p JOIN locales l ON p.local_id = l.id WHERE l.tenant_id = 1);
