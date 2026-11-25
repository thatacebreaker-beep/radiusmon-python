Update the compose for ip / port to match your radiusserverinfo, own mods
* create a certs folder containing a file: 
 - radius_secret.txt (save the radius client key in here, matching the clients conf of your radius)
 - ca.pem (full chained pem)
 - computer.pem (paste your eap client authentication certificate pem)
 - computer.key (paste your eap client authentication certificate private key)

docker compose build
docker compose up -d
