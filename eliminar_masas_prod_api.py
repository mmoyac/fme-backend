#!/usr/bin/env python
"""
Script automatizado para eliminar todos los datos de Masas Estación (Tenant 1) en PRODUCCIÓN.
Usa la API REST para conectarse a producción.
⚠️ USAR CON EXTREMA PRECAUCIÓN - PRODUCCIÓN
"""

import requests
import sys

# Configuración
API_URL = "https://api.masasestacion.cl"
TENANT_ID = 1  # Masas Estación

def autenticar():
    """Autenticarse en la API de producción."""
    print("\n🔐 Autenticando en producción...")
    login_data = {
        "username": "admin@fme.cl",
        "password": "admin"
    }
    
    try:
        resp = requests.post(f"{API_URL}/api/auth/token", data=login_data)
        resp.raise_for_status()
        token = resp.json()["access_token"]
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        print("✅ Autenticación exitosa")
        return headers
    except Exception as e:
        print(f"❌ ERROR en autenticación: {e}")
        sys.exit(1)


def listar_y_contar(endpoint, headers, nombre):
    """Listar y contar registros de un endpoint."""
    try:
        # Agregar limit=10000 para evitar paginación default de 100
        separator = '&' if '?' in endpoint else '?'
        url = f"{API_URL}{endpoint}{separator}limit=10000"
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            data = resp.json()
            return data, len(data)
        else:
            print(f"⚠️  Error al listar {nombre}: {resp.status_code}")
            return [], 0
    except Exception as e:
        print(f"❌ Error al listar {nombre}: {e}")
        return [], 0


def eliminar_pedidos(headers):
    """Eliminar todos los pedidos del tenant."""
    pedidos, count = listar_y_contar("/api/pedidos/", headers, "pedidos")
    
    if count == 0:
        print("✅ No hay pedidos para eliminar")
        return 0
    
    print(f"\n🗑️  Eliminando {count} pedidos...")
    eliminados = 0
    
    for pedido in pedidos:
        pedido_id = pedido.get('id')
        numero = pedido.get('numero_pedido', 'N/A')
        
        try:
            # Intentar eliminar directamente
            resp = requests.delete(f"{API_URL}/api/pedidos/{pedido_id}", headers=headers)
            
            if resp.status_code in [200, 204]:
                eliminados += 1
                print(f"   ✓ Pedido #{numero} eliminado")
            elif resp.status_code == 404:
                print(f"   ⚠️  Pedido #{numero} ya no existe")
            else:
                # Intentar parsear JSON solo si hay contenido
                try:
                    error = resp.json().get('detail', resp.text) if resp.text else resp.status_code
                except:
                    error = resp.text if resp.text else resp.status_code
                print(f"   ❌ Error eliminando pedido #{numero}: {error}")
        except Exception as e:
            print(f"   ❌ Excepción eliminando pedido #{numero}: {e}")
    
    print(f"✅ {eliminados} pedidos eliminados")
    return eliminados


def eliminar_compras(headers):
    """Eliminar todas las compras del tenant (incluidas las RECIBIDAS)."""
    try:
        response = requests.get(f"{API_URL}/api/compras/?limit=10000", headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"❌ Error obteniendo compras: {response.status_code}")
            return 0
        
        compras = response.json()
        count = len(compras)
        
        if count == 0:
            print("✅ No hay compras para eliminar")
            return 0
        
        print(f"\n🗑️  Eliminando {count} compras (forzado)...")
        eliminados = 0
        
        for compra in compras:
            compra_id = compra.get('id')
            numero_doc = compra.get('numero_documento', 'N/A')
            estado = compra.get('estado', 'N/A')
            
            try:
                # Usar force=true para eliminar incluso compras RECIBIDAS
                resp = requests.delete(
                    f"{API_URL}/api/compras/{compra_id}?force=true", 
                    headers=headers, 
                    timeout=30
                )
                
                if resp.status_code in [200, 204]:
                    eliminados += 1
                    print(f"   ✓ Compra #{numero_doc} ({estado}) eliminada")
                elif resp.status_code == 404:
                    print(f"   ⚠️  Compra #{numero_doc} ya no existe")
                else:
                    try:
                        error = resp.json().get('detail', resp.text) if resp.text else resp.status_code
                    except:
                        error = resp.text if resp.text else resp.status_code
                    print(f"   ❌ Error eliminando compra #{numero_doc}: {error}")
                    
            except Exception as e:
                print(f"   ❌ Excepción eliminando compra #{numero_doc}: {e}")
                continue
        
        print(f"✅ {eliminados} compras eliminadas")
        return eliminados
        
    except Exception as e:
        print(f"❌ Error general eliminando compras: {e}")
        return 0


