param(
    [Parameter(Mandatory=$true)]
    [string]$Domain,
    
    [Parameter(Mandatory=$false)]
    [string]$Email = "info@lexastech.cl",
    
    [Parameter(Mandatory=$false)]
    [string]$VPS = "168.231.96.205"
)

function Write-Success { param($msg) Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Info { param($msg) Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-Warn { param($msg) Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Err { param($msg) Write-Host "[ERROR] $msg" -ForegroundColor Red }

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host " Configuracion SSL/Nginx para Tenant Multi-Tenant" -ForegroundColor Cyan
Write-Host "=====================================================================" -ForegroundColor Cyan
Write-Host ""

if ($Domain -notmatch '^[a-zA-Z0-9\-\.]+\.[a-zA-Z]+$') {
    Write-Err "Formato de dominio invalido: $Domain"
    Write-Info "Ejemplo valido: bigschool.lexastech.cl"
    exit 1
}

$AdminDomain = "admin.$Domain"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ConfFile = Join-Path $ScriptDir "$Domain.conf"
$TempPath = "/tmp/$Domain.conf"
$NginxPath = "/root/docker/nginx-proxy/conf.d/$Domain.conf"

Write-Info "Dominio Landing:   $Domain"
Write-Info "Dominio Backoffice: $AdminDomain"
Write-Info "Email Certbot:     $Email"
Write-Info "VPS:               $VPS"
Write-Host ""

Write-Host "=====================================================================" -ForegroundColor Yellow
Write-Info "Paso 1/6: Verificando configuracion DNS..."
Write-Host "=====================================================================" -ForegroundColor Yellow

try {
    $dnsCheck1 = Resolve-DnsName -Name $Domain -Type A -ErrorAction Stop
    $dnsCheck2 = Resolve-DnsName -Name $AdminDomain -Type A -ErrorAction Stop
    
    $ip1 = $dnsCheck1.IPAddress
    $ip2 = $dnsCheck2.IPAddress
    
    Write-Success "$Domain -> $ip1"
    Write-Success "$AdminDomain -> $ip2"
    
    if ($ip1 -ne $VPS -or $ip2 -ne $VPS) {
        Write-Warn "Los dominios no apuntan a $VPS"
        $continue = Read-Host "Deseas continuar de todas formas? (s/n)"
        if ($continue -ne "s") {
            Write-Info "Configuracion cancelada"
            exit 0
        }
    }
} catch {
    Write-Err "No se pudo resolver DNS para los dominios"
    Write-Info "Configura el DNS primero:"
    Write-Host "  $Domain        A    $VPS" -ForegroundColor Yellow
    Write-Host "  $AdminDomain   A    $VPS" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Yellow
Write-Info "Paso 2/6: Generando configuracion nginx..."
Write-Host "=====================================================================" -ForegroundColor Yellow

$nginxContent = @"
server {
    listen 80;
    server_name $Domain;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://`$host`$request_uri;
    }
}

server {
    listen 443 ssl;
    http2 on;
    server_name $Domain;

    ssl_certificate /etc/letsencrypt/live/$Domain/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$Domain/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://masas_estacion_frontend:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade `$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host `$host;
        proxy_set_header X-Real-IP `$remote_addr;
        proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto `$scheme;
        proxy_set_header X-Forwarded-Host `$host;
        proxy_cache_bypass `$http_upgrade;
    }
}

server {
    listen 80;
    server_name $AdminDomain;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://`$host`$request_uri;
    }
}

server {
    listen 443 ssl;
    http2 on;
    server_name $AdminDomain;

    ssl_certificate /etc/letsencrypt/live/$Domain/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$Domain/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    location / {
        proxy_pass http://masas_estacion_backoffice:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade `$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host `$host;
        proxy_set_header X-Real-IP `$remote_addr;
        proxy_set_header X-Forwarded-For `$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto `$scheme;
        proxy_set_header X-Forwarded-Host `$host;
        proxy_cache_bypass `$http_upgrade;
    }
}
"@

[System.IO.File]::WriteAllText("$ConfFile", $nginxContent)
Write-Success "Archivo generado: $ConfFile"
Write-Host ""

Write-Host "=====================================================================" -ForegroundColor Yellow
Write-Info "Paso 3/6: Copiando configuracion al VPS..."
Write-Host "=====================================================================" -ForegroundColor Yellow
Write-Warn "Se te pedira la contrasena del VPS..."

# Limpiar archivos antiguos primero
ssh "root@$VPS" "rm -f $TempPath $NginxPath"

scp $ConfFile "root@${VPS}:${TempPath}"
if ($LASTEXITCODE -ne 0) {
    Write-Err "Error al copiar archivo al VPS"
    exit 1
}

Write-Success "Archivo copiado al VPS"

# Instalar configuracion (ignorar error si falla por certificados faltantes)
ssh "root@$VPS" "cp $TempPath $NginxPath"
Write-Info "Archivo instalado en nginx (los bloques HTTPS fallarán hasta obtener certificados)"
Write-Host ""

Write-Host "=====================================================================" -ForegroundColor Yellow
Write-Info "Paso 4/6: Obteniendo certificados SSL..."
Write-Host "=====================================================================" -ForegroundColor Yellow
Write-Warn "Este paso puede tomar 30-60 segundos..."

# Usar echo '1' para seleccionar automáticamente la primera cuenta de certbot
$certbotResult = ssh "root@$VPS" "echo '1' | docker exec -i nginx_certbot certbot certonly --webroot -w /var/www/certbot --email $Email --agree-tos -d $Domain -d $AdminDomain 2>&1"
Write-Host $certbotResult

if ($certbotResult -match 'Successfully received certificate') {
    Write-Success "Certificados SSL obtenidos exitosamente"
} elseif ($certbotResult -match 'Certificate not yet due for renewal') {
    Write-Success "Certificados ya existen y son validos"
} else {
    Write-Err "Error al obtener certificado SSL"
    Write-Info "Revisa los logs arriba para mas detalles"
    exit 1
}
Write-Host ""

Write-Host "=====================================================================" -ForegroundColor Yellow
Write-Info "Paso 5/6: Instalando configuracion y recargando nginx con SSL..."
Write-Host "=====================================================================" -ForegroundColor Yellow

ssh "root@$VPS" "cp $TempPath $NginxPath ; docker exec nginx_proxy nginx -t ; docker exec nginx_proxy nginx -s reload"

if ($LASTEXITCODE -ne 0) {
    Write-Err "Error al recargar nginx con SSL"
    exit 1
}

Write-Success "Nginx recargado con HTTPS activo"
Write-Host ""

Write-Host "=====================================================================" -ForegroundColor Yellow
Write-Info "Paso 6/6: Verificando funcionamiento..."
Write-Host "=====================================================================" -ForegroundColor Yellow

Start-Sleep -Seconds 3

try {
    $response1 = Invoke-WebRequest -Uri "https://$Domain" -Method Head -TimeoutSec 10 -UseBasicParsing -SkipCertificateCheck 2>$null
    Write-Success "Landing responde en HTTPS: https://$Domain"
} catch {
    Write-Warn "Landing no responde aun (puede tomar unos segundos)"
}

try {
    $response2 = Invoke-WebRequest -Uri "https://$AdminDomain" -Method Head -TimeoutSec 10 -UseBasicParsing -SkipCertificateCheck 2>$null
    Write-Success "Backoffice responde en HTTPS: https://$AdminDomain"
} catch {
    Write-Warn "Backoffice no responde aun (puede tomar unos segundos)"
}

Write-Host ""
Write-Host "=====================================================================" -ForegroundColor Green
Write-Host " Configuracion completada exitosamente" -ForegroundColor Green
Write-Host "=====================================================================" -ForegroundColor Green
Write-Host ""

Write-Info "URLs configuradas:"
Write-Host "  Landing:    https://$Domain" -ForegroundColor Cyan
Write-Host "  Backoffice: https://$AdminDomain" -ForegroundColor Cyan
Write-Host ""

Write-Success "Listo!"
