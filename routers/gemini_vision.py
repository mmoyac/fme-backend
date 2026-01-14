"""
Endpoint para integración con Gemini Vision API
Para extraer datos de etiquetas de carne con mayor precisión
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
import google.generativeai as genai
import base64
from typing import Optional, List
import json
import os
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import Producto
from difflib import SequenceMatcher
from schemas.gemini_vision import DatosEtiquetaResponse, ErrorResponse
from difflib import SequenceMatcher

router = APIRouter(prefix="/api/gemini", tags=["gemini-vision"])

# Configurar Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class DatosEtiquetaResponse(BaseModel):
    peso_bruto_kg: Optional[str] = None
    peso_neto_kg: Optional[str] = None
    fecha_vencimiento: Optional[str] = None  # YYYY-MM-DD
    fecha_fabricacion: Optional[str] = None  # YYYY-MM-DD
    nombre_producto: Optional[str] = None  # Nombre del producto extraído
    producto_id: Optional[int] = None  # ID del producto encontrado por matching
    producto_match_score: Optional[float] = None  # Score del matching (0-1)
    lote_tropa: Optional[str] = None
    codigo_barras_superior: Optional[str] = None
    confianza: Optional[float] = None
    texto_extraido: Optional[str] = None

def encontrar_producto_similar(nombre_extraido: str, db: Session) -> tuple[Optional[int], float]:
    """
    Busca el producto más similar en la base de datos usando fuzzy matching
    Returns: (producto_id, match_score)
    """
    if not nombre_extraido or len(nombre_extraido.strip()) < 2:
        return None, 0.0
    
    productos = db.query(Producto).all()
    mejor_match = None
    mejor_score = 0.0
    
    nombre_limpio = nombre_extraido.strip().lower()
    
    for producto in productos:
        # Comparar con el nombre del producto
        score_nombre = SequenceMatcher(None, nombre_limpio, producto.nombre.lower()).ratio()
        
        # Comparar con el SKU si está disponible
        score_sku = 0.0
        if producto.sku:
            score_sku = SequenceMatcher(None, nombre_limpio, producto.sku.lower()).ratio()
        
        # Tomar el mejor score entre nombre y SKU
        score_final = max(score_nombre, score_sku)
        
        # Si encontramos un match mejor, lo guardamos
        if score_final > mejor_score and score_final > 0.3:  # Umbral mínimo del 30%
            mejor_match = producto.id
            mejor_score = score_final
    
    return mejor_match, mejor_score


@router.post("/extraer-etiqueta", response_model=DatosEtiquetaResponse)
async def extraer_datos_etiqueta(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Extrae datos específicos de etiquetas de carne usando Gemini Vision API
    """
    if not GEMINI_API_KEY:
        raise HTTPException(
            status_code=503, 
            detail="Gemini API no configurada. Configure GEMINI_API_KEY en variables de entorno."
        )
    
    try:
        # Leer archivo de imagen
        contents = await file.read()
        
        # Configurar modelo Gemini - usar modelo 2.5 disponible
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Prompt específico para etiquetas de carne argentinas
        prompt = """
        Analiza esta etiqueta de carne argentina y extrae EXACTAMENTE los siguientes datos en formato JSON.
        
        INSTRUCCIONES ESPECÍFICAS:
        1. Busca "Peso Bruto" o "Gross Weight" - debe ser un número como 19.15
        2. Busca "Peso Neto" o "Net Weight" - debe ser un número como 17.71  
        3. Busca fecha de vencimiento - formato DD/MM/YYYY, conviértela a YYYY-MM-DD
        4. Busca fecha de fabricación, elaboración o faena - formato DD/MM/YYYY, conviértela a YYYY-MM-DD
        5. Busca el NOMBRE DEL PRODUCTO - ej: "PUNTA PICANA", "ASADO", "BIFE DE CHORIZO", etc.
        6. Busca "Lote" o número de 8 dígitos que empiece con "2025" (ej: 20250715)
        7. Busca código de barras de 11 dígitos que empiece con "906" (ej: 90677477200)
        
        FORMATO DE RESPUESTA (solo JSON válido, sin explicaciones):
        {
            "peso_bruto_kg": "19.15",
            "peso_neto_kg": "17.71", 
            "fecha_vencimiento": "2025-11-13",
            "fecha_fabricacion": "2025-07-15",
            "nombre_producto": "PUNTA PICANA",
            "lote_tropa": "20250715",
            "codigo_barras_superior": "90677477200",
            "confianza": 0.95
        }
        
        Si no encuentras algún dato, usa null en lugar del valor.
        """
        
        # Procesar imagen con Gemini
        response = model.generate_content([
            prompt,
            {
                "mime_type": file.content_type,
                "data": contents
            }
        ])
        
        # Extraer JSON de la respuesta
        respuesta_texto = response.text.strip()
        print(f"📝 Respuesta cruda de Gemini: {respuesta_texto[:200]}...")
        
        # Limpiar respuesta si tiene markdown
        if respuesta_texto.startswith("```json"):
            respuesta_texto = respuesta_texto[7:]
        if respuesta_texto.endswith("```"):
            respuesta_texto = respuesta_texto[:-3]
        if respuesta_texto.startswith("```"):
            respuesta_texto = respuesta_texto[3:]
            
        respuesta_texto = respuesta_texto.strip()
        print(f"🧹 Respuesta limpia: {respuesta_texto[:200]}...")
        
        # Parsear JSON
        try:
            datos_extraidos = json.loads(respuesta_texto)
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing JSON: {e}")
            print(f"📝 Texto completo: {respuesta_texto}")
            
            # Intentar crear respuesta manualmente parseando texto
            datos_extraidos = {
                "peso_bruto_kg": None,
                "peso_neto_kg": None,
                "fecha_vencimiento": None,
                "fecha_fabricacion": None,
                "nombre_producto": None,
                "lote_tropa": None,
                "codigo_barras_superior": None,
                "confianza": 0.5
            }
            
            # Buscar patrones en el texto si JSON falló
            import re
            
            # Buscar pesos
            peso_bruto_match = re.search(r'"peso_bruto_kg":\s*"?([0-9]+\.?[0-9]*)"?', respuesta_texto)
            if peso_bruto_match:
                datos_extraidos["peso_bruto_kg"] = peso_bruto_match.group(1)
                
            peso_neto_match = re.search(r'"peso_neto_kg":\s*"?([0-9]+\.?[0-9]*)"?', respuesta_texto)
            if peso_neto_match:
                datos_extraidos["peso_neto_kg"] = peso_neto_match.group(1)
                
            # Buscar fechas
            fecha_venc_match = re.search(r'"fecha_vencimiento":\s*"([0-9]{4}-[0-9]{2}-[0-9]{2})"', respuesta_texto)
            if fecha_venc_match:
                datos_extraidos["fecha_vencimiento"] = fecha_venc_match.group(1)
                
            fecha_fab_match = re.search(r'"fecha_fabricacion":\s*"([0-9]{4}-[0-9]{2}-[0-9]{2})"', respuesta_texto)
            if fecha_fab_match:
                datos_extraidos["fecha_fabricacion"] = fecha_fab_match.group(1)
                
            # Buscar nombre del producto
            producto_match = re.search(r'"nombre_producto":\s*"([^"]+)"', respuesta_texto)
            if producto_match:
                datos_extraidos["nombre_producto"] = producto_match.group(1)
                
            # Buscar lote
            lote_match = re.search(r'"lote_tropa":\s*"([0-9]+)"', respuesta_texto)
            if lote_match:
                datos_extraidos["lote_tropa"] = lote_match.group(1)
                
            # Buscar código
            codigo_match = re.search(r'"codigo_barras_superior":\s*"([0-9]+)"', respuesta_texto)
            if codigo_match:
                datos_extraidos["codigo_barras_superior"] = codigo_match.group(1)
            
            print(f"🔍 Datos extraídos por regex: {datos_extraidos}")
        
        # Hacer fuzzy matching del nombre del producto si se extrajo
        producto_id = None
        producto_match_score = 0.0
        
        if datos_extraidos.get("nombre_producto"):
            producto_id, producto_match_score = encontrar_producto_similar(
                datos_extraidos["nombre_producto"], db
            )
            print(f"🎯 Producto matched: ID={producto_id}, Score={producto_match_score:.2f}")
        
        return DatosEtiquetaResponse(
            peso_bruto_kg=datos_extraidos.get("peso_bruto_kg"),
            peso_neto_kg=datos_extraidos.get("peso_neto_kg"),
            fecha_vencimiento=datos_extraidos.get("fecha_vencimiento"),
            fecha_fabricacion=datos_extraidos.get("fecha_fabricacion"),
            nombre_producto=datos_extraidos.get("nombre_producto"),
            lote_tropa=datos_extraidos.get("lote_tropa"),
            codigo_barras_superior=datos_extraidos.get("codigo_barras_superior"),
            confianza=datos_extraidos.get("confianza", 0.9),
            texto_extraido=respuesta_texto,
            producto_id=producto_id,
            producto_match_score=producto_match_score
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando imagen con Gemini: {str(e)}"
        )

@router.post("/extraer-texto")
async def extraer_solo_texto(file: UploadFile = File(...)):
    """
    Extrae solo el texto completo de la imagen para debugging
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="Gemini API no configurada")
    
    try:
        contents = await file.read()
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = "Extrae TODO el texto visible en esta imagen, conservando el formato original."
        
        response = model.generate_content([
            prompt,
            {
                "mime_type": file.content_type,
                "data": contents
            }
        ])
        
        return {
            "texto_extraido": response.text,
            "modelo": "gemini-1.5-flash"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Agregar al main.py:
# from routers import gemini_vision
# app.include_router(gemini_vision.router)