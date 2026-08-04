$content = @'
@echo off
:: Quick start - just run the CLI
docker run -it --rm ^
    -v "%cd%/input:/app/input" ^
    -v "%cd%/output:/app/output" ^
    --env-file .env ^
    --add-host host.docker.internal:host-gateway ^
    ai-kcmedicalresearch ^
    python launcher.py
'@
$content | Out-File -FilePath "docker_quick_start.bat" -Encoding ASCII -Force