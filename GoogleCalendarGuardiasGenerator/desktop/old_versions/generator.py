import csv
from datetime import datetime, timedelta
import os

def leer_tecnicos():
    """Lee la lista de técnicos desde tecnicos.txt"""
    archivo_tecnicos = "tecnicos.txt"
    
    if not os.path.exists(archivo_tecnicos):
        print(f"ERROR: No se encuentra el archivo '{archivo_tecnicos}'")
        print(f"Por favor, crea un archivo 'tecnicos.txt' con un nombre de técnico por línea.")
        input("Presiona Enter para salir...")
        exit(1)
    
    nombres = []
    try:
        with open(archivo_tecnicos, 'r', encoding='utf-8') as f:
            for linea in f:
                nombre = linea.strip()
                if nombre:  # Ignorar líneas vacías
                    nombres.append(nombre)
    except Exception as e:
        print(f"ERROR al leer el archivo '{archivo_tecnicos}': {e}")
        input("Presiona Enter para salir...")
        exit(1)
    
    if not nombres:
        print(f"ERROR: El archivo '{archivo_tecnicos}' está vacío o no contiene nombres válidos.")
        input("Presiona Enter para salir...")
        exit(1)
    
    print(f"\n✓ Se han cargado {len(nombres)} técnicos desde '{archivo_tecnicos}':")
    for i, nombre in enumerate(nombres, 1):
        print(f"  {i}. {nombre}")
    
    return nombres

def leer_festivos():
    """Lee la lista de festivos desde festivos.txt"""
    archivo_festivos = "festivos.txt"
    festivos = {}  # {fecha: anotacion}
    
    if not os.path.exists(archivo_festivos):
        print(f"\n⚠️ ADVERTENCIA: No se encuentra el archivo '{archivo_festivos}'")
        print(f"No se generarán guardias para festivos.")
        return festivos
    
    try:
        with open(archivo_festivos, 'r', encoding='utf-8') as f:
            for num_linea, linea in enumerate(f, 1):
                linea = linea.strip()
                if not linea:  # Ignorar líneas vacías
                    continue
                
                # Parsear: dd/mm/aaaa o dd/mm/aaaa,anotación
                partes = linea.split(',', 1)
                fecha_str = partes[0].strip()
                anotacion = partes[1].strip() if len(partes) > 1 else ""
                
                try:
                    fecha = datetime.strptime(fecha_str, "%d/%m/%Y").date()
                    festivos[fecha] = anotacion
                except ValueError:
                    print(f"  ⚠️ Línea {num_linea}: Formato de fecha inválido '{fecha_str}' (se ignora)")
    except Exception as e:
        print(f"ERROR al leer el archivo '{archivo_festivos}': {e}")
        input("Presiona Enter para salir...")
        exit(1)
    
    if festivos:
        print(f"\n✓ Se han cargado {len(festivos)} festivos desde '{archivo_festivos}':")
        for fecha, anotacion in sorted(festivos.items()):
            if anotacion:
                print(f"  {fecha.strftime('%d/%m/%Y')} - {anotacion}")
            else:
                print(f"  {fecha.strftime('%d/%m/%Y')}")
    else:
        print(f"\n⚠️ El archivo '{archivo_festivos}' está vacío.")
    
    return festivos

def pedir_fecha(mensaje):
    """Pide una fecha en formato DD/MM/AAAA"""
    while True:
        fecha_str = input(mensaje + " (formato DD/MM/AAAA): ")
        try:
            fecha = datetime.strptime(fecha_str, "%d/%m/%Y").date()
            return fecha
        except ValueError:
            print("Formato de fecha inválido. Inténtalo de nuevo.")

def encontrar_sabado_anterior(fecha):
    """Encuentra el sábado anterior o igual a la fecha dada"""
    dias_hasta_sabado = (fecha.weekday() - 5) % 7
    return fecha - timedelta(days=dias_hasta_sabado)

def encontrar_sabado_siguiente(fecha):
    """Encuentra el sábado siguiente o igual a la fecha dada"""
    dias_hasta_sabado = (5 - fecha.weekday()) % 7
    if dias_hasta_sabado == 0 and fecha.weekday() == 5:
        return fecha
    return fecha + timedelta(days=dias_hasta_sabado if dias_hasta_sabado > 0 else 7)

