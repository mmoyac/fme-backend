from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.database import get_db
from database.models import Role, MenuItem, User
from routers.auth import get_current_active_user
from schemas.auth import MenuItem as MenuItemSchema

router = APIRouter()

@router.get("/fix-menu")
def fix_menu_pedidos(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint temporal para verificar y corregir el menú de pedidos
    """
    if not current_user.role or current_user.role.nombre.lower() != 'admin':
        raise HTTPException(status_code=403, detail="Solo administradores pueden ejecutar esta acción")
    
    result = {
        "status": "success",
        "actions": [],
        "users": [],
        "roles": []
    }
    
    try:
        # 1. Verificar si existe el item "Pedidos"
        pedidos_menu = db.query(MenuItem).filter(MenuItem.nombre == "Pedidos").first()
        
        if not pedidos_menu:
            pedidos_menu = MenuItem(
                nombre="Pedidos",
                href="/admin/pedidos", 
                icon="🛒",
                orden=2
            )
            db.add(pedidos_menu)
            db.commit()
            db.refresh(pedidos_menu)
            result["actions"].append("Menu 'Pedidos' creado")
        else:
            result["actions"].append(f"Menu 'Pedidos' existe: {pedidos_menu.href}")
        
        # 2. Verificar y corregir roles
        roles = db.query(Role).all()
        
        for role in roles:
            role_info = {
                "nombre": role.nombre,
                "menus_antes": [menu.nombre for menu in role.menus],
                "acciones": []
            }
            
            # Si es admin, administrador o vendedor, asegurar que tiene acceso a Pedidos
            if role.nombre.lower() in ['admin', 'administrador', 'vendedor']:
                menu_names = [menu.nombre for menu in role.menus]
                if "Pedidos" not in menu_names:
                    role.menus.append(pedidos_menu)
                    db.commit()
                    role_info["acciones"].append("Agregado acceso a 'Pedidos'")
            
            role_info["menus_despues"] = [menu.nombre for menu in role.menus]
            result["roles"].append(role_info)
        
        # 3. Información de usuarios
        users = db.query(User).filter(User.is_active == True).all()
        
        for user in users:
            user_info = {
                "email": user.email,
                "nombre": user.nombre_completo,
                "role": user.role.nombre if user.role else "Sin rol",
                "menu_count": len(user.role.menus) if user.role else 0,
                "tiene_pedidos": "Pedidos" in [menu.nombre for menu in user.role.menus] if user.role else False
            }
            result["users"].append(user_info)
            
    except Exception as e:
        db.rollback()
        result["status"] = "error"
        result["error"] = str(e)
        
    return result


@router.get("/menu-status")
def get_menu_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtener estado actual del menú para debugging
    """
    result = {
        "current_user": {
            "email": current_user.email,
            "role": current_user.role.nombre if current_user.role else None,
            "menus": [{"nombre": menu.nombre, "href": menu.href, "icon": menu.icon} 
                     for menu in current_user.role.menus] if current_user.role else []
        },
        "all_menu_items": [],
        "all_roles": []
    }
    
    # Todos los menús disponibles
    all_menus = db.query(MenuItem).order_by(MenuItem.orden).all()
    for menu in all_menus:
        result["all_menu_items"].append({
            "nombre": menu.nombre,
            "href": menu.href,
            "icon": menu.icon,
            "orden": menu.orden
        })
    
    # Todos los roles y sus menús
    roles = db.query(Role).all()
    for role in roles:
        result["all_roles"].append({
            "nombre": role.nombre,
            "menus": [menu.nombre for menu in role.menus]
        })
    
    return result