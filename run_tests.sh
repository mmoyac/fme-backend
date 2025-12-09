#!/bin/bash
# Script para ejecutar todos los tests

echo "🧪 Ejecutando tests del backend..."
echo ""

# Instalar dependencias si es necesario
if [ ! -d ".venv" ]; then
    echo "Creando entorno virtual..."
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

# Ejecutar tests
echo "Ejecutando suite de tests..."
pytest tests/ -v --tb=short

# Generar reporte de cobertura
echo ""
echo "📊 Generando reporte de cobertura..."
pytest tests/ --cov=. --cov-report=html --cov-report=term

echo ""
echo "✅ Tests completados!"
echo "📁 Reporte de cobertura: htmlcov/index.html"
