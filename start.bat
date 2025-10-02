@echo off
echo Starting OJ System...
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

echo Docker is running...
echo.

REM Start Docker containers
echo Starting Docker containers...
docker-compose up -d

if errorlevel 1 (
    echo Error: Failed to start containers.
    pause
    exit /b 1
)

echo.
echo Containers started successfully!
echo.
echo Waiting for database to be ready...
timeout /t 10 /nobreak >nul

echo.
echo Running database migrations...
docker-compose exec -T web python manage.py migrate

echo.
echo Creating superuser (if needed)...
echo You can skip this step if superuser already exists.
docker-compose exec web python manage.py createsuperuser

echo.
echo Collecting static files...
docker-compose exec -T web python manage.py collectstatic --noinput

echo.
echo ========================================
echo OJ System is ready!
echo.
echo Web: http://localhost:8000
echo Admin: http://localhost:8000/admin
echo API Docs: http://localhost:8000/api/docs
echo ========================================
echo.
echo Press any key to view logs...
pause >nul

docker-compose logs -f


