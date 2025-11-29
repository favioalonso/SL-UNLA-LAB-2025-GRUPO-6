"""
Módulo para generar reportes en formato PDF usando la librería borb 2.1.5.
Contiene funciones para crear PDFs de los diferentes tipos de reportes del sistema.
"""
from borb.pdf import TableCell
from borb.pdf import Document, Page, SingleColumnLayout, Paragraph, PDF, FixedColumnWidthTable as Table
from borb.pdf.canvas.color.color import HexColor
from borb.pdf.canvas.layout.layout_element import Alignment
from decimal import Decimal
from io import BytesIO
from datetime import date


def generar_pdf_turnos_por_fecha(fecha: str, cantidad: int, turnos: list) -> bytes:
    """
    Genera un PDF con el reporte de turnos por fecha.

    Args:
        fecha: Fecha del reporte en formato YYYY-MM-DD
        cantidad: Cantidad total de turnos
        turnos: Lista de personas con sus turnos para esa fecha
                Estructura esperada: [{"persona": {"id": int, "nombre": str, "dni": str}, "turnos": [...]}]

    Returns:
        bytes: Contenido del PDF generado
    """
    doc = Document()
    page = Page()
    doc.add_page(page)
    layout = SingleColumnLayout(page)

    # Título
    layout.add(Paragraph(
        "Reporte de Turnos por Fecha",
        font_size=Decimal(20),
        font_color=HexColor("#2C3E50")
    ))

    layout.add(Paragraph(f"Fecha: {fecha}", font_size=Decimal(14)))
    layout.add(Paragraph(f"Total de turnos: {cantidad}", font_size=Decimal(12)))
    layout.add(Paragraph(" "))  # Espacio

    # Generar tabla con los datos
    if turnos:
        for persona_data in turnos:
            persona = persona_data["persona"]
            turnos_persona = persona_data["turnos"]

            # Información de la persona
            layout.add(Paragraph(
                f"Persona: {persona['nombre']}",
                font_size=Decimal(14),
                font_color=HexColor("#34495E")
            ))
            layout.add(Paragraph(f"DNI: {persona['dni']}", font_size=Decimal(10)))

            # Tabla de turnos
            tabla = Table(number_of_rows=len(turnos_persona) + 1, number_of_columns=3)

            # Encabezados
            tabla.add(Paragraph("ID", font_color=HexColor("#FFFFFF"), background_color=HexColor("#3498DB")))
            tabla.add(Paragraph("Hora", font_color=HexColor("#FFFFFF"), background_color=HexColor("#3498DB")))
            tabla.add(Paragraph("Estado", font_color=HexColor("#FFFFFF"), background_color=HexColor("#3498DB")))

            # Datos
            for turno in turnos_persona:
                tabla.add(Paragraph(str(turno["id"])))
                tabla.add(Paragraph(str(turno["hora"])))
                tabla.add(Paragraph(turno["estado"]))

            layout.add(tabla)
            layout.add(Paragraph(" "))  # Espacio entre personas
    else:
        layout.add(Paragraph("No se encontraron turnos para esta fecha.", font_size=Decimal(12)))

    # Generar bytes del PDF
    buffer = BytesIO()
    PDF.dumps(buffer, doc)
    return buffer.getvalue()


