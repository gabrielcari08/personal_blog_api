from fastapi import FastAPI

app = FastAPI(title='Personal Blog API', description='API for the Personal Blog')

@app.get('/')
def root():
    return {'message': 'Personal Blog is running'}