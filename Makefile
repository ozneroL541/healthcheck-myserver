PWD := $(shell pwd)
SERVICE_FILE := healthcheck.service
PY_FILE := healthcheck.py
ENV_FILE := .env
PATH_PY := $(PWD)/$(PY_FILE)
PATH_ENV := $(PWD)/$(ENV_FILE)

.PHONY: release install clean

.DEFAULT_GOAL := release

release:
	@echo '[Unit]' 										>  $(SERVICE_FILE)
	@echo 'Description = Healthcheck service to know if the system is alive' 	>> $(SERVICE_FILE)
	@echo 'After = network.target' 						>> $(SERVICE_FILE)
	@echo '' 											>> $(SERVICE_FILE)
	@echo '[Service]' 									>> $(SERVICE_FILE)
	@echo 'Type = simple' 								>> $(SERVICE_FILE)
	@echo 'User = root' 								>> $(SERVICE_FILE)
	@echo 'EnvironmentFile = $(PATH_ENV)' 				>> $(SERVICE_FILE)
	@echo 'WorkingDirectory = $(PATH_PY)' 				>> $(SERVICE_FILE)
	@echo 'ExecStart = $(PATH_PY)' 						>> $(SERVICE_FILE)
	@echo 'Restart = on-failure' 						>> $(SERVICE_FILE)
	@echo 'RestartSec = 30s' 							>> $(SERVICE_FILE)
	@echo 'ExecStop = /bin/kill -s SIGINT $MAINPID' 	>> $(SERVICE_FILE)
	@echo 'TimeoutStopSec = 30' 						>> $(SERVICE_FILE)
	@echo 'KillMode = control-group' 					>> $(SERVICE_FILE)
	@echo 'KillSignal = SIGINT' 						>> $(SERVICE_FILE)
	@echo '' 											>> $(SERVICE_FILE)
	@echo '[Install]' 									>> $(SERVICE_FILE)
	@echo 'WantedBy = multi-user.target'				>> $(SERVICE_FILE)

install: 
	@echo "Installing the service..."
	@make release
	@cp $(SERVICE_FILE) /etc/systemd/system/
	@systemctl daemon-reload
	@systemctl enable $(SERVICE_FILE)

clean:
	@rm -f $(SERVICE_FILE)