def generar_pdf_turnos_cancelados_mes(reporte_data: dict) -> bytes:
    """
    Genera un PDF con el reporte de turnos cancelados del mes especificado.

    Args:
        reporte_data: Diccionario con los datos del reporte
                     Estructura esperada: {"mes": str, "anio": int, "total_cancelados": int, "detalle_por_persona": [...]}

    Returns:
        bytes: Contenido del PDF generado
    """
    doc = Document()
    page = Page()
    doc.add_page(page)
    layout = SingleColumnLayout(page)

    # Título
    mes = reporte_data.get('mes', 'N/A')
    anio = reporte_data.get('anio', 'N/A')
    layout.add(Paragraph(
        f"Reporte de Turnos Cancelados - {mes} {anio}",
        font_size=Decimal(20),
        font_color=HexColor("#E74C3C")
    ))

    layout.add(Paragraph(" "))
    total = reporte_data.get('total_cancelados', 0)
    layout.add(Paragraph(f"Total de turnos cancelados: {total}", font_size=Decimal(14)))
    layout.add(Paragraph(" "))

    # Tabla con personas y turnos cancelados
    detalle = reporte_data.get('detalle_por_persona', [])

    if detalle and total > 0:
        # Tabla con 4 columnas
        tabla = Table(number_of_rows=len(detalle) + 1, number_of_columns=4)

        # Encabezados
        tabla.add(Paragraph("DNI", font_color=HexColor("#FFFFFF"), background_color=HexColor("#E74C3C")))
        tabla.add(Paragraph("Nombre", font_color=HexColor("#FFFFFF"), background_color=HexColor("#E74C3C")))
        tabla.add(Paragraph("Teléfono", font_color=HexColor("#FFFFFF"), background_color=HexColor("#E74C3C")))
        tabla.add(Paragraph("Cant. Cancelados", font_color=HexColor("#FFFFFF"), background_color=HexColor("#E74C3C")))

        # Datos
        for item in detalle:
            persona_info = item.get('persona', {})
            tabla.add(Paragraph(persona_info.get('dni', 'N/A')))
            tabla.add(Paragraph(persona_info.get('nombre', 'N/A')))
            tabla.add(Paragraph(persona_info.get('telefono', 'N/A')))
            tabla.add(Paragraph(str(persona_info.get('cantidad_de_cancelados', 0))))

        layout.add(tabla)
    else:
        layout.add(Paragraph(
            f"No se encontraron turnos cancelados para {mes} de {anio}.",
            font_size=Decimal(12),
            font_color=HexColor("#7F8C8D")
        ))

    # Generar bytes del PDF
    buffer = BytesIO()
    PDF.dumps(buffer, doc)
    return buffer.getvalue()


def generar_pdf_turnos_por_persona(persona_data: dict) -> bytes:
    """
    Genera un PDF con el reporte de turnos de una persona específica.

    Args:
        persona_data: Diccionario con datos de la persona y sus turnos
                     Estructura esperada del endpoint get_turnos_por_dni:
                     {"persona": {"nombre": str, "dni": str, "edad": int}, "turnos": [...], "total_turnos": int}

    Returns:
        bytes: Contenido del PDF generado
    """
    doc = Document()
    page = Page()
    doc.add_page(page)
    layout = SingleColumnLayout(page)

    # Título
    layout.add(Paragraph(
        "Reporte de Turnos por Persona",
        font_size=Decimal(20),
        font_color=HexColor("#27AE60")
    ))

    layout.add(Paragraph(" "))

    # Información de la persona (PersonaOut es un objeto Pydantic, no un diccionario)
    persona = persona_data["persona"]
    layout.add(Paragraph(f"Nombre: {persona.nombre}", font_size=Decimal(16)))
    layout.add(Paragraph(f"DNI: {persona.dni}", font_size=Decimal(12)))
    layout.add(Paragraph(f"Edad: {persona.edad} años", font_size=Decimal(12)))
    layout.add(Paragraph(f"Total de turnos: {persona_data['total_turnos']}", font_size=Decimal(12)))
    layout.add(Paragraph(" "))

    # Tabla de turnos
    turnos = persona_data["turnos"]

    if turnos:
        tabla = Table(number_of_rows=len(turnos) + 1, number_of_columns=4)

        # Encabezados
        tabla.add(Paragraph("ID", font_color=HexColor("#FFFFFF"), background_color=HexColor("#27AE60")))
        tabla.add(Paragraph("Fecha", font_color=HexColor("#FFFFFF"), background_color=HexColor("#27AE60")))
        tabla.add(Paragraph("Hora", font_color=HexColor("#FFFFFF"), background_color=HexColor("#27AE60")))
        tabla.add(Paragraph("Estado", font_color=HexColor("#FFFFFF"), background_color=HexColor("#27AE60")))

        # Datos
        for turno in turnos:
            tabla.add(Paragraph(str(turno["id"])))
            tabla.add(Paragraph(str(turno["fecha"])))
            tabla.add(Paragraph(str(turno["hora"])))
            tabla.add(Paragraph(turno["estado"]))

        layout.add(tabla)
    else:
        layout.add(Paragraph("Esta persona no tiene turnos registrados.", font_size=Decimal(12)))

    # Generar bytes del PDF
    buffer = BytesIO()
    PDF.dumps(buffer, doc)
    return buffer.getvalue()

