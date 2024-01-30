default: start
clean_start: clean start

VENV = venv
VBIN = $(VENV)/bin

$(VENV):
	python3 -m venv venv

	sudo chmod +x $(VBIN)/activate
	./$(VBIN)/activate
	$(VBIN)/pip install -e .

	sudo chown -R root:root $(VBIN)/python
	sudo chmod u+s $(VBIN)/python

start: $(VENV)
	@echo "Starting computer_link"
	$(VBIN)/python computer_link

clean:
	sudo rm -rf venv .venv *.egg-info {*,*/*,*/*/*}/__pycache__

clear_config: clean
	sudo rm -rf *_config.json

.PHONY: default start clean clear_config clean_start