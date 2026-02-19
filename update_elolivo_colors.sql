UPDATE configuracion_landing 
SET colores = '{"primario": "#6B8E23", "secundario": "#8B7355", "acento": "#DAA520", "fondo_hero_inicio": "#2C3E1F", "fondo_hero_fin": "#4A5D3A"}'::json 
WHERE tenant_id = 2;

SELECT tenant_id, colores FROM configuracion_landing WHERE tenant_id = 2;