def generar_pdf_personas_con_min_cancelados(datos_persona: dict, min: int=5)-> bytes:
    """
    Genera un PDF con el reporte de turnos de una persona que tiene un min o mas turnos cancelados

    Recibe:
        datos_persona: Diccionario con lista de personas con su contador de turnos y sus turnos asignados
    Retorna:
        bytes: Contenido del PDF generado
    """
 
    documento = Document()
    pagina = Page()
    documento.add_page(pagina)
    disenio = SingleColumnLayout(pagina)

    #Titulo del PDF
    disenio.add(Paragraph(
        f"reporte de personas con un mínimo de {min} turnos cancelados".capitalize(),
        font_size=Decimal(20),
        font_color=HexColor("#27AE60")
    ))
    for personas_reportadas in datos_persona:


        #Informacion de la persona
        persona = personas_reportadas["persona"]
        disenio.add(Paragraph(f"Nombre: {persona.nombre}", font_size=Decimal(16)))
        disenio.add(Paragraph(f"DNI: {persona.dni}", font_size=Decimal(12)))
        disenio.add(Paragraph(f"Edad: {persona.edad} años", font_size=Decimal(12)))
        disenio.add(Paragraph(f"Total de turnos cancelados: {personas_reportadas["turnos_cancelados_contador"]}", font_size=Decimal(12), padding_bottom=Decimal(30), font_color=HexColor("#FF0000")))

        #Tabla de turnos
        turnos = personas_reportadas["turnos_cancelados_detalle"]
        tabla = Table(number_of_rows=len(turnos)+1, number_of_columns=4)

        #Encabezados
        encabezados=["ID", "Fecha", "Hora", "Estado"]
        for encabezado in encabezados:
            celda_encabezado = TableCell(Paragraph(encabezado, font_color=HexColor("#FFFFFF")), background_color=HexColor("#71BE91"), padding_left=Decimal(10), padding_top=Decimal(5), padding_bottom=Decimal(5))
            tabla.add(celda_encabezado)
        
        #Datos del turno
        for turno in turnos:
            celda_id = TableCell(Paragraph(str(turno["id"])), background_color=HexColor("#D9F7F7"), padding_left=Decimal(10), padding_top=Decimal(5), padding_bottom=Decimal(5))
            celda_fecha = TableCell(Paragraph(str(turno["fecha"])), background_color=HexColor("#D9F7F7"), padding_left=Decimal(10), padding_top=Decimal(5), padding_bottom=Decimal(5))
            celda_hora = TableCell(Paragraph(str(turno["hora"])), background_color=HexColor("#D9F7F7"), padding_left=Decimal(10), padding_top=Decimal(5), padding_bottom=Decimal(5))
            celda_estado = TableCell(Paragraph(str(turno["hora"])), background_color=HexColor("#D9F7F7"), padding_left=Decimal(10), padding_top=Decimal(5), padding_bottom=Decimal(5))
            tabla.add(celda_id)
            tabla.add(celda_fecha)
            tabla.add(celda_hora)
            tabla.add(celda_estado)

        disenio.add(tabla)

    #Generar bytes del PDF
    buffer = BytesIO()
    PDF.dumps(buffer, documento)
    return buffer.getvalue()

