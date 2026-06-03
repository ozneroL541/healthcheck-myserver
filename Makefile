PWD := $(shell pwd)
SERVICE_FILE := healthcheck.service
PY_FILE := src/healthcheck.py
ENV_FILE := .env
PATH_PY := $(PWD)/$(PY_FILE)
PATH_ENV := $(PWD)/$(ENV_FILE)
USER := $(shell whoami)

.PHONY: release install clean

.DEFAULT_GOAL := release

INIT_SYSTEM := $(shell cat /proc/1/comm)

sysemd_file:
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

openrc_file:
	@echo '#!/sbin/openrc-run'							>> $(SERVICE_FILE)
	@echo 'description="Healthcheck service to know if the system is alive"'	>> $(SERVICE_FILE)
	@echo 'command="/usr/bin/python3"'					>> $(SERVICE_FILE)
	@echo 'command_args="$(PATH_PY)"'					>> $(SERVICE_FILE)
	@echo 'command_user="lorenzo"'						>> $(SERVICE_FILE)
	@echo 'directory="$(PWD)"'							>> $(SERVICE_FILE)
	@echo 'pidfile="/run/healthcheck.pid"'				>> $(SERVICE_FILE)
	@echo 'respawn_delay=30'							>> $(SERVICE_FILE)
	@echo 'respawn_max=0'								>> $(SERVICE_FILE)
	@echo 'depend() {'									>> $(SERVICE_FILE)
	@echo '    need net'								>> $(SERVICE_FILE)
	@echo '}'											>> $(SERVICE_FILE)

install_systemd:
	@make sysemd_file
	@cp $(SERVICE_FILE) /etc/systemd/system/
	@systemctl daemon-reload
	@systemctl enable $(SERVICE_FILE)
	@echo "Service installed. Run 'sudo systemctl start $(SERVICE_FILE)' to start"

install_openrc:
	@make openrc_file
	@cp $(SERVICE_FILE) /etc/init.d/
	@chmod +x /etc/init.d/$(SERVICE_FILE)
	@rc-update add $(SERVICE_FILE) default
	@echo "Service installed. Run 'sudo rc-service $(SERVICE_FILE) start' to start."

install: 
	@echo "Setting file permissions..."
	@chmod +x $(PY_FILE)
	@touch $(ENV_FILE)
	@chmod 644 $(ENV_FILE)
	@echo "Installing the service..."
	@if [ "$(INIT_SYSTEM)" = "systemd" ]; then \
		echo "Detected init system: systemd"; \
		$(MAKE) install_systemd; \
	elif [ "$(INIT_SYSTEM)" = "openrc-init" ]; then \
		echo "Detected init system: openrc"; \
		$(MAKE) install_openrc; \
	else \
		echo "Unsupported init system: systemd or openrc not found"; \
		echo "$(INIT_SYSTEM) detected. Please install the service manually."; \
		exit 1; \
	fi
	
	
clean:
	@rm -rf $(SERVICE_FILE) __pycache__/
