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
        elements.extend(self._crear_encabezado(pedido))
        
        # Información de la boleta
        elements.extend(self._crear_info_boleta(pedido))
        
        # Información del cliente
        elements.extend(self._crear_info_cliente(pedido))
        
        # Tabla de productos
        elements.extend(self._crear_tabla_productos(pedido))
        
        # Totales
        elements.extend(self._crear_totales(pedido))
        
        # Pie de página
        elements.extend(self._crear_pie_pagina(pedido))
        
        # Construir PDF
        doc.build(elements)
        
        # Reiniciar buffer para lectura
        buffer.seek(0)
        return buffer
    
    def _crear_encabezado(self, pedido: Pedido):
        """Crear encabezado con información de la empresa."""
        elementos = []
        
        # Obtener información del tenant desde el pedido
        tenant = pedido.tenant
        config_landing = tenant.configuracion_landing if tenant and hasattr(tenant, 'configuracion_landing') else None
        
        # Usar nombre del tenant o el nombre comercial de la configuración
        nombre_empresa = tenant.nombre if tenant else "TIENDA"
        if config_landing and config_landing.nombre_comercial:
            nombre_empresa = config_landing.nombre_comercial.upper()
        
        # Usar dominio principal o descripción del footer
        subtitulo = f"www.{tenant.dominio_principal}" if tenant and tenant.dominio_principal else ""
        if config_landing and config_landing.texto_footer_descripcion:
            subtitulo = config_landing.texto_footer_descripcion
        
        # Título de la empresa
        elementos.append(Paragraph(nombre_empresa, self.styles['TituloEmpresa']))
        if subtitulo:
            elementos.append(Paragraph(subtitulo, self.styles['SubtituloEmpresa']))
        
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
        numero_pedido = pedido.numero_pedido
        
        estado_codigo = pedido.estado_pedido.codigo if pedido.estado_pedido else "—"

        info_data = [
            ["N° Pedido:", numero_pedido, "Fecha:", fecha_formateada],
            ["Estado:", estado_codigo, "Pagado:", "SÍ" if pedido.es_pagado else "NO"]
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
    
    def _calcular_iva_pedido(self, pedido):
        """Calcula neto, IVA y total para el pedido completo."""
        TASA_IVA = 0.19
        neto_total = 0.0
        iva_total = 0.0
        for item in pedido.items:
            precio = float(item.precio_unitario_venta)
            qty = float(item.cantidad)
            incluye_iva = getattr(item.producto, 'precio_incluye_iva', True) if item.producto else True
            if incluye_iva:
                # Precio ya incluye IVA → extraer neto
                neto_item = round((precio / (1 + TASA_IVA)) * qty)
            else:
                # Precio es neto → calcular IVA
                neto_item = round(precio * qty)
            iva_item = round(neto_item * TASA_IVA)
            neto_total += neto_item
            iva_total += iva_item
        return int(neto_total), int(iva_total)

    def _crear_tabla_productos(self, pedido: Pedido):
        """Crear tabla con el detalle de productos."""
        elementos = []

        TASA_IVA = 0.19

        # Encabezados de la tabla
        headers = ["Producto", "Cant.", "Precio Unit.", "Neto", "Subtotal"]
        data = [headers]

        # Agregar productos
        for item in pedido.items:
            precio = float(item.precio_unitario_venta)
            qty = float(item.cantidad)
            incluye_iva = getattr(item.producto, 'precio_incluye_iva', True) if item.producto else True

            subtotal_bruto = round(precio * qty)
            if incluye_iva:
                neto_item = round((precio / (1 + TASA_IVA)) * qty)
            else:
                neto_item = round(precio * qty)
                subtotal_bruto = round(precio * qty * (1 + TASA_IVA))

            data.append([
                item.producto.nombre if item.producto else f"Producto ID {item.producto_id}",
                str(qty if qty != int(qty) else int(qty)),
                f"${precio:,.0f}",
                f"${neto_item:,.0f}",
                f"${subtotal_bruto:,.0f}"
            ])

        # Crear tabla
        tabla = Table(data, colWidths=[70*mm, 15*mm, 28*mm, 24*mm, 25*mm])
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

        # Calcular neto e IVA
        neto_total, iva_total = self._calcular_iva_pedido(pedido)
        monto_bruto = pedido.monto_total  # Total con IVA ya calculado y almacenado

        # Subtotal (si hay descuento por puntos)
        if pedido.descuento_puntos and pedido.descuento_puntos > 0:
            subtotal = float(pedido.monto_total) + float(pedido.descuento_puntos)
            totales_data.append(["Subtotal:", f"${subtotal:,.0f}"])
            totales_data.append([
                f"Descuento puntos ({pedido.puntos_usados or 0} pts):",
                f"-${float(pedido.descuento_puntos):,.0f}"
            ])

        # Desglose IVA
        totales_data.append(["Neto:", f"${neto_total:,.0f}"])
        totales_data.append(["IVA (19%):", f"${iva_total:,.0f}"])

        # Total final
        totales_data.append(["TOTAL:", f"${pedido.monto_total:,.0f}"])
        
        # Información de puntos según el estado del pedido
        estado_codigo = pedido.estado_pedido.codigo if pedido.estado_pedido else ""
        if estado_codigo == 'CANCELADO':
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
                if estado_codigo in ['CONFIRMADO', 'EN_PREPARACION', 'ENTREGADO']:
                    estado_puntos = " ✓"
                else:
                    estado_puntos = " (pendiente confirmación)"
                
                totales_data.append([
                    f"Puntos ganados{estado_puntos}:",
                    f"+{pedido.puntos_ganados} pts"
                ])
        
        # Mostrar puntos disponibles del cliente DESPUÉS de procesar este pedido
        # (Solo para pedidos no cancelados, ya que los cancelados no afectan los puntos)
        if estado_codigo != 'CANCELADO':
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
                if estado_codigo in ['CONFIRMADO', 'EN_PREPARACION', 'ENTREGADO']:
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
        else:  # estado_codigo == 'CANCELADO'
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
    
    def _crear_pie_pagina(self, pedido: Pedido):
        """Crear pie de página."""
        elementos = []
        
        # Obtener información del tenant desde el pedido
        tenant = pedido.tenant
        config_landing = tenant.configuracion_landing if tenant and hasattr(tenant, 'configuracion_landing') else None
        
        # Usar nombre del tenant
        nombre_empresa = tenant.nombre if tenant else "Tienda"
        if config_landing and config_landing.nombre_comercial:
            nombre_empresa = config_landing.nombre_comercial
        
        # Usar descripción del footer o dominio
        subtitulo = ""
        if config_landing and config_landing.texto_footer_descripcion:
            subtitulo = config_landing.texto_footer_descripcion
        elif tenant and tenant.dominio_principal:
            subtitulo = f"www.{tenant.dominio_principal}"
        
        # Información adicional
        texto_gracias = f"¡Gracias por su compra!<br/>{nombre_empresa}"
        if subtitulo:
            texto_gracias += f" - {subtitulo}"
        
        elementos.append(Paragraph(
            texto_gracias,
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


class GeneradorFactura(GeneradorBoleta):
    """
    Generador de facturas en formato PDF.
    Extiende GeneradorBoleta añadiendo datos tributarios del cliente.
    """

    def _setup_custom_styles(self):
        super()._setup_custom_styles()
        self.styles.add(ParagraphStyle(
            name='TituloFactura',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1D4ED8'),
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))

    def generar_factura(self, pedido: Pedido) -> BinaryIO:
        """Genera una factura en PDF para el pedido dado."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        elements = []
        elements.extend(self._crear_encabezado_factura(pedido))
        elements.extend(self._crear_info_factura(pedido))
        elements.extend(self._crear_info_cliente_tributario(pedido))
        elements.extend(self._crear_tabla_productos(pedido))
        elements.extend(self._crear_totales(pedido))
        elements.extend(self._crear_pie_factura(pedido))
        doc.build(elements)
        buffer.seek(0)
        return buffer

    def _calcular_iva_pedido(self, pedido):
        """Override: para CAJAS_VARIABLES usa asignaciones_picking para calcular neto/IVA correcto.
        Para otros tipos delega al método base que usa precio_unitario_venta."""
        es_cajas = (
            (pedido.tipo_pedido and pedido.tipo_pedido.codigo == "CAJAS_VARIABLES")
            or getattr(pedido, 'tipo_pedido_id', None) == 2
        )
        if es_cajas:
            TASA_IVA = 0.19
            neto_total = 0.0
            for item in pedido.items:
                for asig in getattr(item, 'asignaciones_picking', []):
                    neto_total += float(asig.peso_real) * float(asig.precio_kg)
            neto_total = round(neto_total)
            iva_total = round(neto_total * TASA_IVA)
            return int(neto_total), int(iva_total)
        return super()._calcular_iva_pedido(pedido)

    def _crear_encabezado_factura(self, pedido: Pedido):
        """Encabezado igual al de boleta pero con título de factura."""
        elementos = self._crear_encabezado(pedido)
        return elementos

    def _crear_info_factura(self, pedido: Pedido):
        """Información del número de pedido/factura y folio SII."""
        elementos = []

        if 'TituloFactura' not in self.styles:
            self.styles.add(ParagraphStyle(
                name='TituloFactura',
                parent=self.styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#1D4ED8'),
                spaceAfter=10,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            ))

        elementos.append(Paragraph("FACTURA ELECTRÓNICA", self.styles['TituloFactura']))
        elementos.append(Spacer(1, 5*mm))

        chile_tz = pytz.timezone('America/Santiago')
        if pedido.fecha_pedido.tzinfo is None:
            fecha_utc = pytz.utc.localize(pedido.fecha_pedido)
        else:
            fecha_utc = pedido.fecha_pedido
        fecha_chile = fecha_utc.astimezone(chile_tz)
        fecha_formateada = fecha_chile.strftime("%d/%m/%Y %H:%M")

        folio_valor = pedido.folio_sii if pedido.folio_sii else "Pendiente"
        estado_sii = pedido.estado_sii if pedido.estado_sii else "PENDIENTE"

        info_data = [
            ["N° Pedido:", pedido.numero_pedido, "Fecha:", fecha_formateada],
            ["Folio SII:", folio_valor, "Estado SII:", estado_sii],
        ]
        if pedido.numero_dte:
            info_data.append(["N° DTE:", pedido.numero_dte, "", ""])

        info_table = Table(info_data, colWidths=[30*mm, 50*mm, 25*mm, 50*mm])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ]))
        elementos.append(info_table)
        elementos.append(Spacer(1, 8*mm))
        return elementos

    def _crear_info_cliente_tributario(self, pedido: Pedido):
        """Datos tributarios completos del cliente (RUT, razón social, giro)."""
        elementos = []
        elementos.append(Paragraph("<b>DATOS DEL RECEPTOR</b>", self.styles['DatosPedido']))
        elementos.append(Spacer(1, 3*mm))

        cliente = pedido.cliente
        cliente_data = []

        # Razón social o nombre
        nombre_display = cliente.razon_social if cliente.razon_social else f"{cliente.nombre} {cliente.apellido or ''}".strip()
        cliente_data.append(["Razón Social / Nombre:", nombre_display])

        if cliente.rut:
            cliente_data.append(["RUT:", cliente.rut])

        if cliente.giro:
            cliente_data.append(["Giro:", cliente.giro])

        if cliente.email:
            cliente_data.append(["Email:", cliente.email])

        if cliente.telefono:
            cliente_data.append(["Teléfono:", cliente.telefono])

        if cliente.direccion:
            cliente_data.append(["Dirección:", cliente.direccion])

        cliente_table = Table(cliente_data, colWidths=[45*mm, 110*mm])
        cliente_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EFF6FF')),
        ]))
        elementos.append(cliente_table)
        elementos.append(Spacer(1, 8*mm))
        return elementos

    def _crear_tabla_productos(self, pedido: Pedido):
        """Tabla de productos para factura: muestra kg y precio/kg para cajas variables."""
        elementos = []
        TASA_IVA = 0.19

        # Detectar si es pedido de cajas variables (tipo_pedido_id == 2)
        es_cajas_variables = (
            pedido.tipo_pedido and pedido.tipo_pedido.codigo == "CAJAS_VARIABLES"
        ) or (pedido.tipo_pedido_id == 2)

        if es_cajas_variables:
            headers = ["Producto", "Lote / Código", "Kg netos", "$/kg (neto)", "Neto", "IVA 19%", "Total"]
            data = [headers]

            for item in pedido.items:
                nombre_producto = item.producto.nombre if item.producto else f"Producto {item.producto_id}"
                asignaciones = getattr(item, 'asignaciones_picking', [])

                if asignaciones:
                    for asig in asignaciones:
                        lote = asig.lote
                        codigo_lote = lote.codigo_lote if lote else (asig.lote_id or "—")
                        peso_kg = float(asig.peso_real) if asig.peso_real else 0.0
                        precio_kg_neto = float(asig.precio_kg) if asig.precio_kg else 0.0
                        neto = round(peso_kg * precio_kg_neto)
                        iva = round(neto * TASA_IVA)
                        total_lote = neto + iva
                        data.append([
                            nombre_producto,
                            str(codigo_lote),
                            f"{peso_kg:,.3f} kg",
                            f"${precio_kg_neto:,.0f}",
                            f"${neto:,.0f}",
                            f"${iva:,.0f}",
                            f"${total_lote:,.0f}",
                        ])
                else:
                    # Sin asignaciones aún: mostrar fila resumida
                    precio = float(item.precio_unitario_venta)
                    qty = float(item.cantidad)
                    neto = round(precio * qty)
                    iva = round(neto * TASA_IVA)
                    data.append([
                        nombre_producto,
                        "—",
                        f"{qty:,.3f} kg",
                        f"${precio:,.0f}",
                        f"${neto:,.0f}",
                        f"${iva:,.0f}",
                        f"${neto + iva:,.0f}",
                    ])

            col_widths = [50*mm, 35*mm, 18*mm, 18*mm, 18*mm, 14*mm, 18*mm]
            tabla = Table(data, colWidths=col_widths)
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1D4ED8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
                ('ALIGN', (0, 1), (1, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#EFF6FF'), colors.white]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#BFDBFE')),
            ]))
        else:
            # Tabla estándar para productos regulares
            headers = ["Producto", "Cant.", "Precio Unit.", "Neto", "Subtotal"]
            data = [headers]
            for item in pedido.items:
                precio = float(item.precio_unitario_venta)
                qty = float(item.cantidad)
                incluye_iva = getattr(item.producto, 'precio_incluye_iva', True) if item.producto else True
                subtotal_bruto = round(precio * qty)
                if incluye_iva:
                    neto_item = round((precio / (1 + TASA_IVA)) * qty)
                else:
                    neto_item = round(precio * qty)
                    subtotal_bruto = round(precio * qty * (1 + TASA_IVA))
                data.append([
                    item.producto.nombre if item.producto else f"Producto ID {item.producto_id}",
                    str(qty if qty != int(qty) else int(qty)),
                    f"${precio:,.0f}",
                    f"${neto_item:,.0f}",
                    f"${subtotal_bruto:,.0f}",
                ])
            col_widths = [70*mm, 15*mm, 28*mm, 24*mm, 25*mm]
            tabla = Table(data, colWidths=col_widths)
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#374151')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F8FAFC'), colors.white]),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
            ]))

        elementos.append(tabla)
        elementos.append(Spacer(1, 5*mm))
        return elementos

    def _crear_pie_factura(self, pedido: Pedido):
        """Pie de página de la factura."""
        elementos = []
        tenant = pedido.tenant
        config_landing = tenant.configuracion_landing if tenant and hasattr(tenant, 'configuracion_landing') else None
        nombre_empresa = tenant.nombre if tenant else "Tienda"
        if config_landing and config_landing.nombre_comercial:
            nombre_empresa = config_landing.nombre_comercial

        subtitulo = ""
        if config_landing and config_landing.texto_footer_descripcion:
            subtitulo = config_landing.texto_footer_descripcion
        elif tenant and tenant.dominio_principal:
            subtitulo = f"www.{tenant.dominio_principal}"

        texto = f"Factura emitida por {nombre_empresa}"
        if subtitulo:
            texto += f" - {subtitulo}"
        elementos.append(Paragraph(texto, self.styles['SubtituloEmpresa']))
        elementos.append(Spacer(1, 5*mm))

        chile_tz = pytz.timezone('America/Santiago')
        fecha_generacion = datetime.now(chile_tz).strftime("%d/%m/%Y %H:%M")
        elementos.append(Paragraph(
            f"<font size='8'>Factura generada el {fecha_generacion}</font>",
            ParagraphStyle('Pequeño2', parent=self.styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.HexColor('#9CA3AF'))
        ))
        return elementos


def generar_factura_pedido(pedido: Pedido) -> BinaryIO:
    """
    Función helper para generar una factura de un pedido (tipo FAC).

    Args:
        pedido: Instancia del pedido
        
    Returns:
        BytesIO: Buffer con el PDF generado
    """
    generador = GeneradorFactura()
    return generador.generar_factura(pedido)