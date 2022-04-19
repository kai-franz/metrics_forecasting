# from https://cmudb.slack.com/archives/C02TZ1D1ARM/p1647386748305369

# Set a password for this user
 sudo passwd ubuntu

# Install postgresql-14, pip, and openjdk
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo apt update

sudo apt -y install python3-pip openjdk-17-jdk
sudo apt -y install libpq-dev
pip3 install psycopg2-binary
sudo apt -y install xmlstarlet

sudo apt -y install postgresql-14

# Drop the existing default cluster
sudo pg_dropcluster --stop 14 main

# Make the mount point, format the disk, mount it
sudo mkdir -p /mnt/postgresql
sudo chmod 0777 /mnt/postgresql
sudo mkfs.ext4 -E nodiscard /dev/nvme1n1
sudo mount -o discard /dev/nvme1n1 /mnt/postgresql
# sudo mount -o discard /dev/sdc1 /mnt/postgresql

# Create the new cluster's data folder, then create the cluster
sudo mkdir -p /mnt/postgresql/data
sudo chmod 0750 /mnt/postgresql/data
sudo pg_createcluster --datadir=/mnt/postgresql/data --port=5432 --start 14 main

# Create the user we need
sudo -u postgres psql -c "create user project1user with superuser encrypted password 'project1pass';"

git clone --depth 1 https://github.com/cmu-db/benchbase.git
cd benchbase
./mvnw clean package -P postgres
cd target
tar xvzf benchbase-postgres.tgz
cd benchbase-postgres

cp ../../../main.py ./