def eliminar_ordenes_produccion(headers):
    """Eliminar todas las órdenes de producción del tenant."""
    try:
        response = requests.get(f"{API_URL}/api/produccion/ordenes?limit=10000", headers=headers, timeout=30)
        if response.status_code != 200:
            print(f"❌ Error obteniendo órdenes de producción: {response.status_code}")
            return 0
        
        ordenes = response.json()
        count = len(ordenes)
        
        if count == 0:
            print("✅ No hay órdenes de producción para eliminar")
            return 0
        
        print(f"\n🗑️  Eliminando {count} órdenes de producción...")
        eliminados = 0
        
        for orden in ordenes:
            orden_id = orden.get('id')
            estado = orden.get('estado', 'N/A')
            fecha = orden.get('fecha_programada', 'N/A')
            
            try:
                resp = requests.delete(
                    f"{API_URL}/api/produccion/ordenes/{orden_id}", 
                    headers=headers, 
                    timeout=30
                )
                
                if resp.status_code in [200, 204]:
                    eliminados += 1
                    print(f"   ✓ Orden #{orden_id} ({estado}) eliminada")
                elif resp.status_code == 404:
                    print(f"   ⚠️  Orden #{orden_id} ya no existe")
                else:
                    try:
                        error = resp.json().get('detail', resp.text) if resp.text else resp.status_code
                    except:
                        error = resp.text if resp.text else resp.status_code
                    print(f"   ❌ Error eliminando orden #{orden_id}: {error}")
                    
            except Exception as e:
                print(f"   ❌ Excepción eliminando orden #{orden_id}: {e}")
                continue
        
        print(f"✅ {eliminados} órdenes de producción eliminadas")
        return eliminados
        
    except Exception as e:
        print(f"❌ Error general eliminando órdenes de producción: {e}")
        return 0


def eliminar_productos(headers):
    """Eliminar todos los productos del tenant."""
    productos, count = listar_y_contar("/api/productos/", headers, "productos")
    
    if count == 0:
        print("✅ No hay productos para eliminar")
        return 0
    
    print(f"\n🗑️  Eliminando {count} productos...")
    eliminados = 0
    
    for producto in productos:
        producto_id = producto.get('id')
        sku = producto.get('sku', 'N/A')
        nombre = producto.get('nombre', 'N/A')
        
        try:
            resp = requests.delete(f"{API_URL}/api/productos/{producto_id}", headers=headers)
            
            if resp.status_code in [200, 204]:
                eliminados += 1
                print(f"   ✓ Producto {sku} - {nombre} eliminado")
            elif resp.status_code == 404:
                print(f"   ⚠️  Producto {sku} ya no existe")
            else:
                # Intentar parsear JSON solo si hay contenido
                try:
                    error_detail = resp.json() if resp.text else {"detail": resp.status_code}
                    error = error_detail.get('detail', str(error_detail))
                except:
                    error = resp.text if resp.text else resp.status_code
                print(f"   ❌ Error eliminando producto {sku}: {error}")
                if resp.status_code == 500:
                    print(f"      Status Code: {resp.status_code}, Response: {resp.text[:200]}")
        except Exception as e:
            print(f"   ❌ Excepción eliminando producto {sku}: {e}")
    
    print(f"✅ {eliminados} productos eliminados")
    return eliminados