def asignar_tecnico_festivo(fecha, festivos, guardias_fin_semana, guardias_ya_asignadas, tecnicos):
    """
    Determina a qué técnico asignar un festivo según su proximidad al fin de semana.
    
    Reglas:
    - Lunes/Martes: técnico del fin de semana ANTERIOR
    - Jueves/Viernes: técnico del fin de semana SIGUIENTE
    - Miércoles: sin asignar (???)
    - NO se puede asignar a un técnico que ya tiene guardia en los 2 días previos
    """
    dia_semana = fecha.weekday()  # 0=Lunes, 1=Martes, ..., 6=Domingo
    
    # Sábado o Domingo ya están cubiertos en guardias de fin de semana
    if dia_semana in [5, 6]:
        return None
    
    # Miércoles: sin asignar
    if dia_semana == 2:
        return "???"
    
    # Función auxiliar para verificar si un técnico ya tiene guardia reciente
    def tiene_guardia_reciente(tecnico, fecha_actual, guardias_asignadas):
        """Verifica si el técnico tiene guardia en los 2 días previos a fecha_actual"""
        for i in range(1, 3):  # Verificar 1 y 2 días antes
            fecha_verificar = fecha_actual - timedelta(days=i)
            # Buscar en todas las guardias asignadas
            for guardia_fecha_inicio, guardia_fecha_fin, guardia_tecnico in guardias_asignadas:
                if guardia_tecnico == tecnico:
                    # Verificar si fecha_verificar está dentro del rango de la guardia
                    if guardia_fecha_inicio <= fecha_verificar <= guardia_fecha_fin:
                        return True
        return False
    
    tecnico_sugerido = None
    
    # Lunes o Martes: fin de semana ANTERIOR
    if dia_semana in [0, 1]:
        sabado_anterior = encontrar_sabado_anterior(fecha - timedelta(days=1))
        tecnico_sugerido = guardias_fin_semana.get(sabado_anterior)
    
    # Jueves o Viernes: fin de semana SIGUIENTE
    if dia_semana in [3, 4]:
        sabado_siguiente = encontrar_sabado_siguiente(fecha)
        tecnico_sugerido = guardias_fin_semana.get(sabado_siguiente)
    
    # Verificar si el técnico sugerido tiene guardia reciente
    if tecnico_sugerido and tiene_guardia_reciente(tecnico_sugerido, fecha, guardias_ya_asignadas):
        # El técnico sugerido ya tiene guardia reciente, buscar alternativa
        print(f"    ⚠️ {tecnico_sugerido} ya tiene guardia reciente, buscando alternativa...")
        
        # Buscar el siguiente técnico en la rotación que no tenga guardia reciente
        indice_actual = tecnicos.index(tecnico_sugerido) if tecnico_sugerido in tecnicos else 0
        for i in range(len(tecnicos)):
            indice_siguiente = (indice_actual + i + 1) % len(tecnicos)
            tecnico_alternativo = tecnicos[indice_siguiente]
            if not tiene_guardia_reciente(tecnico_alternativo, fecha, guardias_ya_asignadas):
                print(f"    ✓ Asignando a {tecnico_alternativo} en su lugar")
                return tecnico_alternativo
        
        # Si todos tienen guardia reciente (caso extremo), devolver el sugerido
        print(f"    ⚠️ Todos los técnicos tienen guardias recientes, asignando a {tecnico_sugerido}")
        return tecnico_sugerido
    
    return tecnico_sugerido

# ============ PROGRAMA PRINCIPAL ============

print("=" * 60)
print("  GENERADOR DE GUARDIAS - GOOGLE CALENDAR")
print("=" * 60)

# Leer archivos
tecnicos = leer_tecnicos()
festivos = leer_festivos()

# Pedir fechas
print("\n" + "=" * 60)
fecha_inicio = pedir_fecha("\n¿Fecha de inicio del rango?")
fecha_fin = pedir_fecha("¿Fecha de fin del rango?")

if fecha_fin < fecha_inicio:
    print("\nERROR: La fecha de fin debe ser posterior a la fecha de inicio.")
    input("Presiona Enter para salir...")
    exit(1)

print(f"\n✓ Generando guardias desde {fecha_inicio.strftime('%d/%m/%Y')} hasta {fecha_fin.strftime('%d/%m/%Y')}")

# Encontrar el primer sábado del rango
primer_sabado = encontrar_sabado_siguiente(fecha_inicio)
if primer_sabado > fecha_fin:
    print("\nERROR: No hay ningún fin de semana en el rango especificado.")
    input("Presiona Enter para salir...")
    exit(1)

print(f"✓ Primer fin de semana: {primer_sabado.strftime('%d/%m/%Y')} (sábado)")

# Generar guardias de fin de semana (sábado-domingo)
guardias_fin_semana = {}  # {sabado: tecnico}
fecha_sabado = primer_sabado
indice_tecnico = 0

print("\n" + "=" * 60)
print("ASIGNACIÓN DE GUARDIAS FIN DE SEMANA:")
print("=" * 60)

while fecha_sabado <= fecha_fin:
    tecnico = tecnicos[indice_tecnico]
    guardias_fin_semana[fecha_sabado] = tecnico
    
    domingo = fecha_sabado + timedelta(days=1)
    print(f"  {fecha_sabado.strftime('%d/%m/%Y')} - {domingo.strftime('%d/%m/%Y')} → {tecnico}")
    
    indice_tecnico = (indice_tecnico + 1) % len(tecnicos)
    fecha_sabado += timedelta(weeks=1)

# Generar guardias de festivos
guardias_festivos = []  # [(fecha, tecnico, anotacion, cuenta_para_rotacion)]

