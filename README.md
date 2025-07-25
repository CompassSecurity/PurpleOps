<h1 align="center">
  <br>
  <a href="https://purpleops.app"><img src="static/images/logo.png" alt="PurpleOps Logo" width="200"></a>
  <br>
  PurpleOps
  <br>
</h1>

<h4 align="center">An open-source self-hosted purple team management web application.</h4>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/Licence-blue?logo=unlicense&logoColor=white">
  <a href="https://docs.purpleops.app"><img src="https://img.shields.io/badge/Docs-blue?logo=readthedocs&logoColor=white">
</p>

<p align="center">
  <img src="static/images/demo.gif">
</p>

## Key Features

* Template engagements and testcases
* Framework friendly
* Role-based Access Control & MFA
* Inbuilt DOCX reporting + custom template support

How PurpleOps is different:

* No attribution needed
* Hackable, no "no-reversing" clauses
* No over complications with tomcat, redis, manual database transplanting and an obtuce permission model

## Installation

### Default

```bash
# Clone this repository
$ git clone https://github.com/CyberCX-STA/PurpleOps

# Go into the repository
$ cd PurpleOps

# Alter PurpleOps settings (if you want to customize anything but should work out the box)
$ nano .env

# Run the app with docker (add `-d` to run in background)
$ sudo docker compose up

# PurpleOps should now by available on http://localhost:5000, it is recommended to add a reverse proxy such as nginx or Apache in front of it if you want to expose this to the outside world.
```

<details>
  <summary><h3>Kali</h3></summary>
  
  ```bash
  # Install docker-compose
  sudo apt install docker-compose -y
  
  # Clone this repository
  $ git clone https://github.com/CyberCX-STA/PurpleOps
  
  # Go into the repository
  $ cd PurpleOps
  
  # Alter PurpleOps settings (if you want to customize anything but should work out the box)
  $ nano .env
  
  # Run the app with docker (add `-d` to run in background)
  $ sudo docker-compose up
  
  # PurpleOps should now by available on http://localhost:5000, it is recommended to add a reverse proxy such as nginx or Apache in front of it if you want to expose this to the outside world.
  ```
</details>

<details>
  <summary><h3>Manual</h3></summary>
  
  ```bash
  # Alternatively
  $ sudo docker run --name mongodb -d -p 27017:27017 mongo
  $ pip3 install -r requirements.txt
  $ python3 seeder.py
  $ python3 purpleops.py
  ```
</details>

<details>
  <summary><h3>NGINX Reverse Proxy + Certbot</h3></summary>

  Replace 2x `purpleops.example.com` with your FQDN and ensure your box is open internet-wide on 80/443.
  
  ```bash
  sudo apt install nginx certbot python3-certbot-nginx -y
  sudo nano /etc/nginx/sites-available/purpleops # Paste below file
  sudo ln -s /etc/nginx/sites-available/purpleops /etc/nginx/sites-enabled/
  sudo certbot --nginx -d purpleops.example.com
  sudo service nginx restart
  ```

  ```
  server {
    listen 80;
    server_name purpleops.example.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
  }
  ```
</details>

<details>
  <summary><h3>IP Whitelisting with ufw</h3></summary>
  
  ```bash
  sudo apt install ufw -y
  sudo ufw allow 22
  sudo ufw deny 80
  sudo ufw deny 443
  sudo ufw insert 1 allow from 100.100.100.100/24 to any port 443
  sudo ufw enable
  ```
</details>

## Compass Security Fork
The Compass Security fork includes fixes and new features!

### Updated Dependencies
The Python dependencies (e.g. Flask) were updated to the latest versions.

### Restructured Test Case Form and Flow-Based Approach
We have redesigned the test case form to prioritise the elements that we believe are important during a purple team engagement. 
<br> Is there anything missing? Please let us know — we are eager to hear how other analysts approach Purple Teaming engagements.

<br>Moreover, we have implemented a flow-based approach to facilitate collaboration with the Blue Team.
<img width="2061" height="612" alt="image" src="https://github.com/user-attachments/assets/60e1d78d-cb73-4c10-ae16-9b8f296e59a1" />

#### Waiting Blue:
This signals to the blue team that input is expected from their side. Once the required information has been added, the Blue team can set the state to 'Waiting Red'.
Users with the 'Blue' role can only edit a test case if it is in the 'Waiting Blue' or 'Waiting Red' state.

#### Waiting Red:
This signals to the red team that the blue team has finished adding their details to the test case. The red team can then check that all the required information is present. If so, the state can be changed to 'Complete'.

#### Complete:
The blue team cannot make any more changes to the test case.


### Pytests
We have created pytests for each route. This makes it easy to check whether the application has been affected by any changes made to it.
<br><br>Note: We are still missing security checks (e.g. RBAC) and application logic checks, so if you would like to contribute, we would be glad to merge your pull request!

### Dark Mode
Enjoy PurpleOps in dark mode. To enable this, go to the settings menu.
<img width="2063" height="1041" alt="darkmode_overview" src="https://github.com/user-attachments/assets/1b2870a6-319a-4ca6-8366-f5a8e638842e" />
<img width="2066" height="1120" alt="darkmode_testcase" src="https://github.com/user-attachments/assets/056c721a-2a00-473f-8cbe-39537a843491" />

### Test Case History
The Test Case History allows you to view previous saved versions of the test case. This feature is only available after an initial save, not after an import. Please note that evidence files are not stored.
![test_case_history](https://github.com/user-attachments/assets/b15c3799-a73b-4845-9ec3-fe9f04f3b7a4)

### Restore Deleted Test Cases
You can now restore deleted test cases (requires page reload).
![test_case_restore](https://github.com/user-attachments/assets/a66ba8b0-854f-436b-9602-9c2a244e3ded)

### Test Case Knowlege Base and Variables File
We added the option to add an knowledge base MD file for each TPP. You can find an example here:
https://github.com/CompassSecurity/PurpleOps/blob/main/custom/testcaseskb/T1087_002.md

To view the KB click on the "compass" icon in the test case:
![test_case_kb](https://github.com/user-attachments/assets/f06ed191-2812-4259-9317-ed6d865a729e)

The KB also enables you to set placeholders for frequently used strings. For instance, you could define {{TARGET_DOMAIN_USER}} as a placeholder in an MD file for a command.
```
net user {{TARGET_DOMAIN_USER}} /domain 
```
Define a JSON file which contains all your placeholders and the coresponding text:
```
{
"DOMAIN_NAME" : "testlab.local",
"LOWPRIVILEGED_DOMAIN_USER" : "tmassie",
"TARGET_DOMAIN_USER" : "administrator",
"DC_IP" : "10.0.1.10"
}
```
Upload the JSON file to PurpleOps using your browser. The values will be stored in your session storage (cleared after browser is closed). Use the toggle in the test case KB to replace the placeholders with real data.
![test_case_kb_variables](https://github.com/user-attachments/assets/547f4a21-a043-47a9-8be4-c9a176a23029)


## Credits
- PurpleOps https://github.com/CyberCX-STA/PurpleOps
- Atomic Red Team [(LICENSE)](https://github.com/redcanaryco/atomic-red-team/blob/master/LICENSE.txt) for sample commands
- [CyberCX](https://cybercx.com.au/) for foundational support

## License
Apache