def eliminar_clientes(headers):
    """Eliminar todos los clientes del tenant."""
    clientes, count = listar_y_contar("/api/clientes/", headers, "clientes")
    
    if count == 0:
        print("✅ No hay clientes para eliminar")
        return 0
    
    print(f"\n🗑️  Eliminando {count} clientes (forzado)...")
    eliminados = 0
    
    for cliente in clientes:
        cliente_id = cliente.get('id')
        nombre = cliente.get('nombre', 'N/A')
        email = cliente.get('email', 'N/A')
        
        try:
            # Usar force=true para eliminar incluso con pedidos históricos
            resp = requests.delete(
                f"{API_URL}/api/clientes/{cliente_id}?force=true", 
                headers=headers
            )
            
            if resp.status_code in [200, 204]:
                eliminados += 1
                print(f"   ✓ Cliente {nombre} ({email}) eliminado")
            elif resp.status_code == 404:
                print(f"   ⚠️  Cliente {nombre} ya no existe")
            else:
                # Intentar parsear JSON solo si hay contenido
                try:
                    error = resp.json().get('detail', resp.text) if resp.text else resp.status_code
                except:
                    error = resp.text if resp.text else resp.status_code
                print(f"   ❌ Error eliminando cliente {nombre}: {error}")
        except Exception as e:
            print(f"   ❌ Excepción eliminando cliente {nombre}: {e}")
    
    print(f"✅ {eliminados} clientes eliminados")
    return eliminados


def resetear_secuencias(headers):
    """Resetear todas las secuencias de IDs a 1."""
    print("\n🔄 Reseteando secuencias de IDs...")
    
    try:
        resp = requests.post(
            f"{API_URL}/api/admin/reset-sequences", 
            headers=headers,
            timeout=60
        )
        
        if resp.status_code == 200:
            data = resp.json()
            resetadas = data.get('resetadas', 0)
            total = data.get('total', 0)
            errores = data.get('errores', [])
            
            print(f"✅ {resetadas}/{total} secuencias reseteadas")
            
            if errores:
                print("⚠️  Algunas secuencias tuvieron errores:")
                for error in errores[:5]:  # Mostrar solo primeros 5 errores
                    print(f"   • {error}")
            
            return resetadas
        else:
            print(f"❌ Error reseteando secuencias: {resp.status_code}")
            try:
                error = resp.json().get('detail', resp.text) if resp.text else resp.status_code
            except:
                error = resp.text if resp.text else resp.status_code
            print(f"   {error}")
            return 0
            
    except Exception as e:
        print(f"❌ Excepción reseteando secuencias: {e}")
        return 0


def resetear_inventario(headers):
    """Resetear todo el inventario a cero."""
    print("\n🗑️  Reseteando inventario...")
    
    # Obtener todos los productos
    productos, count = listar_y_contar("/api/productos/", headers, "productos")
    
    if count == 0:
        print("✅ No hay productos con inventario")
        return 0
    
    # Obtener todos los locales
    locales, locales_count = listar_y_contar("/api/locales/", headers, "locales")
    
    if locales_count == 0:
        print("⚠️  No hay locales disponibles")
        return 0
    
    reseteos = 0
    
    for producto in productos:
        producto_id = producto.get('id')
        sku = producto.get('sku', 'N/A')
        
        for local in locales:
            local_id = local.get('id')
            codigo_local = local.get('codigo', 'N/A')
            
            try:
                # Intentar resetear a cero
                resp = requests.put(
                    f"{API_URL}/api/inventario/producto/{producto_id}/local/{local_id}",
                    json={"cantidad_stock": 0},
                    headers=headers
                )
                
                if resp.status_code in [200, 201]:
                    reseteos += 1
                    print(f"   ✓ Inventario de {sku} en {codigo_local} → 0")
                elif resp.status_code == 404:
                    # No existe inventario, está bien
                    pass
                else:
                    # Intentar parsear JSON solo si hay contenido
                    try:
                        error = resp.json().get('detail', resp.text) if resp.text else resp.status_code
                    except:
                        error = resp.text if resp.text else resp.status_code
                    print(f"   ⚠️  Error reseteando {sku} en {codigo_local}: {error}")
            except Exception as e:
                print(f"   ❌ Excepción reseteando {sku} en {codigo_local}: {e}")
    
    print(f"✅ {reseteos} registros de inventario reseteados")
    return reseteos


