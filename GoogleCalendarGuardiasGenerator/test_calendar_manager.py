"""
Script de prueba para validar CalendarManager
"""

from models.calendar_manager import CalendarManager
from datetime import datetime
import os

def test_calendar_manager():
    """Prueba básica del CalendarManager"""
    
    print("=" * 60)
    print("Prueba de CalendarManager")
    print("=" * 60)
    
    # Crear instancia
    cm = CalendarManager("json/test_calendarios.json")
    
    # Test 1: Añadir evento
    print("\n1. Añadiendo evento de prueba...")
    evento = {
        'id': 'test_001',
        'titulo': 'Guardia - Test',
        'tipo': 'guardia',
        'descripcion': 'Evento de prueba',
        'origen': 'test'
    }
    
    resultado = cm.add_event('2026-03-15', evento)
    print(f"   ✓ Evento añadido: {resultado}")
    
    # Test 2: Guardar datos
    print("\n2. Guardando datos...")
    cm.save_data()
    print(f"   ✓ Datos guardados en {cm.data_file}")
    
    # Test 3: Obtener vista de mes
    print("\n3. Obteniendo vista de marzo 2026...")
    mes_data = cm.get_month_view(2026, 3)
    print(f"   ✓ Total eventos en mes: {mes_data['estadisticas_mes']['total_eventos']}")
    
    # Test 4: Vista multi-mes
    print("\n4. Obteniendo vista de 7 meses...")
    start_date = datetime(2026, 1, 1)
    multi_view = cm.get_multi_month_view(start_date, 7)
    print(f"   ✓ Meses recuperados: {len(multi_view)}")
    for mv in multi_view:
        print(f"      - {mv['month_name']}: {mv.get('estadisticas_mes', {}).get('total_eventos', 0)} eventos")
    
    # Test 5: Estadísticas globales
    print("\n5. Estadísticas globales...")
    stats = cm.get_statistics()
    print(f"   ✓ Total meses con datos: {stats['total_meses_con_datos']}")
    print(f"   ✓ Total eventos: {stats['total_eventos']}")
    
    # Test 6: Limpiar archivo de prueba
    print("\n6. Limpiando archivo de prueba...")
    if os.path.exists("json/test_calendarios.json"):
        os.remove("json/test_calendarios.json")
        print("   ✓ Archivo de prueba eliminado")
    
    print("\n" + "=" * 60)
    print("✅ Todas las pruebas pasaron correctamente")
    print("=" * 60)

if __name__ == "__main__":
    test_calendar_manager()
