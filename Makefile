# KOMHunter - Commandes de développement
# Usage: make [cible]

.PHONY: install install-backend install-frontend dev dev-backend dev-frontend help
.PHONY: start-backend start-frontend stop stop-backend stop-frontend reboot
.PHONY: docker-up docker-down

# PIDs / logs (à la racine du repo)
BACKEND_PID  := .backend.pid
FRONTEND_PID := .frontend.pid
BACKEND_LOG  := .backend.log
FRONTEND_LOG := .frontend.log
BUN_BIN      := $(HOME)/.bun/bin

help:
	@echo "KOMHunter - Commandes disponibles:"
	@echo ""
	@echo "  Installation:"
	@echo "    make install          Installer backend + frontend"
	@echo "    make install-backend  Créer venv et installer deps Python"
	@echo "    make install-frontend Installer deps frontend (Bun)"
	@echo ""
	@echo "  Démarrer / Arrêter (processus en arrière-plan):"
	@echo "    make start-backend    Démarrer le backend (port 8000)"
	@echo "    make start-frontend  Démarrer le frontend (port 3000)"
	@echo "    make stop             Arrêter backend + frontend"
	@echo "    make stop-backend    Arrêter le backend"
	@echo "    make stop-frontend   Arrêter le frontend"
	@echo "    make reboot          Arrêter front+back puis redémarrer les deux"
	@echo ""
	@echo "  Dev (bloquant, un par terminal):"
	@echo "    make dev             Affiche comment lancer backend + frontend"
	@echo "    make dev-backend     Lancer le backend (uvicorn, blocant)"
	@echo "    make dev-frontend    Lancer le frontend (bun dev, blocant)"
	@echo ""
	@echo "  Docker:"
	@echo "    make docker-up       Démarrer avec Docker Compose"
	@echo "    make docker-down     Arrêter Docker Compose"

install: install-backend install-frontend

install-backend:
	@echo ">>> Backend: création venv et installation..."
	cd backend && python3 -m venv venv
	cd backend && ./venv/bin/pip install -r requirements.txt
	@echo ">>> Backend: copiez backend/.env.example vers backend/.env et configurez Strava."

install-frontend:
	@echo ">>> Frontend: bun install..."
	@export PATH="$(BUN_BIN):$$PATH"; cd frontend && bun install
	@echo ">>> Frontend: optionnel — copiez frontend/.env.example vers frontend/.env.local"

# --- Start / Stop (processus en arrière-plan) ---

start-backend:
	@if lsof -ti:8000 >/dev/null 2>&1; then echo ">>> Backend déjà en cours sur le port 8000."; exit 1; fi
	@if [ ! -f backend/venv/bin/uvicorn ]; then echo ">>> Backend: venv manquant. Lancez: make install-backend"; exit 1; fi
	@echo ">>> Démarrage du backend (port 8000)..."
	@cd backend && nohup ./venv/bin/uvicorn app.main:app --reload --port 8000 >> ../$(BACKEND_LOG) 2>&1 & echo $$! > ../$(BACKEND_PID)
	@sleep 2
	@if lsof -ti:8000 >/dev/null 2>&1; then echo ">>> Backend démarré. Logs: $(BACKEND_LOG)"; else echo ">>> Erreur au démarrage, voir $(BACKEND_LOG)"; exit 1; fi

start-frontend:
	@if lsof -ti:3000 >/dev/null 2>&1; then echo ">>> Frontend déjà en cours sur le port 3000."; exit 1; fi
	@export PATH="$(BUN_BIN):$$PATH"; command -v bun >/dev/null 2>&1 || { echo ">>> Bun non trouvé. Installez: https://bun.sh"; exit 1; }
	@echo ">>> Démarrage du frontend (port 3000)..."
	@export PATH="$(BUN_BIN):$$PATH"; cd frontend && nohup bun run dev >> ../$(FRONTEND_LOG) 2>&1 & echo $$! > ../$(FRONTEND_PID)
	@sleep 3
	@if lsof -ti:3000 >/dev/null 2>&1; then echo ">>> Frontend démarré. Logs: $(FRONTEND_LOG)"; else echo ">>> Erreur au démarrage, voir $(FRONTEND_LOG)"; exit 1; fi

stop-backend:
	@if lsof -ti:8000 >/dev/null 2>&1; then \
		lsof -ti:8000 | xargs kill -9 2>/dev/null; \
		rm -f $(BACKEND_PID); \
		echo ">>> Backend arrêté (port 8000)."; \
	else \
		echo ">>> Aucun backend en cours sur le port 8000."; \
	fi

stop-frontend:
	@if lsof -ti:3000 >/dev/null 2>&1; then \
		lsof -ti:3000 | xargs kill -9 2>/dev/null; \
		rm -f $(FRONTEND_PID); \
		echo ">>> Frontend arrêté (port 3000)."; \
	else \
		echo ">>> Aucun frontend en cours sur le port 3000."; \
	fi

stop: stop-backend stop-frontend
	@echo ">>> Tout arrêté."

reboot: stop-backend stop-frontend
	@echo ">>> Redémarrage backend + frontend..."
	@sleep 1
	@$(MAKE) start-backend
	@$(MAKE) start-frontend
	@echo ""
	@echo ">>> App: http://localhost:3000 — API: http://localhost:8000"

dev:
	@echo "Lancez dans deux terminaux:"
	@echo ""
	@echo "  Terminal 1 (backend):"
	@echo "    cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000"
	@echo ""
	@echo "  Terminal 2 (frontend):"
	@echo "    cd frontend && bun run dev"
	@echo ""
	@echo "Puis ouvrez http://localhost:3000"

dev-backend:
	cd backend && ./venv/bin/uvicorn app.main:app --reload --port 8000

dev-frontend:
	@export PATH="$(BUN_BIN):$$PATH"; cd frontend && bun run dev

docker-up:
	docker-compose up -d
	@echo "App: http://localhost:3000 — API: http://localhost:8000"

docker-down:
	docker-compose down
