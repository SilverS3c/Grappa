all:
	pip install --no-cache-dir -r requirements.txt
	sed -i "s+ExecStart=.*$+ExecStart=`which python3` `pwd`/Grappa.py -i `hostname` -b $(PLUGIN)+g" grappa.service
	cp grappa.service /etc/systemd/system/grappa.service