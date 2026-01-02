"""
Script para probar las nuevas métricas de caja en el dashboard.
Ejecutar: docker-compose exec backend python scripts/test_dashboard_caja.py
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_dashboard_metricas():
    session = requests.Session()

    # 1. Login
    print("🔐 Logueando como admin...")
    login_data = {
        "username": "admin@fme.cl",
        "password": "admin"
    }
    resp = session.post(f"{BASE_URL}/api/auth/token", data=login_data)
    if resp.status_code != 200:
        print(f"❌ Error login: {resp.text}")
        return
    
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login exitoso\n")

    # 2. Probar dashboard principal (con métricas de caja integradas)
    print("📊 Obteniendo estadísticas del dashboard principal...")
    resp = session.get(f"{BASE_URL}/api/dashboard/estadisticas", headers=headers)
    if resp.status_code == 200:
        stats = resp.json()
        print("✅ Dashboard principal obtenido")
        print(f"   - Ventas del día: ${stats['ventas']['hoy']}")
        print(f"   - Ventas del mes: ${stats['ventas']['mes']}")
        print(f"   - Total clientes: {stats['total_clientes']}")
        
        if 'caja' in stats:
            caja_stats = stats['caja']
            print(f"💰 Métricas de caja integradas:")
            print(f"   - Turnos abiertos: {caja_stats['turnos_abiertos']}")
            print(f"   - Ventas de caja hoy: ${caja_stats['ventas_hoy']}")
            print(f"   - Diferencias pendientes: {caja_stats['diferencias_pendientes']}")
        else:
            print("⚠️ No se encontraron métricas de caja en el dashboard")
    else:
        print(f"❌ Error obteniendo dashboard: {resp.status_code} - {resp.text}")

    print()

    # 3. Probar endpoint específico de métricas de caja
    print("💼 Obteniendo métricas específicas de caja...")
    resp = session.get(f"{BASE_URL}/api/dashboard/metricas-caja", headers=headers)
    if resp.status_code == 200:
        metricas = resp.json()
        print("✅ Métricas de caja obtenidas")
        
        print(f"📅 Fecha consulta: {metricas['fecha_consulta']}")
        
        # Turnos abiertos
        turnos = metricas['turnos_abiertos']
        print(f"🏪 Turnos abiertos: {turnos['total']}")
        if turnos['detalle']:
            for turno in turnos['detalle']:
                print(f"   - {turno['local_nombre']}: {turno['vendedor_nombre']} "
                      f"(${turno['monto_inicial']} inicial, ${turno['ventas_acumuladas']} ventas)")
        
        # Ventas por vendedor
        vendedores = metricas['ventas_por_vendedor_hoy']
        print(f"👥 Vendedores activos hoy: {vendedores['total_vendedores_activos']}")
        if vendedores['detalle']:
            for vendedor in vendedores['detalle'][:3]:  # Top 3
                print(f"   - {vendedor['vendedor_nombre']}: "
                      f"{vendedor['num_ventas']} ventas, ${vendedor['total_ventas']}")
        
        # Diferencias de cuadre
        diferencias = metricas['diferencias_cuadre_recientes']
        print(f"⚠️ Diferencias de cuadre (últimos 7 días): {diferencias['total_con_diferencia']}")
        if diferencias['detalle']:
            for diff in diferencias['detalle'][:2]:  # Primeras 2
                tipo = "📈" if diff['tipo_diferencia'] == 'sobrante' else "📉"
                print(f"   {tipo} {diff['local_nombre']} - {diff['vendedor_nombre']}: "
                      f"${diff['diferencia']} ({diff['tipo_diferencia']})")
        
        # Resumen de operaciones
        operaciones = metricas['resumen_operaciones_30d']
        print(f"📋 Total operaciones (30d): {operaciones['total_operaciones']}")
        for op in operaciones['por_tipo']:
            print(f"   - {op['tipo']}: {op['cantidad']} operaciones, ${op['total_monto']}")
    
    else:
        print(f"❌ Error obteniendo métricas de caja: {resp.status_code} - {resp.text}")

    print("\n🎉 ¡Prueba de métricas completada!")

if __name__ == "__main__":
    test_dashboard_metricas()