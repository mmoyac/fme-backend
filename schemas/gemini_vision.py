"""
Schemas para la integración con Gemini Vision API
Extracción de datos de etiquetas de productos cárnicos
"""

from pydantic import BaseModel
from typing import Optional


class DatosEtiquetaResponse(BaseModel):
    """
    Respuesta de extracción de datos de etiqueta usando Gemini Vision
    """
    peso_bruto_kg: Optional[str] = None
    peso_neto_kg: Optional[str] = None
    fecha_vencimiento: Optional[str] = None
    fecha_fabricacion: Optional[str] = None
    nombre_producto: Optional[str] = None
    lote_tropa: Optional[str] = None
    codigo_barras_superior: Optional[str] = None
    confianza: float = 0.0
    texto_extraido: Optional[str] = None
    # Campos para fuzzy matching del producto
    producto_id: Optional[int] = None
    producto_match_score: float = 0.0
    
    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """
    Respuesta de error estándar
    """
    error: str
    detalle: Optional[str] = None
    timestamp: Optional[str] = None
    
    class Config:
        from_attributes = True