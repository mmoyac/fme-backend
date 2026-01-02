"""
Utilidades para generar reportes PDF del sistema de caja.
"""
from datetime import datetime
from typing import List, Dict, Any
from io import BytesIO

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

def generar_pdf_cierre_caja(turno_data: Dict[str, Any], operaciones: List[Dict[str, Any]]) -> BytesIO:
    """
    Genera un PDF con el reporte de cierre de caja.
    
    Args:
        turno_data: Información del turno de caja
        operaciones: Lista de operaciones realizadas durante el turno
    
    Returns:
        BytesIO: PDF generado en memoria
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                          rightMargin=2*cm, leftMargin=2*cm, 
                          topMargin=2*cm, bottomMargin=2*cm)
    
    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=20,
        alignment=TA_CENTER,
        textColor=colors.darkblue
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.darkgreen
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    
    # Contenido del PDF
    story = []
    
    # Título
    story.append(Paragraph("🏪 REPORTE DE CIERRE DE CAJA", title_style))
    story.append(Spacer(1, 20))
    
    # Información del establecimiento
    story.append(Paragraph("MASAS ESTACIÓN", subtitle_style))
    story.append(Paragraph("Sistema de Control de Caja", normal_style))
    story.append(Spacer(1, 15))
    
    # Información del turno
    info_turno = [
        ["📋 INFORMACIÓN DEL TURNO", ""],
        ["", ""],
        ["Turno ID:", f"#{turno_data['id']:05d}"],
        ["Local:", turno_data.get('local_nombre', 'N/A')],
        ["Vendedor:", turno_data.get('vendedor_nombre', 'N/A')],
        ["Fecha Apertura:", format_datetime(turno_data['fecha_apertura'])],
        ["Fecha Cierre:", format_datetime(turno_data['fecha_cierre'])],
        ["Estado:", turno_data['estado']],
    ]
    
    table_info = Table(info_turno, colWidths=[5*cm, 10*cm])
    table_info.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('SPAN', (0, 0), (1, 0)),
        ('BACKGROUND', (0, 0), (1, 0), colors.lightblue),
        ('BACKGROUND', (0, 1), (1, 1), colors.white),
        ('FONTNAME', (0, 2), (0, -1), 'Helvetica-Bold'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    story.append(table_info)
    story.append(Spacer(1, 20))
    
    # Resumen financiero
    monto_inicial = float(turno_data.get('monto_inicial', 0))
    efectivo_esperado = float(turno_data.get('efectivo_esperado', 0))
    efectivo_real = float(turno_data.get('efectivo_real', 0))
    diferencia = float(turno_data.get('diferencia', 0))
    
    # Calcular totales por tipo de operación
    total_ventas = sum(op.get('monto', 0) for op in operaciones if op.get('tipo_operacion') == 'VENTA')
    total_ingresos = sum(op.get('monto', 0) for op in operaciones if op.get('tipo_operacion') == 'INGRESO')
    total_egresos = sum(op.get('monto', 0) for op in operaciones if op.get('tipo_operacion') == 'EGRESO')
    total_devoluciones = sum(op.get('monto', 0) for op in operaciones if op.get('tipo_operacion') == 'DEVOLUCION')
    
    resumen_financiero = [
        ["💰 RESUMEN FINANCIERO", "MONTO"],
        ["", ""],
        ["Monto Inicial", f"${monto_inicial:,.0f}"],
        ["Total Ventas", f"${total_ventas:,.0f}"],
        ["Total Ingresos", f"${total_ingresos:,.0f}"],
        ["Total Egresos", f"${-total_egresos:,.0f}"],
        ["Total Devoluciones", f"${-total_devoluciones:,.0f}"],
        ["", ""],
        ["Efectivo Esperado", f"${efectivo_esperado:,.0f}"],
        ["Efectivo Real", f"${efectivo_real:,.0f}"],
        ["", ""],
        ["DIFERENCIA", f"${diferencia:,.0f}"],
    ]
    
    table_resumen = Table(resumen_financiero, colWidths=[10*cm, 5*cm])
    table_resumen.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, 0), 'Helvetica-Bold'),
        ('SPAN', (0, 0), (0, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgreen),
        ('BACKGROUND', (0, 1), (-1, 1), colors.white),
        ('FONTNAME', (0, 2), (0, 9), 'Helvetica'),
        ('FONTNAME', (0, 11), (0, 11), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 11), (-1, 11), 12),
        ('BACKGROUND', (0, 11), (-1, 11), colors.lightyellow if diferencia == 0 else colors.lightcoral if diferencia < 0 else colors.lightgreen),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    story.append(table_resumen)
    story.append(Spacer(1, 20))
    
    # Detalle de operaciones
    if operaciones:
        story.append(Paragraph("📊 DETALLE DE OPERACIONES", subtitle_style))
        story.append(Spacer(1, 10))
        
        # Encabezados de la tabla
        data_operaciones = [
            ["HORA", "TIPO", "DESCRIPCIÓN", "MEDIO PAGO", "MONTO"]
        ]
        
        # Agregar operaciones
        for op in operaciones:
            fecha_op = format_time(op.get('fecha_operacion', ''))
            tipo_op = op.get('tipo_operacion', '')
            descripcion = op.get('descripcion', '')[:30] + ('...' if len(op.get('descripcion', '')) > 30 else '')
            medio_pago = op.get('medio_pago_nombre', '') if op.get('medio_pago_nombre') else '-'
            monto = op.get('monto', 0)
            
            # Agregar signo según el tipo de operación
            if tipo_op in ['EGRESO', 'DEVOLUCION']:
                monto_str = f"-${abs(monto):,.0f}"
            else:
                monto_str = f"${monto:,.0f}"
            
            data_operaciones.append([
                fecha_op,
                tipo_op,
                descripcion,
                medio_pago,
                monto_str
            ])
        
        table_operaciones = Table(data_operaciones, colWidths=[3*cm, 3*cm, 5*cm, 3*cm, 3*cm])
        table_operaciones.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('ALIGN', (4, 0), (4, -1), 'RIGHT'),  # Alinear montos a la derecha
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        story.append(table_operaciones)
        story.append(Spacer(1, 20))
    
    # Observaciones
    if turno_data.get('observaciones_cierre'):
        story.append(Paragraph("📝 OBSERVACIONES DEL CIERRE", subtitle_style))
        story.append(Paragraph(turno_data['observaciones_cierre'], normal_style))
        story.append(Spacer(1, 20))
    
    # Footer
    story.append(Spacer(1, 30))
    footer_data = [
        ["", "", ""],
        ["_" * 25, "_" * 25, "_" * 25],
        ["Firma Vendedor", "Firma Supervisor", "Fecha y Hora"],
        ["", "", datetime.now().strftime("%d/%m/%Y %H:%M")],
    ]
    
    table_footer = Table(footer_data, colWidths=[5*cm, 5*cm, 5*cm])
    table_footer.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 2), (-1, 2), 'Helvetica-Bold'),
    ]))
    
    story.append(table_footer)
    
    # Generar PDF
    doc.build(story)
    buffer.seek(0)
    return buffer

def format_datetime(date_string: str) -> str:
    """Formatea una fecha para mostrar en el PDF."""
    if not date_string:
        return "N/A"
    try:
        dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return dt.strftime("%d/%m/%Y %H:%M")
    except:
        return date_string

def format_time(date_string: str) -> str:
    """Formatea solo la hora para mostrar en el PDF."""
    if not date_string:
        return "N/A"
    try:
        dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return dt.strftime("%H:%M")
    except:
        return date_string