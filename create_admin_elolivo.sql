-- Crear usuario admin para El Olivo (tenant_id = 2)
-- La contraseña "admin" hasheada con Argon2
INSERT INTO users (email, nombre_completo, hashed_password, role_id, tenant_id, local_defecto_id)
VALUES (
    'admin@elolivo.cl',
    'Admin El Olivo',
    '$argon2id$v=19$m=65536,t=3,p=4$Yzc0ZjBlMGM4NzQ5NDA1ZmFlMDE5ODJkZWQ2ODM5ZDM$vWr8TN1aS5fAV9aNy7qZEqPqLtBXePCvFcQvfJVSFnE',
    1,  -- role_id = 1 (admin)
    2,  -- tenant_id = 2 (El Olivo)
    (SELECT id FROM locales WHERE tenant_id = 2 AND codigo = 'WEB' LIMIT 1)
);

SELECT id, email, nombre_completo, tenant_id FROM users WHERE tenant_id = 2;