def generar_pdf_turnos_confirmados_desde_hasta(datos_reporte: dict, fecha_desde: date, fecha_hasta: date, pag: int, por_pag: int):
    """
    Genera un PDF con el reporte de turnos confirmados entre dos fechas

    Recibe:
        datos_reporte: Diccionario de lista de turnos, cantidad de registros y metadata de páginas
    Retorna:
        bytes: Contenido del PDF generado
    """
    documento = Document()
    pagina = Page()
    documento.add_page(pagina)
    disenio = SingleColumnLayout(pagina)

    #Titulo del PDF
    disenio.add(Paragraph(
        f"reporte de turnos confirmados entre {fecha_desde} y {fecha_hasta}".capitalize(),
        font_size=Decimal(20),
        font_color=HexColor("#0713B8")
    ))
    #Data de los registros encontrados
    cant_turnos = datos_reporte["total_registros"]
    disenio.add(Paragraph(f"Total de turnos confirmados: {cant_turnos}", font_size=Decimal(12), padding_bottom=Decimal(10), font_color=HexColor("#FF0000")))
    disenio.add(Paragraph(f"Se muestran {por_pag} de registros de la página {pag}",font_size=Decimal(10), padding_bottom=Decimal(30), font_color=HexColor("#000000")))


    #Tabla de turnos
    turnos = datos_reporte["turnos"]
    tabla = Table(number_of_rows=len(turnos)+1, number_of_columns=3)


    #Encabezados
    encabezados=["ID", "Fecha", "Hora"]
    for encabezado in encabezados:
            celda_encabezado = TableCell(Paragraph(encabezado, font_color=HexColor("#FFFFFF")), background_color=HexColor("#71BE91"), padding_left=Decimal(10), padding_top=Decimal(5), padding_bottom=Decimal(5))
            tabla.add(celda_encabezado)

    for turno in turnos:
        celda_id = TableCell(Paragraph(str(turno["id"])), background_color=HexColor("#D9F7F7"), padding_left=Decimal(10), padding_top=Decimal(5), padding_bottom=Decimal(5))
        celda_fecha = TableCell(Paragraph(str(turno["fecha"])), background_color=HexColor("#D9F7F7"), padding_left=Decimal(10), padding_top=Decimal(5), padding_bottom=Decimal(5))
        celda_hora = TableCell(Paragraph(str(turno["hora"])), background_color=HexColor("#D9F7F7"), padding_left=Decimal(10), padding_top=Decimal(5), padding_bottom=Decimal(5))
        tabla.add(celda_id)
        tabla.add(celda_fecha)
        tabla.add(celda_hora)

    disenio.add(tabla)

    #Generar bytes del PDF
    buffer = BytesIO()
    PDF.dumps(buffer, documento)
    return buffer.getvalue()

def generar_pdf_personas_estado(datos_reporte: dict, estado: bool):
    """
    Genera un PDF con el reporte de personas con estado habilitado (true) o deshabilitado (false)

    Recibe:
        datos_reporte: Diccionario de personas
    Retorna:
        bytes: Contenido del PDF generado
    """
    documento = Document()
    pagina = Page()
    documento.add_page(pagina)
    disenio = SingleColumnLayout(pagina)

    #Titulo del PDF
    disenio.add(Paragraph(
        f"reporte de personas con estado {'habilitado' if estado else 'deshabilitado'}".capitalize(),
        font_size=Decimal(20),
        font_color=HexColor("#0713B8")
    ))
    cant_registros = len(datos_reporte)
    disenio.add(Paragraph(
        f"cantidad de personas con estado {'habilitado' if estado else 'deshabilitado'}: {cant_registros}".capitalize(), 
        font_size=Decimal(14), 
        font_color=HexColor("#27AE60") if estado else HexColor("#E01515")
    ))
    #Tabla de personas
    tabla = Table(number_of_rows=cant_registros+1, number_of_columns=4)

    #Encabezados
    encabezados=["Nombre", "DNI", "Telefono", "Edad"]
    for encabezado in encabezados:
        celda_encabezado = TableCell(Paragraph(encabezado, font_color=HexColor("#FFFFFF")), background_color=HexColor("#71BE91"), padding_left=Decimal(10), padding_top=Decimal(5), padding_bottom=Decimal(5))
        tabla.add(celda_encabezado)
    #Datos por persona
    for persona in datos_reporte:
        celda_nombre = TableCell(Paragraph(str(persona.nombre)), background_color=HexColor("#D9F7F7"), padding_left=Decimal(10), padding_top=Decimal(5), padding_bottom=Decimal(5))
        celda_dni = TableCell(Paragraph(str(persona.dni)), background_color=HexColor("#D9F7F7"), padding_left=Decimal(10), padding_top=Decimal(5), padding_bottom=Decimal(5))
        celda_telefono = TableCell(Paragraph(str(persona.telefono)), background_color=HexColor("#D9F7F7"), padding_left=Decimal(10), padding_top=Decimal(5), padding_bottom=Decimal(5))
        celda_edad = TableCell(Paragraph(str(persona.edad)), background_color=HexColor("#D9F7F7"), padding_left=Decimal(10), padding_top=Decimal(5), padding_bottom=Decimal(5))
        tabla.add(celda_nombre)
        tabla.add(celda_dni)
        tabla.add(celda_telefono)
        tabla.add(celda_edad)

    disenio.add(tabla)

    #Generar bytes del PDF
    buffer = BytesIO()
    PDF.dumps(buffer, documento)
    return buffer.getvalue()