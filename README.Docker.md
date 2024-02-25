### Building and running your application

Build:
`docker buildx build --platform=linux/amd64 -t anki-gen-fin .`


Start the application by running:

`docker run  --rm -v $(pwd)/input:/app/input -v $(pwd)/output:/app/output -v $(pwd)/media:/app/media anki-gen-fin python3 process.py process --input LB-S1-L16.csv`



