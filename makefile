all: .build.start_sensors

.build.python-smbus:
	sudo apt install python-smbus
	@date > .build.python-smbus

.build.python-pip: .build.python-smbus
	sudo apt install python-pip
	@date > .build.python-pip

.build.cp-service: .build.python-pip
	sudo cp sensors.service /etc/systemd/system/sensors.service
	@date > .build.cp-service

.build.install-paho-mqtt: .build.cp-service
	pip install --user paho-mqtt
	@date > .build.install-paho-mqtt

.build.daemon-reload: .build.install-paho-mqtt
	sudo systemctl daemon-reload
	@date > .build.daemon-reload

.build.enable_sensors: .build.daemon-reload
	sudo systemctl enable sensors
	@date > .build.enable_sensors

.build.start_sensors: .build.enable_sensors
	sudo systemctl start sensors
	@date > .build.start_sensors


clean:
	rm .build* || true
