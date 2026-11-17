# Spec Delta

## Purpose

Centro de capacitación con lecciones interactivas por módulo del sistema, visible solo para usuarios autenticados y limitado a los módulos que su tenant tiene contratados.

## ADDED Requirements

### Requirement: Acceso solo autenticado
El sistema SHALL exigir una sesión válida para consultar el índice de capacitación y el contenido de cualquier lección. Ningún contenido de capacitación SHALL quedar accesible por una URL pública sin autenticación.

#### Scenario: Sin sesión
- **WHEN** se pide el índice o una lección sin token o con un token inválido o expirado
- **THEN** el sistema responde 401 y no entrega contenido

#### Scenario: Usuario inactivo
- **WHEN** un usuario desactivado pide el índice o una lección
- **THEN** el sistema rechaza la solicitud igual que el resto de la API autenticada

### Requirement: Índice filtrado por módulos contratados
El sistema SHALL devolver un índice con las secciones de capacitación que el usuario puede ver: la sección `general` y cada módulo contratado por su tenant que tenga lecciones. Cada sección incluye clave, nombre y lecciones ordenadas con slug, título y descripción.

#### Scenario: Tenant con inventario contratado
- **WHEN** un usuario de un tenant con el módulo `inventario` pide el índice
- **THEN** el índice incluye la sección `inventario` con sus lecciones en el orden del manifiesto

#### Scenario: Módulo no contratado
- **WHEN** un usuario de un tenant sin el módulo `produccion` pide el índice
- **THEN** el índice no incluye la sección `produccion` aunque tenga lecciones

#### Scenario: Módulo contratado sin lecciones
- **WHEN** el tenant tiene contratado un módulo que todavía no tiene lecciones
- **THEN** ese módulo no aparece en el índice

#### Scenario: Sección general
- **WHEN** cualquier usuario autenticado pide el índice y existen lecciones en `general`
- **THEN** el índice incluye la sección `general`, sin importar los módulos contratados

### Requirement: Entrega del contenido de una lección
El sistema SHALL entregar el HTML de una lección identificada por módulo y slug solo si el módulo es `general` o está contratado por el tenant del usuario. Si no, responde 403.

#### Scenario: Lección de módulo contratado
- **WHEN** un usuario con `inventario` contratado pide la lección `inventario/conteo`
- **THEN** el sistema responde 200 con el HTML de la lección

#### Scenario: Lección de módulo no contratado
- **WHEN** un usuario sin `cobranza` contratado pide una lección de `cobranza`
- **THEN** el sistema responde 403 y no entrega contenido

#### Scenario: Lección inexistente
- **WHEN** se pide un slug que no está en el manifiesto del módulo
- **THEN** el sistema responde 404

### Requirement: Solo se sirven lecciones declaradas
El sistema SHALL servir únicamente lecciones declaradas en el manifiesto de un módulo conocido. Cualquier módulo o slug con caracteres fuera de `[a-z0-9_-]`, o que intente salir de la carpeta de contenido, SHALL rechazarse sin leer archivos del disco.

#### Scenario: Intento de path traversal
- **WHEN** se pide una lección con módulo o slug como `../main` o `..%2F.env`
- **THEN** el sistema responde 404 y no lee ningún archivo fuera del catálogo

#### Scenario: Módulo desconocido
- **WHEN** se pide una lección de un módulo que no existe en el sistema
- **THEN** el sistema responde 404

### Requirement: Superadmin ve todo
Un superadmin en modo plataforma (sin tenant impersonado) SHALL ver el índice completo y poder abrir cualquier lección, para revisar el contenido. Si está impersonando un tenant, ve lo mismo que vería ese tenant.

#### Scenario: Superadmin sin tenant
- **WHEN** un superadmin sin impersonar pide el índice
- **THEN** el índice incluye todas las secciones que tienen lecciones

### Requirement: Visualización aislada en el backoffice
El backoffice SHALL mostrar cada lección en un contexto aislado, de modo que el script de la lección se ejecute pero no pueda leer la sesión del usuario, el almacenamiento ni el DOM del backoffice, ni hacer llamadas autenticadas a la API.

#### Scenario: Lección interactiva
- **WHEN** el usuario abre una lección con un quiz
- **THEN** el quiz funciona (responde a clics y muestra resultados) dentro del visor

#### Scenario: Script de la lección intenta leer la sesión
- **WHEN** el script de una lección intenta acceder al almacenamiento o al documento del backoffice
- **THEN** el acceso falla y el token del usuario no queda expuesto

### Requirement: Índice de capacitación en el backoffice
El backoffice SHALL ofrecer una sección de capacitación que liste las secciones y lecciones del índice entregado por la API y permita abrir cada lección. Si la API responde 403 o 404 al abrir una lección, muestra un mensaje en lugar del visor.

#### Scenario: Navegación
- **WHEN** un usuario entra a la sección de capacitación
- **THEN** ve las secciones permitidas con sus lecciones y puede abrir cualquiera

#### Scenario: Enlace directo a una lección no permitida
- **WHEN** un usuario abre la URL de una lección de un módulo no contratado
- **THEN** el backoffice muestra un mensaje de acceso no disponible y no muestra contenido
