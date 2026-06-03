PWD := $(shell pwd)
SERVICE_FILE := healthcheck.service
PY_FILE := src/healthcheck.py
ENV_FILE := .env
PATH_PY := $(PWD)/$(PY_FILE)
PATH_ENV := $(PWD)/$(ENV_FILE)
USER := $(shell whoami)

.PHONY: release install clean

.DEFAULT_GOAL := release

release:
	@echo '[Unit]' 										>  $(SERVICE_FILE)
	@echo 'Description=Healthcheck service to know if the system is alive' 	>> $(SERVICE_FILE)
	@echo 'After=network.target' 						>> $(SERVICE_FILE)
	@echo '' 											>> $(SERVICE_FILE)
	@echo '[Service]' 									>> $(SERVICE_FILE)
	@echo 'Type=simple' 								>> $(SERVICE_FILE)
	@echo 'User=$(USER)'								>> $(SERVICE_FILE)
	@echo 'WorkingDirectory=$(PWD)' 					>> $(SERVICE_FILE)
	@echo 'ExecStart=/usr/bin/python3 $(PATH_PY)' 						>> $(SERVICE_FILE)
	@echo 'Restart=on-failure' 							>> $(SERVICE_FILE)
	@echo 'RestartSec=30s' 								>> $(SERVICE_FILE)
	@echo 'ExecStop=/bin/kill -s SIGINT $$MAINPID' 		>> $(SERVICE_FILE)
	@echo 'TimeoutStopSec=30' 							>> $(SERVICE_FILE)
	@echo 'KillMode=control-group' 						>> $(SERVICE_FILE)
	@echo 'KillSignal=SIGINT' 							>> $(SERVICE_FILE)
	@echo '' 											>> $(SERVICE_FILE)
	@echo '[Install]' 									>> $(SERVICE_FILE)
	@echo 'WantedBy=multi-user.target'					>> $(SERVICE_FILE)

install: 
	@echo "Setting file permissions..."
	@chmod +x $(PY_FILE)
	@chmod 644 $(ENV_FILE)
	@echo "Installing the service..."
	@make release
	@cp $(SERVICE_FILE) /etc/systemd/system/
	@systemctl daemon-reload
	@systemctl enable $(SERVICE_FILE)
	@echo "Service installed. Run 'sudo systemctl start $(SERVICE_FILE)' to start."

clean:
	@rm -rf $(SERVICE_FILE) __pycache__/
