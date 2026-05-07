# ==========================================
# 🛠️ IOT BACKEND MANAGEMENT TOOL
# ==========================================

BACKEND_DIR = d:/FastAPI/datn/backend
PYTHON = $(BACKEND_DIR)/har_env/Scripts/python.exe
PIP = $(BACKEND_DIR)/har_env/Scripts/pip.exe

.PHONY: help install dev test migrate-init migrate-check

help:
	@echo "Sử dụng: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  install       Cài đặt dependencies từ requirements.txt"
	@echo "  dev           Chạy server FastAPI (Hot-reload)"
	@echo "  test          Chạy unit tests với pytest"
	@echo "  migrate-init  Khởi tạo Alembic cho database PostgreSQL"
	@echo "  migrate-check Kiểm tra trạng thái migration"

install:
	$(PIP) install -r $(BACKEND_DIR)/requirements.txt

dev:
	cd $(BACKEND_DIR) && $(PYTHON) -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	cd $(BACKEND_DIR) && pytest

migrate-init:
	cd $(BACKEND_DIR) && alembic init alembic

migrate-check:
	cd $(BACKEND_DIR) && alembic current
