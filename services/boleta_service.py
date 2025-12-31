"""
Servicio para generar boletas/facturas en PDF.
"""
import io
from datetime import datetime
from typing import BinaryIO
import pytz

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from database.models import Pedido


class GeneradorBoleta:
    """
    Generador de boletas en formato PDF.
    """
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configurar estilos personalizados para la boleta."""
        # Título principal
        self.styles.add(ParagraphStyle(
            name='TituloEmpresa',
            parent=self.styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1E293B'),
            spaceAfter=5,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Subtítulo
        self.styles.add(ParagraphStyle(
            name='SubtituloEmpresa',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#475569'),
            spaceAfter=20,
            alignment=TA_CENTER
        ))
        
        # Título de boleta
        self.styles.add(ParagraphStyle(
            name='TituloBoleta',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#DC2626'),
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Datos del pedido
        self.styles.add(ParagraphStyle(
            name='DatosPedido',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#374151'),
            spaceAfter=3,
            alignment=TA_LEFT
        ))
    
    def generar_boleta(self, pedido: Pedido) -> BinaryIO:
        """
        Genera una boleta en PDF para el pedido dado.
        
        Args:
            pedido: Instancia del pedido para generar la boleta
            
        Returns:
            BytesIO: Buffer con el PDF generado
        """
        # Crear buffer para el PDF
        buffer = io.BytesIO()
        
        # Crear documento PDF
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        # Elementos del documento
        elements = []
        
        # Encabezado de la empresa
        elements.extend(self._crear_encabezado())
        
        # Información de la boleta
        elements.extend(self._crear_info_boleta(pedido))
        
        # Información del cliente
        elements.extend(self._crear_info_cliente(pedido))
        
        # Tabla de productos
        elements.extend(self._crear_tabla_productos(pedido))
        
        # Totales
        elements.extend(self._crear_totales(pedido))
        
        # Pie de página
        elements.extend(self._crear_pie_pagina())
        
        # Construir PDF
        doc.build(elements)
        
        # Reiniciar buffer para lectura
        buffer.seek(0)
        return buffer
    
    def _crear_encabezado(self):
        """Crear encabezado con información de la empresa."""
        elementos = []
        
        # Título de la empresa
        elementos.append(Paragraph("MASAS ESTACIÓN", self.styles['TituloEmpresa']))
        elementos.append(Paragraph("Panadería y Pastelería Artesanal", self.styles['SubtituloEmpresa']))
        
        # Línea separadora
        elementos.append(Spacer(1, 10*mm))
        
        return elementos
    
    def _crear_info_boleta(self, pedido: Pedido):
        """Crear información de la boleta."""
        elementos = []
        
        # Título de boleta
        elementos.append(Paragraph("BOLETA DE VENTA", self.styles['TituloBoleta']))
        elementos.append(Spacer(1, 5*mm))
        
        # Configurar zona horaria de Chile
        chile_tz = pytz.timezone('America/Santiago')
        
        # Convertir fecha del pedido a zona horaria de Chile
        if pedido.fecha_pedido.tzinfo is None:
            # Si no tiene zona horaria, asumir UTC
            fecha_utc = pytz.utc.localize(pedido.fecha_pedido)
        else:
            fecha_utc = pedido.fecha_pedido
        
        fecha_chile = fecha_utc.astimezone(chile_tz)
        fecha_formateada = fecha_chile.strftime("%d/%m/%Y %H:%M")
        numero_pedido = f"PED-{pedido.id:05d}"
        
        info_data = [
            ["N° Pedido:", numero_pedido, "Fecha:", fecha_formateada],
            ["Estado:", pedido.estado, "Pagado:", "SÍ" if pedido.es_pagado else "NO"]
        ]
        
        info_table = Table(info_data, colWidths=[30*mm, 50*mm, 20*mm, 40*mm])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),  # Primera columna en negrita
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),  # Tercera columna en negrita
        ]))
        
        elementos.append(info_table)
        elementos.append(Spacer(1, 8*mm))
        
        return elementos
    
    def _crear_info_cliente(self, pedido: Pedido):
        """Crear información del cliente."""
        elementos = []
        
        # Título
        elementos.append(Paragraph("<b>DATOS DEL CLIENTE</b>", self.styles['DatosPedido']))
        elementos.append(Spacer(1, 3*mm))
        
        # Información del cliente
        cliente_data = [
            ["Nombre:", pedido.cliente.nombre],
            ["Email:", pedido.cliente.email],
        ]
        
        if pedido.cliente.telefono:
            cliente_data.append(["Teléfono:", pedido.cliente.telefono])
        
        if pedido.cliente.direccion:
            cliente_data.append(["Dirección:", pedido.cliente.direccion])
            if pedido.cliente.comuna:
                cliente_data.append(["Comuna:", pedido.cliente.comuna])
        
        cliente_table = Table(cliente_data, colWidths=[30*mm, 120*mm])
        cliente_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ]))
        
        elementos.append(cliente_table)
        elementos.append(Spacer(1, 8*mm))
        
        return elementos
    
    def _crear_tabla_productos(self, pedido: Pedido):
        """Crear tabla con el detalle de productos."""
        elementos = []
        
        # Encabezados de la tabla
        headers = ["Producto", "Cant.", "Precio Unit.", "Subtotal"]
        data = [headers]
        
        # Agregar productos
        total_general = 0
        for item in pedido.items:
            subtotal = item.cantidad * item.precio_unitario_venta
            total_general += subtotal
            
            data.append([
                item.producto.nombre if item.producto else f"Producto ID {item.producto_id}",
                str(item.cantidad),
                f"${item.precio_unitario_venta:,.0f}",
                f"${subtotal:,.0f}"
            ])
        
        # Crear tabla
        tabla = Table(data, colWidths=[80*mm, 20*mm, 30*mm, 30*mm])
        tabla.setStyle(TableStyle([
            # Estilo del encabezado
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            
            # Estilo del contenido
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Cantidad y precios centrados
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),     # Producto alineado a la izquierda
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F8FAFC'), colors.white]),
            
            # Bordes
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
        ]))
        
        elementos.append(tabla)
        elementos.append(Spacer(1, 5*mm))
        
        return elementos
    
    def _crear_totales(self, pedido: Pedido):
        """Crear sección de totales."""
        elementos = []
        
        # Preparar datos de totales
        totales_data = []
        
        # Subtotal (si hay descuento por puntos)
        if pedido.descuento_puntos and pedido.descuento_puntos > 0:
            subtotal = pedido.monto_total + float(pedido.descuento_puntos)
            totales_data.append(["Subtotal:", f"${subtotal:,.0f}"])
            
            # Descuento por puntos
            totales_data.append([
                f"Descuento puntos ({pedido.puntos_usados or 0} pts):", 
                f"-${float(pedido.descuento_puntos):,.0f}"
            ])
        
        # Total final
        totales_data.append(["TOTAL:", f"${pedido.monto_total:,.0f}"])
        
        # Información de puntos según el estado del pedido
        if pedido.estado == 'CANCELADO':
            # Si el pedido está cancelado, mostrar información de devolución
            if pedido.puntos_ganados and pedido.puntos_ganados > 0:
                totales_data.append([
                    "Puntos devueltos:",
                    f"-{pedido.puntos_ganados} pts"
                ])
            if pedido.puntos_usados and pedido.puntos_usados > 0:
                totales_data.append([
                    "Puntos reintegrados:",
                    f"+{pedido.puntos_usados} pts"
                ])
            totales_data.append([
                "⚠️ PEDIDO CANCELADO",
                ""
            ])
        else:
            # Información de puntos ganados (solo si el pedido no está cancelado)
            if pedido.puntos_ganados and pedido.puntos_ganados > 0:
                estado_puntos = ""
                if pedido.estado in ['CONFIRMADO', 'EN_PREPARACION', 'ENTREGADO']:
                    estado_puntos = " ✓"
                else:
                    estado_puntos = " (pendiente confirmación)"
                
                totales_data.append([
                    f"Puntos ganados{estado_puntos}:",
                    f"+{pedido.puntos_ganados} pts"
                ])
        
        # Mostrar puntos disponibles del cliente DESPUÉS de procesar este pedido
        # (Solo para pedidos no cancelados, ya que los cancelados no afectan los puntos)
        if pedido.estado != 'CANCELADO':
            from services.puntos_service import PuntosService
            from database.database import SessionLocal
            from database.models import MovimientoPuntos
            
            # Obtener sesión de BD para consultar puntos del cliente
            db = SessionLocal()
            try:
                # Calcular puntos disponibles al momento de este pedido
                # Sumar todos los movimientos hasta la fecha de este pedido
                movimientos = db.query(MovimientoPuntos).filter(
                    MovimientoPuntos.cliente_id == pedido.cliente_id,
                    MovimientoPuntos.fecha_movimiento <= pedido.fecha_pedido
                ).order_by(MovimientoPuntos.fecha_movimiento.asc()).all()
                
                puntos_disponibles_en_momento = 0
                for mov in movimientos:
                    if mov.tipo_movimiento.value in ['GANADOS']:
                        puntos_disponibles_en_momento += mov.puntos
                    elif mov.tipo_movimiento.value in ['USADOS']:
                        puntos_disponibles_en_momento -= mov.puntos
                    elif mov.tipo_movimiento.value in ['AJUSTE']:
                        puntos_disponibles_en_momento += mov.puntos  # Los ajustes pueden ser positivos o negativos
                
                # Agregar los puntos de este pedido si está confirmado
                if pedido.estado in ['CONFIRMADO', 'EN_PREPARACION', 'ENTREGADO']:
                    # Sumar puntos ganados en este pedido
                    if pedido.puntos_ganados:
                        puntos_disponibles_en_momento += pedido.puntos_ganados
                    # Restar puntos usados en este pedido
                    if pedido.puntos_usados:
                        puntos_disponibles_en_momento -= pedido.puntos_usados
                
                # Solo mostrar si hay puntos disponibles
                if puntos_disponibles_en_momento > 0:
                    totales_data.append([
                        "Puntos disponibles:",
                        f"{puntos_disponibles_en_momento} pts"
                    ])
            except Exception:
                # Si hay error obteniendo puntos, no mostrar nada
                pass
            finally:
                db.close()
        else:
            # Para pedidos cancelados, mostrar los puntos disponibles actuales del cliente
            from services.puntos_service import PuntosService
            from database.database import SessionLocal
            
            db = SessionLocal()
            try:
                puntos_cliente = PuntosService.obtener_puntos_cliente(db, pedido.cliente_id)
                if puntos_cliente and puntos_cliente.puntos_disponibles >= 0:
                    totales_data.append([
                        "Puntos actuales:",
                        f"{puntos_cliente.puntos_disponibles} pts"
                    ])
            except Exception:
                pass
            finally:
                db.close()
        
        totales_table = Table(totales_data, colWidths=[130*mm, 30*mm])
        totales_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-2, -1), 'Helvetica'),  # Filas normales
            ('FONTNAME', (-2, -2), (-2, -2), 'Helvetica-Bold'),  # Fila del TOTAL
            ('FONTSIZE', (0, 0), (-2, -1), 10),  # Filas normales
            ('FONTSIZE', (-2, -2), (-2, -2), 12),  # Fila del TOTAL
            ('BACKGROUND', (-2, -2), (-1, -2), colors.HexColor('#F1F5F9')),  # Fondo del TOTAL
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
            ('LINEABOVE', (-2, -2), (-1, -2), 2, colors.HexColor('#374151')),  # Línea arriba del TOTAL
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elementos.append(totales_table)
        elementos.append(Spacer(1, 10*mm))
        
        return elementos
    
    def _crear_pie_pagina(self):
        """Crear pie de página."""
        elementos = []
        
        # Información adicional
        elementos.append(Paragraph(
            "¡Gracias por su compra!<br/>Masas Estación - Panadería Artesanal",
            self.styles['SubtituloEmpresa']
        ))
        
        elementos.append(Spacer(1, 5*mm))
        
        # Fecha de generación en zona horaria de Chile
        chile_tz = pytz.timezone('America/Santiago')
        fecha_generacion = datetime.now(chile_tz).strftime("%d/%m/%Y %H:%M")
        elementos.append(Paragraph(
            f"<font size='8'>Boleta generada el {fecha_generacion}</font>",
            ParagraphStyle('Pequeño', parent=self.styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.HexColor('#9CA3AF'))
        ))
        
        return elementos


def generar_boleta_pedido(pedido: Pedido) -> BinaryIO:
    """
    Función helper para generar una boleta de un pedido.
    
    Args:
        pedido: Instancia del pedido
        
    Returns:
        BytesIO: Buffer con el PDF generado
    """
    generador = GeneradorBoleta()
    return generador.generar_boleta(pedido)