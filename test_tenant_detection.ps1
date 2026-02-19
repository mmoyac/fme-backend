# Script para probar detección de tenant en desarrollo

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "  TEST DE DETECCION DE TENANT (Desarrollo)" -ForegroundColor Cyan
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""

$API_BASE = "http://localhost:8000"

# Hostnames a probar
$testCases = @(
    @{hostname="localhost"; descripcion="Localhost (default)"},
    @{hostname="masasestacion.cl"; descripcion="Dominio exacto"},
    @{hostname="www.masasestacion.cl"; descripcion="Con www (NUEVO)"},
    @{hostname="admin.masasestacion.cl"; descripcion="Subdominio admin"},
    @{hostname="elolivo.masasestacion.cl"; descripcion="Subdominio elolivo"}
)

foreach ($test in $testCases) {
    Write-Host ""
    Write-Host "Probando: $($test.hostname)" -ForegroundColor Cyan
    Write-Host "  $($test.descripcion)" -ForegroundColor Gray
    
    try {
        $response = Invoke-RestMethod `
            -Uri "$API_BASE/api/config/landing" `
            -Headers @{
                "X-Forwarded-Host" = $test.hostname
            }
        
        Write-Host "  Tenant: $($response.tenant.nombre) (ID: $($response.tenant.id))" -ForegroundColor Green
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "  ERROR: Status $statusCode" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host ""
