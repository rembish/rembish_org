# README
I'm not sure if somebody will want to create a fork or participate in development of
this project, but at least we save a few comments for myself: how to bootstrap
this application. Nothing to tough, but still good to know. 

## Step by step project setup
1. Check if you have `python` 3.8+ (check deadsnakes if not: https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa)
```bash
python -V
```
2. Install `nvm`: https://github.com/nvm-sh/nvm#install--update-script:
```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.37.1/install.sh | bash
```
3. Install latest `node`
```bash
nvm install node
```
4. Install `node` modules
```bash
npm install
```
5. Install `poetry`: https://python-poetry.org/docs/#installation
```bash
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
```
6. Setup `poetry` to use local virtual environment
```bash
poetry config virtualenvs.in-project true
```
7. Create virtualenv and install project dependencies
```bash
poetry install
```
8. Create development SSL certificates (install `make` if don't have it, like `sudo apt install make`)
```bash
make devssl
```
9. Create a `secrets` file (see further instructions in the example comments):
```bash
cp secrets.example secrets
vi secrets
```
10. Initialize database (make sure, that you have working `docker`: https://docs.docker.com/engine/install/ubuntu/)
```bash
poetry run docker-compose up database
```
11. Apply database migrations (or restore a dump if you have one)
```bash
poetry run flask db upgrade
# or if dump
cat dump.sql | poetry run docker-compose exec -T database mysql -p<root-password> rembish_org
```
12. Check if you have the right `localhost` alias:
```bash
sudo vi /etc/hosts
# Add dev.rembish.org to 127.0.0.1
```

## Starting dev environment
1. Using `flask` WSGI server:
```bash
env $(cat secrets | xargs) poetry run flask run
# Server will be spawned on https://dev.rembish.org:5000
```
2. Using `docker`:
```bash
poetry run docker-compose up
# Server will be started on standard HTTPS port: https://dev.rembish.org
```

## Contributing and deploying
1. Don't forget to add your changes to `CHANGELOG.md`
2. To deploy new version:
   - increase version: `poetry run flask version -i [patch|minor|major]`
   - commit changes: `git commit -m "Release X.Y.Z`
   - tag 'em: `git tag vX.Y.Z`
   - and push: `git push --tags origin main`
3. Github Actions will deploy the application automatically
4. Check it on https://rembish.org