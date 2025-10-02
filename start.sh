#!/bin/bash

echo "Starting OJ System..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

echo "Docker is running..."
echo ""

# Start Docker containers
echo "Starting Docker containers..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "Error: Failed to start containers."
    exit 1
fi

echo ""
echo "Containers started successfully!"
echo ""
echo "Waiting for database to be ready..."
sleep 10

echo ""
echo "Running database migrations..."
docker-compose exec -T web python manage.py migrate

echo ""
echo "Collecting static files..."
docker-compose exec -T web python manage.py collectstatic --noinput

echo ""
echo "========================================"
echo "OJ System is ready!"
echo ""
echo "Web: http://localhost:8000"
echo "Admin: http://localhost:8000/admin"
echo "API Docs: http://localhost:8000/api/docs"
echo "========================================"
echo ""
echo "Press Ctrl+C to stop viewing logs..."
echo ""

docker-compose logs -f


