-- Crear configuración de landing para El Olivo (tenant_id = 2)

INSERT INTO configuracion_landing (
    tenant_id,
    logo_url,
    favicon_url,
    nombre_comercial,
    colores,
    hero_titulo,
    hero_subtitulo,
    hero_imagen_url,
    hero_cta_texto,
    hero_cta_link,
    hero_badges,
    beneficios,
    redes_sociales,
    telefono,
    email,
    direccion,
    texto_footer_descripcion,
    texto_copyright,
    meta_title,
    meta_description
) VALUES (
    2,  -- tenant_id = 2 (El Olivo)
    '/logo-elolivo.png',
    '/favicon.ico',
    'El Olivo',
    -- Colores (Verde olivo como color principal)
    '{
        "primario": "#6B8E23",
        "primario_light": "#9ACD32",
        "primario_dark": "#556B2F",
        "secundario": "#8FBC8F",
        "secundario_light": "#90EE90",
        "secundario_dark": "#2E8B57",
        "acento": "#9ACD32",
        "fondo_hero_inicio": "#1C1C1C",
        "fondo_hero_fin": "#2F4F2F",
        "fondo_seccion": "#2F4F2F"
    }'::jsonb,
    'Productos frescos directo del campo',
    'Calidad y frescura en cada producto. Tu tienda de confianza.',
    '/hero-elolivo.jpg',
    'Ver Productos',
    '#productos',
    -- Hero Badges
    '[
        {"icono": "🌿", "texto": "100% Natural"},
        {"icono": "🚚", "texto": "Entrega Rápida"},
        {"icono": "✓", "texto": "Calidad Garantizada"}
    ]'::jsonb,
    -- Beneficios
    '[
        {
            "icono": "🌱",
            "titulo": "Productos Frescos",
            "descripcion": "Productos seleccionados con máxima frescura y calidad"
        },
        {
            "icono": "⚡",
            "titulo": "Entrega Rápida",
            "descripcion": "Recibe tus productos en el menor tiempo posible"
        },
        {
            "icono": "💰",
            "titulo": "Mejores Precios",
            "descripcion": "Precios competitivos sin comprometer la calidad"
        },
        {
            "icono": "🎁",
            "titulo": "Ofertas Exclusivas",
            "descripcion": "Promociones y descuentos para clientes frecuentes"
        }
    ]'::jsonb,
    -- Redes Sociales
    '{
        "facebook": "https://facebook.com/elolivo",
        "instagram": "https://instagram.com/elolivo",
        "whatsapp": "+56912345678"
    }'::jsonb,
    '+56 9 1234 5678',
    'contacto@elolivo.cl',
    'Calle Principal 123, Santiago',
    'El Olivo es tu tienda de confianza para productos frescos y de calidad.',
    '© 2026 El Olivo. Todos los derechos reservados.',
    'El Olivo - Productos Frescos',
    'Encuentra los mejores productos frescos del campo en El Olivo. Calidad garantizada y entrega rápida.'
)
ON CONFLICT (tenant_id) DO UPDATE SET
    logo_url = EXCLUDED.logo_url,
    favicon_url = EXCLUDED.favicon_url,
    nombre_comercial = EXCLUDED.nombre_comercial,
    colores = EXCLUDED.colores,
    hero_titulo = EXCLUDED.hero_titulo,
    hero_subtitulo = EXCLUDED.hero_subtitulo,
    hero_imagen_url = EXCLUDED.hero_imagen_url,
    hero_cta_texto = EXCLUDED.hero_cta_texto,
    hero_cta_link = EXCLUDED.hero_cta_link,
    hero_badges = EXCLUDED.hero_badges,
    beneficios = EXCLUDED.beneficios,
    redes_sociales = EXCLUDED.redes_sociales,
    telefono = EXCLUDED.telefono,
    email = EXCLUDED.email,
    direccion = EXCLUDED.direccion,
    texto_footer_descripcion = EXCLUDED.texto_footer_descripcion,
    texto_copyright = EXCLUDED.texto_copyright,
    meta_title = EXCLUDED.meta_title,
    meta_description = EXCLUDED.meta_description,
    updated_at = now();

SELECT 'Configuración de landing creada/actualizada para El Olivo' as resultado;
