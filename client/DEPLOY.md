# Deploying

First, download the latest build artefact. 
You can get this by going to <https://github.com/dogsbodytech/warboard/actions>, selecting the top run and downloading the item `app` from under the heading Artefacts.

Upload this to the server.
`$CLIENT_DEPLOY_DIR` should be replaced in all below snippets with where you uploaded it.


If you've already set it up once and are just updating, run the below and then stop: 

```
sudo systemctl start warboard_client
```


First, install a recent version of node.

```bash
sudo apt -y install curl
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

Create the systemd service file:

```bash
sudo nano /lib/systemd/system/warboard_client.service
```

```service
[Unit]
Description=Warboard client server
After=network.target

[Service]
Environment="HOST=127.0.0.1 REDIS_DB_NUMBER=$N"
Type=simple
User=ubuntu
ExecStart=/usr/bin/node $CLIENT_DEPLOY_DIR/index.js
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

set REDIS_DB_NUMBER to whatever the config for the python server has it as.

See <https://github.com/sveltejs/kit/tree/master/packages/adapter-node#environment-variables> for options on the server.
More should be set depending on configuration of the reverse proxy.


Refresh systemd so it picks up the file:

```bash
sudo systemctl daemon-reload
```

Start and enable (running at startup) it:

```
sudo systemctl start warboard_client
sudo systemctl enable warboard_client
```

The server should now be accessible at 127.0.0.1:3000

You must now configure the reverse proxy & https per your normal processes.