def eliminar_precios(headers):
    """Eliminar todos los precios del tenant."""
    print("\n🗑️  Eliminando precios...")
    
    # Obtener todos los productos
    productos, count = listar_y_contar("/api/productos/", headers, "productos")
    
    if count == 0:
        print("✅ No hay productos con precios")
        return 0
    
    # Obtener todos los locales
    locales, locales_count = listar_y_contar("/api/locales/", headers, "locales")
    
    if locales_count == 0:
        print("⚠️  No hay locales disponibles")
        return 0
    
    eliminados = 0
    
    for producto in productos:
        producto_id = producto.get('id')
        sku = producto.get('sku', 'N/A')
        unidad_medida_id = producto.get('unidad_medida_id', 1)
        
        for local in locales:
            local_id = local.get('id')
            codigo_local = local.get('codigo', 'N/A')
            
            try:
                # Intentar eliminar precio
                resp = requests.delete(
                    f"{API_URL}/api/precios/producto/{producto_id}/local/{local_id}/unidad/{unidad_medida_id}",
                    headers=headers
                )
                
                if resp.status_code in [200, 204]:
                    eliminados += 1
                    print(f"   ✓ Precio de {sku} en {codigo_local} eliminado")
                elif resp.status_code == 404:
                    # No existe precio, está bien
                    pass
                else:
                    # Intentar parsear JSON solo si hay contenido
                    try:
                        error = resp.json().get('detail', resp.text) if resp.text else resp.status_code
                    except:
                        error = resp.text if resp.text else resp.status_code
                    # No mostrar error, solo continuar
                    pass
            except Exception as e:
                # No mostrar excepción, solo continuar
                pass
    
    print(f"✅ {eliminados} precios eliminados")
    return eliminados


def limpiar_dependencias_productos(headers):
    """Limpiar dependencias de productos (recetas, información nutricional, sellos)."""
    print("\n🗑️  Limpiando dependencias de productos...")
    
    # Obtener todos los productos
    productos, count = listar_y_contar("/api/productos/", headers, "productos")
    
    if count == 0:
        print("✅ No hay productos con dependencias")
        return 0
    
    limpiados = 0
    
    for producto in productos:
        producto_id = producto.get('id')
        sku = producto.get('sku', 'N/A')
        
        try:
            # 1. Eliminar información nutricional
            # Endpoint: DELETE /api/etiquetas/producto/{producto_id}/nutricional
            resp = requests.delete(
                f"{API_URL}/api/etiquetas/producto/{producto_id}/nutricional",
                headers=headers
            )
            if resp.status_code in [200, 204]:
                limpiados += 1
                print(f"   ✓ Info nutricional de {sku} eliminada")
            elif resp.status_code != 404:  # 404 = no tiene info nutricional, es OK
                print(f"   ⚠️  Info nutricional {sku}: {resp.status_code}")
        except Exception as e:
            print(f"   ⚠️  Error info nutricional {sku}: {e}")
        
        try:
            # 2. Eliminar sellos (usando POST con array vacío)
            # El endpoint POST elimina todos los sellos existentes antes de agregar nuevos
            # Endpoint: POST /api/etiquetas/producto/{producto_id}/sellos
            resp = requests.post(
                f"{API_URL}/api/etiquetas/producto/{producto_id}/sellos",
                json={"sello_ids": []},
                headers=headers
            )
            if resp.status_code in [200, 201]:
                limpiados += 1
                print(f"   ✓ Sellos de {sku} eliminados")
            elif resp.status_code != 404:  # 404 = no tiene sellos, es OK
                print(f"   ⚠️  Sellos {sku}: {resp.status_code}")
        except Exception as e:
            print(f"   ⚠️  Error sellos {sku}: {e}")
        
        try:
            # 3. Eliminar receta activa (si existe)
            # Primero GET para obtener la receta, luego DELETE
            # Endpoint GET: /api/recetas/productos/{producto_id}/receta
            # Endpoint DELETE: /api/recetas/recetas/{receta_id}
            resp_get = requests.get(
                f"{API_URL}/api/recetas/productos/{producto_id}/receta",
                headers=headers
            )
            
            if resp_get.status_code == 200:
                receta = resp_get.json()
                receta_id = receta.get('id')
                
                if receta_id:
                    resp_delete = requests.delete(
                        f"{API_URL}/api/recetas/recetas/{receta_id}",
                        headers=headers
                    )
                    
                    if resp_delete.status_code in [200, 204]:
                        limpiados += 1
                        print(f"   ✓ Receta de {sku} eliminada (ID: {receta_id})")
                    else:
                        print(f"   ⚠️  Delete receta {sku}: {resp_delete.status_code}")
            elif resp_get.status_code != 404:  # 404 = no tiene receta, es OK
                print(f"   ⚠️  Get receta {sku}: {resp_get.status_code}")
                
        except Exception as e:
            print(f"   ⚠️  Error recetas {sku}: {e}")
    
    print(f"✅ {limpiados} dependencias limpiadas")
    return limpiados


