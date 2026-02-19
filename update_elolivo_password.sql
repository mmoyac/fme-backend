-- Actualizar contraseña del usuario admin@elolivo.cl
UPDATE users 
SET hashed_password = '$argon2id$v=19$m=65536,t=3,p=4$IETI+R/jPMfYW4sRYizF2A$SzdsBrC1fAtjYyU7pUYc3pKPBNjCWcj1+jzN2TTOJ8g'
WHERE email = 'admin@elolivo.cl';

SELECT id, email, nombre_completo, tenant_id, is_active, LENGTH(hashed_password) as pwd_len 
FROM users 
WHERE email = 'admin@elolivo.cl';
