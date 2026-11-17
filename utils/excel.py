"""Helper común para exportar listados a Excel (.xlsx) con openpyxl.

Pedido del cliente (reunión 16-11-26): "exportar a Excel" en varios módulos.
"""
from io import BytesIO
from typing import Iterable, Optional, Sequence

FORMATO_CLP = '#,##0'
FORMATO_CANTIDAD = '#,##0.###'


def generar_xlsx(
    titulo_hoja: str,
    encabezados: Sequence[str],
    filas: Iterable[Sequence],
    anchos: Optional[Sequence[int]] = None,
    formatos: Optional[dict] = None,
) -> bytes:
    """Devuelve el contenido de un .xlsx con encabezado destacado y panel congelado.

    `formatos`: {indice_columna (0-based): number_format}.
    """
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = titulo_hoja[:31]
    ws.append(list(encabezados))
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="1F4E78")

    for fila in filas:
        ws.append(list(fila))

    for idx, fmt in (formatos or {}).items():
        for row in ws.iter_rows(min_row=2, min_col=idx + 1, max_col=idx + 1):
            row[0].number_format = fmt
    for i, ancho in enumerate(anchos or [], start=1):
        ws.column_dimensions[get_column_letter(i)].width = ancho
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
