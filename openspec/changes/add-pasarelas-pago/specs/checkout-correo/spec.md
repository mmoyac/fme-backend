## ADDED Requirements

### Requirement: Validación del correo del checkout
El sistema SHALL validar el correo del cliente de la tienda en tres niveles: formato real, dominio que existe y recibe correo (consulta DNS con timeout de 4 s) y sugerencia de corrección de errores de tipeo en dominios comunes. Si el DNS no responde, NO SHALL bloquear la compra (solo valida el formato). La validación SHALL estar disponible en `POST /api/pedidos/validar-email` y SHALL repetirse al crear el pedido.

#### Scenario: Dominio inexistente
- **WHEN** el cliente ingresa un correo cuyo dominio no existe o no recibe correos
- **THEN** el sistema lo rechaza con un mensaje en español y, si corresponde, sugiere el dominio correcto

#### Scenario: Dominio mal escrito que sí existe
- **WHEN** el cliente ingresa `nombre@gmial.com` (dominio con MX registrado por terceros)
- **THEN** el correo se acepta como válido, pero se sugiere `nombre@gmail.com`
- **AND** la landing exige corregirlo o confirmar que está bien antes de continuar

### Requirement: Verificación del correo con código
Antes de crear un pedido de la tienda, el cliente SHALL verificar su correo con un código de 6 dígitos enviado por correo (n8n, webhook `verificacion-email`). El código SHALL vencer a los 10 minutos, servir una sola vez y permitir máximo 5 intentos; solo su HMAC SHALL guardarse. Los envíos SHALL limitarse a 1 por minuto y 5 por hora por correo, y a 15 por hora por IP. Un código correcto SHALL entregar un token firmado de 30 días ligado al tenant y al correo.

#### Scenario: Código correcto
- **WHEN** el cliente ingresa el código vigente
- **THEN** recibe el token y la landing lo guarda en el navegador por 30 días

#### Scenario: Código incorrecto
- **WHEN** el cliente ingresa un código incorrecto
- **THEN** el sistema responde 400 indicando los intentos restantes y, al agotarlos, anula el código

#### Scenario: Reenvío inmediato
- **WHEN** el cliente pide otro código antes de 60 segundos
- **THEN** el sistema responde 429 indicando cuánto esperar

### Requirement: Pedido de la tienda solo con correo verificado
`POST /api/pedidos/` SHALL exigir un `email_token` válido para el tenant y el correo del pedido. En desarrollo, el backend SHALL además escribir el código en el log para poder probar sin correo.

#### Scenario: Sin token o token de otro correo
- **WHEN** se intenta crear un pedido sin token o con el token emitido para otro correo
- **THEN** el sistema responde 400 "Verifica tu correo con el código que te enviamos…" y no crea el pedido