# Lista para rastrear todas las guardias asignadas (incluye fin de semana)
# Formato: [(fecha_inicio, fecha_fin, tecnico), ...]
guardias_asignadas = []

# Añadir guardias de fin de semana al tracker
for fecha_sabado, tecnico in guardias_fin_semana.items():
    domingo = fecha_sabado + timedelta(days=1)
    guardias_asignadas.append((fecha_sabado, domingo, tecnico))

if festivos:
    print("\n" + "=" * 60)
    print("ASIGNACIÓN DE GUARDIAS FESTIVOS:")
    print("=" * 60)
    
    for fecha, anotacion in sorted(festivos.items()):
        # Solo procesar festivos dentro del rango
        if fecha < fecha_inicio or fecha > fecha_fin:
            continue
        
        dia_semana = fecha.weekday()
        
        # Ignorar sábados y domingos (ya están cubiertos)
        if dia_semana in [5, 6]:
            print(f"  {fecha.strftime('%d/%m/%Y')} - Ya cubierto en guardia de fin de semana (ignorado)")
            continue
        
        tecnico_asignado = asignar_tecnico_festivo(fecha, festivos, guardias_fin_semana, guardias_asignadas, tecnicos)
        
        if tecnico_asignado == "???":
            print(f"  {fecha.strftime('%d/%m/%Y')} (Miércoles) → ??? (sin asignar)")
            guardias_festivos.append((fecha, "???", anotacion, False))
        elif tecnico_asignado:
            dia_nombre = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"][dia_semana]
            print(f"  {fecha.strftime('%d/%m/%Y')} ({dia_nombre}) → {tecnico_asignado}")
            guardias_festivos.append((fecha, tecnico_asignado, anotacion, True))
            # Añadir esta guardia al tracker
            guardias_asignadas.append((fecha, fecha, tecnico_asignado))
        if dia_semana in [5, 6]:
            print(f"  {fecha.strftime('%d/%m/%Y')} - Ya cubierto en guardia de fin de semana (ignorado)")
            continue
        
        tecnico_asignado = asignar_tecnico_festivo(fecha, festivos, guardias_fin_semana)
        
        if tecnico_asignado == "???":
            print(f"  {fecha.strftime('%d/%m/%Y')} (Miércoles) → ??? (sin asignar)")
            guardias_festivos.append((fecha, "???", anotacion, False))
        elif tecnico_asignado:
            dia_nombre = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"][dia_semana]
            print(f"  {fecha.strftime('%d/%m/%Y')} ({dia_nombre}) → {tecnico_asignado}")
            guardias_festivos.append((fecha, tecnico_asignado, anotacion, True))

# Crear archivo CSV
nombre_archivo = "guardias-support.csv"
print("\n" + "=" * 60)
print(f"Generando archivo '{nombre_archivo}'...")
print("=" * 60)

# Combinar todas las guardias en una lista para ordenarlas cronológicamente
todas_guardias = []

# Añadir guardias de fin de semana (sábado-domingo)
for fecha_sabado, tecnico in guardias_fin_semana.items():
    if fecha_sabado <= fecha_fin:
        domingo = fecha_sabado + timedelta(days=1)
        todas_guardias.append({
            'fecha_inicio': fecha_sabado,
            'fecha_fin': domingo,
            'tecnico': tecnico,
            'subject': f"Guardia - {tecnico}"
        })

# Añadir guardias de festivos
for fecha, tecnico, anotacion, _ in guardias_festivos:
    if anotacion:
        subject = f"Guardia {anotacion} - {tecnico}"
    else:
        subject = f"Guardia - {tecnico}"
    
    todas_guardias.append({
        'fecha_inicio': fecha,
        'fecha_fin': fecha,
        'tecnico': tecnico,
        'subject': subject
    })

# Ordenar todas las guardias por fecha de inicio
todas_guardias.sort(key=lambda x: x['fecha_inicio'])

# Escribir el CSV con todas las guardias ordenadas
with open(nombre_archivo, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file, delimiter=',')
    writer.writerow([
        "Subject", "Start Date", "Start Time", "End Date", "End Time",
        "All Day Event", "Description", "Location", "Private"
    ])
    
    for guardia in todas_guardias:
        writer.writerow([
            guardia['subject'],
            guardia['fecha_inicio'].strftime("%Y-%m-%d"),
            "00:00:00",
            guardia['fecha_fin'].strftime("%Y-%m-%d"),
            "23:59:59",
            "False",
            "",
            "",
            "False"
        ])

print(f"\n✅ Archivo '{nombre_archivo}' generado correctamente.")
print(f"   - {len(guardias_fin_semana)} guardias de fin de semana")
print(f"   - {len(guardias_festivos)} guardias de festivos")
print(f"   - Total: {len(guardias_fin_semana) + len(guardias_festivos)} eventos")
print("\n" + "=" * 60)
input("\nPresiona Enter para salir...")

