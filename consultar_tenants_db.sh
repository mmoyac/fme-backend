#!/bin/bash

# Script para consultar directamente la tabla tenants en producción

echo "===================================================================="
echo "  CONSULTA DIRECTA A BASE DE DATOS - TABLA TENANTS"
echo "===================================================================="
echo ""

# Ejecutar consulta en el contenedor de PostgreSQL
docker exec -i masas_estacion_db psql -U fme -d fme_database << EOF

\echo '=== TABLA TENANTS ==='
SELECT 
    id,
    codigo,
    nombre,
    dominio_principal,
    subdomain,
    activo,
    created_at
FROM tenants
ORDER BY id;

\echo ''
\echo '=== VERIFICACION DE ENCODING ==='
SELECT 
    id,
    nombre,
    length(dominio_principal) as len_dominio,
    dominio_principal,
    octet_length(dominio_principal) as octets_dominio,
    length(subdomain) as len_subdomain,
    subdomain
FROM tenants
WHERE id = 1;

EOF

echo ""
echo "===================================================================="