def eliminar_datos_masasestacion():
    """Elimina todos los datos del tenant Masas Estación en PRODUCCIÓN via API."""
    
    print('=' * 60)
    print('🗑️  RESET COMPLETO - MASAS ESTACIÓN (PRODUCCIÓN)')
    print('=' * 60)
    print('\n💀💀💀 PELIGRO: ESTO ES PRODUCCIÓN 💀💀💀')
    print(f'\n🌐 API: {API_URL}')
    print(f'📍 Tenant: {TENANT_ID} (Masas Estación)')
    print('\n⚠️  Este script eliminará TODO de Masas Estación:')
    print('   📋 Todos los PEDIDOS')
    print('   📦 Todos los PRODUCTOS')
    print('   👥 Todos los CLIENTES y puntos')
    print('   📊 Todo el INVENTARIO (stock → 0)')
    print('\n✅ Se mantienen (maestras):')
    print('   • Locales')
    print('   • Proveedores')
    print('   • Categorías, Unidades, Tipos')
    print('   • Usuarios y Roles')
    print('\n⚠️⚠️⚠️ ESTO ES PRODUCCIÓN - NO HAY VUELTA ATRÁS ⚠️⚠️⚠️\n')
    
    confirmacion1 = input('¿Confirmas que deseas RESETEAR PRODUCCIÓN? (SI/NO): ').strip().upper()
    
    if confirmacion1 != 'SI':
        print('\n❌ Operación cancelada')
        return
    
    confirmacion2 = input('\n⚠️⚠️⚠️ SEGUNDA CONFIRMACIÓN ⚠️⚠️⚠️\nEscribe "DELETE PRODUCTION" para continuar: ').strip()
    
    if confirmacion2 != "DELETE PRODUCTION":
        print('\n❌ Operación cancelada (confirmación incorrecta)')
        return
    
    print('\n🔄 Iniciando eliminación en PRODUCCIÓN...')
    print('=' * 60)
    
    try:
        # 1. Autenticar
        headers = autenticar()
        
        # 2. Contar registros actuales
        print("\n📊 Contando registros actuales...")
        pedidos, pedidos_count = listar_y_contar("/api/pedidos/", headers, "pedidos")
        productos, productos_count = listar_y_contar("/api/productos/", headers, "productos")
        clientes, clientes_count = listar_y_contar("/api/clientes/", headers, "clientes")
        
        # Contar órdenes de producción y compras
        try:
            resp_ordenes = requests.get(f"{API_URL}/api/produccion/ordenes?limit=10000", headers=headers, timeout=30)
            ordenes_count = len(resp_ordenes.json()) if resp_ordenes.status_code == 200 else 0
        except:
            ordenes_count = 0
            
        try:
            resp_compras = requests.get(f"{API_URL}/api/compras/?limit=10000", headers=headers, timeout=30)
            compras_count = len(resp_compras.json()) if resp_compras.status_code == 200 else 0
        except:
            compras_count = 0
        
        print(f"   📋 Pedidos: {pedidos_count}")
        print(f"   📦 Productos: {productos_count}")
        print(f"   👥 Clientes: {clientes_count}")
        print(f"   🏭 Órdenes Producción: {ordenes_count}")
        print(f"   📦 Compras: {compras_count}")
        
        total_registros = pedidos_count + productos_count + clientes_count + ordenes_count + compras_count
        
        if total_registros == 0:
            print('\n✅ No hay datos para eliminar')
            print('✅ Base de datos ya está limpia para Masas Estación')
            return
        
        print('\n⚠️  RESUMEN DE ELIMINACIÓN:')
        print(f'   💀 {pedidos_count} pedidos')
        print(f'   💀 {productos_count} productos')
        print(f'   💀 {clientes_count} clientes')
        print(f'   💀 {ordenes_count} órdenes de producción')
        print(f'   💀 {compras_count} compras')
        print(f'   💀 Inventario → 0')
        print('=' * 60)
        
        confirmacion_final = input('\n🔴 ÚLTIMA CONFIRMACIÓN: ¿Continuar? (SI/NO): ').strip().upper()
        
        if confirmacion_final != 'SI':
            print('\n❌ Operación cancelada')
            return
        
        # 3. Eliminar en orden correcto (respetando FKs)
        
        # 3.1. Eliminar pedidos primero (tienen FKs a clientes y productos)
        pedidos_eliminados = eliminar_pedidos(headers)
        
        # 3.2. Resetear inventario (antes de eliminar productos)
        inventario_reseteado = resetear_inventario(headers)
        
        # 3.3. Eliminar precios (antes de eliminar productos)
        precios_eliminados = eliminar_precios(headers)
        
        # 3.4. Limpiar dependencias de productos (recetas, info nutricional, sellos)
        dependencias_limpiadas = limpiar_dependencias_productos(headers)
        
        # 3.5. Eliminar compras (antes de productos por FK en detalles_compra)
        compras_eliminadas = eliminar_compras(headers)
        
        # 3.6. Eliminar órdenes de producción (antes de productos por FK en detalles)
        ordenes_eliminadas = eliminar_ordenes_produccion(headers)
        
        # 3.7. Eliminar productos (después de limpiar todas sus dependencias)
        productos_eliminados = eliminar_productos(headers)
        
        # 3.8. Eliminar clientes (después de pedidos, con force=true)
        clientes_eliminados = eliminar_clientes(headers)
        
        # 3.9. Resetear secuencias de IDs a 1
        secuencias_reseteadas = resetear_secuencias(headers)
        
        # 4. Resumen final
        print('\n' + '=' * 60)
        print('✅ ELIMINACIÓN COMPLETADA EN PRODUCCIÓN')
        print('=' * 60)
        print('\n📊 Resumen:')
        print(f'   ✓ {pedidos_eliminados} pedidos eliminados')
        print(f'   ✓ {inventario_reseteado} registros de inventario reseteados')
        print(f'   ✓ {precios_eliminados} precios eliminados')
        print(f'   ✓ {dependencias_limpiadas} dependencias de productos limpiadas')
        print(f'   ✓ {compras_eliminadas} compras eliminadas')
        print(f'   ✓ {ordenes_eliminadas} órdenes de producción eliminadas')
        print(f'   ✓ {productos_eliminados} productos eliminados')
        print(f'   ✓ {clientes_eliminados} clientes eliminados')
        print(f'   ✓ {secuencias_reseteadas} secuencias de IDs reseteadas')
        
        # 5. Verificación final
        print('\n🔍 Verificación final...')
        pedidos_rest, pedidos_rest_count = listar_y_contar("/api/pedidos/", headers, "pedidos")
        productos_rest, productos_rest_count = listar_y_contar("/api/productos/", headers, "productos")
        clientes_rest, clientes_rest_count = listar_y_contar("/api/clientes/", headers, "clientes")
        
        print(f'   • {pedidos_rest_count} pedidos restantes')
        print(f'   • {productos_rest_count} productos restantes')
        print(f'   • {clientes_rest_count} clientes restantes')
        
        if pedidos_rest_count == 0 and productos_rest_count == 0 and clientes_rest_count == 0:
            print('\n✅✅✅ BASE DE DATOS COMPLETAMENTE LIMPIA ✅✅✅')
        else:
            print('\n⚠️  Aún quedan algunos registros (revisar logs arriba)')
        
    except Exception as e:
        print(f'\n❌ Error durante la eliminación: {str(e)}')
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    eliminar_datos_masasestacion()
